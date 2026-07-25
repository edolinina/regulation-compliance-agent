"""Pydantic models shared across extraction and evaluation workflows."""

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime configuration for LLM-backed operations."""

    api_key: str
    model: str = "gpt-4.1-mini"


class ComplianceRule(BaseModel):
    """A single atomic compliance rule extracted from a regulation document."""

    id: str = Field(min_length=1)
    requirement: str = Field(min_length=1)
    source_document: str = Field(min_length=1)
    source_page: int = Field(ge=1)
    source_quote: str = Field(min_length=1)
    source_url: str | None = Field(default=None)


class ExtractedRules(BaseModel):
    """Structured LLM response for rule extraction."""

    rules: list[ComplianceRule] = Field(default_factory=list)


class Failure(BaseModel):
    """A user-facing compliance failure found in marketing text."""

    rule_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)


class EvaluationResult(BaseModel):
    """Structured LLM response for a compliance evaluation run."""

    failures: list[Failure] = Field(default_factory=list)