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
    def __init__(self, settings: Settings) -> None:
        self._llm = ChatOpenAI(
            model=settings.model,
            api_key=settings.api_key,
            temperature=0,
        )

        self._extraction_chain = self._build_extraction_chain()
        self._evaluation_chain = self._build_evaluation_chain()

    def _build_extraction_chain(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EXTRACTION_SYSTEM_PROMPT),
                ("human", EXTRACTION_USER_PROMPT),
            ]
        )

        structured_llm = self._llm.with_structured_output(
            ExtractedRules,
            method="json_schema",
        )

        return prompt | structured_llm

    def _build_evaluation_chain(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EVALUATION_SYSTEM_PROMPT),
                ("human", EVALUATION_USER_PROMPT),
            ]
        )

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
        return await self._evaluation_chain.ainvoke(
            {
                "user_text": user_text,
                "rules": [rule.model_dump() for rule in rules],
            }
        )