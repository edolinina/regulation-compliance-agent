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
    def __init__(self, settings: Settings) -> None:
        llm = LLMClient(settings)

        self._extractor = RuleExtractor(llm)
        self._evaluator = ComplianceEvaluator(llm)

    async def extract_rules(self) -> None:
        rules = await self._extractor.run()
        print(f"Extracted {len(rules)} rules.")

    async def evaluate(self, user_text: str) -> None:
        result = await self._evaluator.evaluate(user_text)
        report = self._evaluator.render_report(result)

        if report:
            print(report)

    async def run(self, user_text: str) -> None:
        await self.extract_rules()
        await self.evaluate(user_text)


def load_settings() -> Settings:
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
    try:
        asyncio.run(async_main())
    except (RuntimeError, FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()
