"""CLI entry point for evaluating the agent against the golden dataset."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from compliance_agent.evaluation import ComplianceEvaluator
from compliance_agent.llm import LLMClient
from compliance_agent.main import load_settings


async def evaluate_dataset(dataset_path: Path) -> None:
    """Run the evaluator against each golden dataset case and print accuracy."""
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))

    settings = load_settings()
    evaluator = ComplianceEvaluator(LLMClient(settings))

    correct = 0

    for case in cases:
        result = await evaluator.evaluate(case["text"])
        predicted_compliant = not result.failures
        passed = predicted_compliant == case["expected_compliant"]
        correct += int(passed)

        print(
            f'{case["id"]}: '
            f'{"PASS" if passed else "FAIL"} '
            f'(expected={"compliant" if case["expected_compliant"] else "non-compliant"}, '
            f'predicted={"compliant" if predicted_compliant else "non-compliant"})'
        )

        if not passed:
            # Only print detailed failures when the predicted label is wrong.
            for failure in result.failures:
                print(f"  - {failure.rule_id}: {failure.explanation}")

    total = len(cases)
    print(f"\nAccuracy: {correct}/{total} ({correct / total:.0%})")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for dataset evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate the compliance agent against the golden dataset."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/golden_dataset.json"),
    )
    return parser.parse_args()


def main() -> None:
    """Execute the async dataset evaluation CLI."""
    args = parse_args()
    asyncio.run(evaluate_dataset(args.dataset))


if __name__ == "__main__":
    main()

