"""Rule evaluation workflow and human-readable report rendering."""

import json
from pathlib import Path

from .constants import RULES_PATH
from .llm import LLMClient
from .models import ComplianceRule, EvaluationResult, Failure

RED = "\033[91m"
GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"


class ComplianceEvaluator:
    """Load extracted rules and evaluate marketing text against them."""

    def __init__(
        self,
        llm: LLMClient,
        rules_path: Path = RULES_PATH,
    ) -> None:
        """Store evaluator dependencies and the rules source location."""
        self._llm = llm
        self._rules_path = rules_path

    async def evaluate(
        self,
        user_text: str,
    ) -> EvaluationResult:
        """Evaluate user text and reject any hallucinated rule identifiers."""
        rules = self._load_rules()

        result = await self._llm.evaluate(
            user_text=user_text,
            rules=rules,
        )

        valid_rule_ids = {rule.id for rule in rules}

        unknown_ids = {
            failure.rule_id
            for failure in result.failures
            if failure.rule_id not in valid_rule_ids
        }

        if unknown_ids:
            # Structured outputs should only refer to known extracted rules.
            raise ValueError(
                f"Unknown rule IDs returned: {sorted(unknown_ids)}"
            )

        return result

    def _load_rules(self) -> list[ComplianceRule]:
        """Read and validate extracted rules from disk."""
        raw = json.loads(
            self._rules_path.read_text(
                encoding="utf-8",
            )
        )

        return [
            ComplianceRule.model_validate(item)
            for item in raw
        ]

    @staticmethod
    def render_report(result: EvaluationResult) -> str:
        """Format failures as a terminal-friendly compliance report."""
        unique: dict[str, Failure] = {}

        for failure in result.failures:
            # Collapse duplicate findings that quote the same user text.
            key = failure.evidence.strip().lower()
            unique.setdefault(key, failure)

        failures = list(unique.values())

        if not failures:
            return (
                f"{GREEN}{BOLD}🟢 COMPLIANT{RESET}\n"
                "No compliance issues found."
            )

        lines = [
            f"{RED}{BOLD}🔴 NON-COMPLIANT{RESET}",
            f"Found {len(failures)} compliance issue(s).",
            "",
        ]

        for index, failure in enumerate(failures, start=1):
            lines.extend(
                [
                    f"{index}. {BOLD}{failure.title}{RESET}",
                    f"   Rule: {failure.rule_id}",
                    f'   Matched text: "{failure.evidence}"',
                    f"   Why: {failure.explanation}",
                    f"   Fix: {failure.recommendation}",
                    "",
                ]
            )

        return "\n".join(lines).rstrip()
