"""
llm_service.py — Service layer for LLM initialization and interaction.

Responsibility: Build and manage the Chat (Lisette) instance.
Analogous to a @Service bean that wraps an external API client in Spring Boot.
"""

from lisette import Chat
from configuration import (
    SYSTEM_PROMPT_TEMPLATE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
)


class LlmInitResult:
    """
    Value object for the outcome of an LLM initialization attempt.
    Keeps callers free of try/except and provides a uniform interface.
    """

    def __init__(self, llm: Chat = None, error: str = None):
        self.llm = llm
        self.error = error

    @property
    def is_success(self) -> bool:
        return self.llm is not None and self.error is None


def build_llm(document_text: str) -> LlmInitResult:
    try:
        system_prompt = _build_system_prompt(document_text)
        llm = Chat(
            model=DEFAULT_MODEL,
            sp=system_prompt,
            temp=DEFAULT_TEMPERATURE,
        )
        return LlmInitResult(llm=llm)
    except Exception as e:
        return LlmInitResult(error=f"Failed to initialize AI tutor: {str(e)}")


def query_llm(llm: Chat, prompt: str) -> tuple[str | None, str | None]:
    """
    Sends a user prompt to the LLM and returns the assistant's reply.

    Args:
        llm:    Initialized Chat instance.
        prompt: User's question string.

    Returns:
        (response_text, error_message) — exactly one of which will be None.
    """
    try:
        response = llm(prompt)
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"Error generating response: {str(e)}"


# ── Private helpers ──────────────────────────────────────────────────────────

def _build_system_prompt(document_text: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(paper_txt=document_text)