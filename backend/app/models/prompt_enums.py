"""Prompt challenge enums. Native string columns — no PostgreSQL enum types."""

from enum import StrEnum


class PromptTaskType(StrEnum):
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    REWRITING = "rewriting"
    STRUCTURED_OUTPUT = "structured_output"
    ROUTING = "routing"
    QUESTION_ANSWERING = "question_answering"
    TOOL_SELECTION = "tool_selection"
    SAFETY = "safety"
    PROMPT_DEBUGGING = "prompt_debugging"
    RAG_INSTRUCTION = "rag_instruction"
    AGENT_INSTRUCTION = "agent_instruction"
    FORMATTING = "formatting"
    CONSTRAINT_FOLLOWING = "constraint_following"


class PromptProgressStatus(StrEnum):
    ATTEMPTED = "attempted"
    MASTERED = "mastered"
