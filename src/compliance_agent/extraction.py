"""PDF download, text extraction, and rule extraction orchestration."""

import asyncio
import json
from io import BytesIO
from pathlib import Path

import httpx
from pypdf import PdfReader

from tqdm import tqdm

from .constants import (
    DOWNLOAD_TIMEOUT_SECONDS,
    MAX_CONCURRENT_DOCUMENTS,
    REGULATION_PDFS,
    RULES_PATH,
)
from .llm import LLMClient
from .models import ComplianceRule


class RuleExtractor:
    """Extract compliance rules from a configured set of regulation PDFs."""

    def __init__(
        self,
        llm: LLMClient,
        pdf_urls: dict[str, str] = REGULATION_PDFS,
        rules_path: Path = RULES_PATH,
        max_concurrency: int = MAX_CONCURRENT_DOCUMENTS,
    ) -> None:
        """Configure extraction inputs and a concurrency limiter."""
        self._llm = llm
        self._pdf_urls = pdf_urls
        self._rules_path = rules_path
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def run(self) -> list[ComplianceRule]:
        """Process all PDFs, persist extracted rules, and return them."""
        async with httpx.AsyncClient(
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            tasks = [
                asyncio.create_task(
                    self._process_pdf(
                        client=client,
                        document_id=document_id,
                        url=url,
                    )
                )
                for document_id, url in self._pdf_urls.items()
            ]

            rules: list[ComplianceRule] = []

            with tqdm(
                total=len(tasks),
                desc="Extracting rules",
                unit="PDF",
            ) as progress:
                for completed in asyncio.as_completed(tasks):
                    # Surface each document result as soon as it finishes.
                    document_id, document_rules, error = await completed

                    if error is not None:
                        tqdm.write(f"{document_id}: failed: {error}")
                    else:
                        rules.extend(document_rules)
                        tqdm.write(
                            f"{document_id}: extracted "
                            f"{len(document_rules)} rules"
                        )

                    progress.update(1)

        self._save_rules(rules)

        return rules

    async def _process_pdf(
        self,
        client: httpx.AsyncClient,
        document_id: str,
        url: str,
    ) -> tuple[str, list[ComplianceRule], Exception | None]:
        """Download one PDF, extract its text, and turn it into rules."""
        try:
            async with self._semaphore:
                pdf_bytes = await self._download_pdf(client, url)

                document_text = await asyncio.to_thread(
                    self._extract_text,
                    pdf_bytes,
                )

                result = await self._llm.extract_rules(
                    document_id=document_id,
                    document_text=document_text,
                )

                # Persist the source URL on each returned rule for traceability.
                for rule in result.rules:
                    rule.source_url = url

                return document_id, result.rules, None

        except Exception as error:
            return document_id, [], error

    @staticmethod
    async def _download_pdf(
        client: httpx.AsyncClient,
        url: str,
    ) -> bytes:
        """Fetch a remote PDF and validate the response looks like a PDF."""
        response = await client.get(url)
        response.raise_for_status()

        content = response.content

        if not content.lstrip().startswith(b"%PDF"):
            raise ValueError(
                f"URL did not return a PDF: {url}"
            )

        return content

    @staticmethod
    def _extract_text(pdf_bytes: bytes) -> str:
        """Extract page-delimited text from raw PDF bytes."""
        reader = PdfReader(BytesIO(pdf_bytes))

        pages = [
            (
                # Keep page markers so extracted rules can cite their origin.
                f"===== PAGE {page_number} =====\n"
                f"{(page.extract_text() or '').strip()}"
            )
            for page_number, page in enumerate(
                reader.pages,
                start=1,
            )
        ]

        document_text = "\n\n".join(pages).strip()

        if not document_text:
            raise ValueError(
                "No text could be extracted from the PDF."
            )

        return document_text

    def _save_rules(
        self,
        rules: list[ComplianceRule],
    ) -> None:
        """Write validated rules to the configured JSON file."""
        self._rules_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._rules_path.write_text(
            json.dumps(
                [rule.model_dump() for rule in rules],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
