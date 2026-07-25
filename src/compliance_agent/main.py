"""Command-line entry point for rule extraction and compliance evaluation."""

from __future__ import annotations

import argparse
import asyncio
import os

from dotenv import load_dotenv

from .evaluation import ComplianceEvaluator
from .extraction import RuleExtractor
from .llm import LLMClient
from .models import Settings


class CompliancePipeline:
    """Coordinate rule extraction and evaluation with shared LLM settings."""

    def __init__(self, settings: Settings) -> None:
        """Initialize both pipeline stages with the same LLM client."""
        llm = LLMClient(settings)

        self._extractor = RuleExtractor(llm)
        self._evaluator = ComplianceEvaluator(llm)

    async def extract_rules(self) -> None:
        """Extract and persist rules from the configured regulation PDFs."""
        rules = await self._extractor.run()
        print(f"Extracted {len(rules)} rules.")

    async def evaluate(self, user_text: str) -> None:
        """Evaluate user text and print a formatted compliance report."""
        result = await self._evaluator.evaluate(user_text)
        report = self._evaluator.render_report(result)

        if report:
            print(report)

    async def run(self, user_text: str) -> None:
        """Run extraction first, then evaluate the provided user text."""
        await self.extract_rules()
        await self.evaluate(user_text)


def load_settings() -> Settings:
    """Load runtime settings from the environment and validate required keys."""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file or environment."
        )

    return Settings(
        api_key=api_key,
        model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI options for extraction and evaluation commands."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract rules from PDFs and save rules.json",
    )

    parser.add_argument(
        "--evaluate",
        type=str,
        help="Marketing text to evaluate",
    )

    return parser.parse_args()


async def async_main() -> None:
    """Dispatch CLI actions based on the provided arguments."""
    args = parse_args()
    settings = load_settings()
    pipeline = CompliancePipeline(settings)

    if not args.extract and not args.evaluate:
        raise SystemExit(
            "Use --extract, --evaluate TEXT, or both."
        )

    if args.extract:
        await pipeline.extract_rules()

    if args.evaluate:
        await pipeline.evaluate(args.evaluate)


def main() -> None:
    """Run the CLI and convert common runtime errors into exit messages."""
    try:
        asyncio.run(async_main())
    except (RuntimeError, FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()
