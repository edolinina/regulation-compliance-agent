"""LLM wrapper for structured rule extraction and evaluation prompts."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .constants import (
    EVALUATION_SYSTEM_PROMPT,
    EVALUATION_USER_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT,
)
from .models import Settings, EvaluationResult, ExtractedRules, ComplianceRule


class LLMClient:
    """Expose structured LLM calls for extraction and evaluation workflows."""

    def __init__(self, settings: Settings) -> None:
        """Create the shared chat model and both structured prompt chains."""
        self._llm = ChatOpenAI(
            model=settings.model,
            api_key=settings.api_key,
            temperature=0,
        )

        self._extraction_chain = self._build_extraction_chain()
        self._evaluation_chain = self._build_evaluation_chain()

    def _build_extraction_chain(self):
        """Build the structured extraction chain used for regulation PDFs."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EXTRACTION_SYSTEM_PROMPT),
                ("human", EXTRACTION_USER_PROMPT),
            ]
        )

        # Force schema-shaped responses so downstream validation stays simple.
        structured_llm = self._llm.with_structured_output(
            ExtractedRules,
            method="json_schema",
        )

        return prompt | structured_llm

    def _build_evaluation_chain(self):
        """Build the structured evaluation chain used for marketing text."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EVALUATION_SYSTEM_PROMPT),
                ("human", EVALUATION_USER_PROMPT),
            ]
        )

        # The evaluator expects only failure objects, never free-form prose.
        structured_llm = self._llm.with_structured_output(
            EvaluationResult,
            method="json_schema",
        )

        return prompt | structured_llm

    async def extract_rules(
        self,
        document_id: str,
        document_text: str,
    ) -> ExtractedRules:
        """Extract compliance rules from one regulation document."""
        result = await self._extraction_chain.ainvoke(
            {
                "document_id": document_id,
                "document_text": document_text,
            }
        )

        return ExtractedRules.model_validate(result)

    async def evaluate(
        self,
        user_text: str,
        rules: list[ComplianceRule],
    ) -> EvaluationResult:
        """Evaluate user text against the supplied extracted rules."""
        return await self._evaluation_chain.ainvoke(
            {
                "user_text": user_text,
                "rules": [rule.model_dump() for rule in rules],
            }
        )