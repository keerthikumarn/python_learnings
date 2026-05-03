"""
session_manager.py — Centralized Streamlit session state management.

Responsibility: Own all reads and writes to st.session_state so that the
UI layer never accesses raw session keys directly.

Analogous to a stateful @SessionScoped bean or a Redux store in Spring/React.
Every key is declared in ONE place — no more scattered string literals.
"""

import streamlit as st
from lisette import Chat

# ── Session key constants ────────────────────────────────────────────────────
# Define all keys here to avoid silent typo-bugs from bare string access.

_KEY_MESSAGES = "messages"
_KEY_DOCUMENT_TEXT = "document_text"
_KEY_LLM = "llm"


# ── Initialisation ───────────────────────────────────────────────────────────

def init_session_state() -> None:
    """
    Seeds session state with default values on first run.
    Safe to call on every Streamlit rerun — only sets keys that are absent.
    """
    defaults = {
        _KEY_MESSAGES: [],
        _KEY_DOCUMENT_TEXT: None,
        _KEY_LLM: None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ── Document text accessors ──────────────────────────────────────────────────

def get_document_text() -> str | None:
    return st.session_state[_KEY_DOCUMENT_TEXT]


def set_document_text(text: str) -> None:
    st.session_state[_KEY_DOCUMENT_TEXT] = text


def has_document() -> bool:
    return st.session_state[_KEY_DOCUMENT_TEXT] is not None


# ── LLM accessors ────────────────────────────────────────────────────────────

def get_llm() -> Chat | None:
    return st.session_state[_KEY_LLM]


def set_llm(llm: Chat) -> None:
    st.session_state[_KEY_LLM] = llm


def has_llm() -> bool:
    return st.session_state[_KEY_LLM] is not None


# ── Chat message accessors ───────────────────────────────────────────────────

def get_messages() -> list[dict]:
    return st.session_state[_KEY_MESSAGES]


def append_message(role: str, content: str) -> None:
    """Appends a single chat turn. role must be 'user' or 'assistant'."""
    st.session_state[_KEY_MESSAGES].append({"role": role, "content": content})


def clear_chat(new_llm: Chat) -> None:
    """
    Resets chat history and replaces the LLM instance.
    Used by the 'Clear Chat' button to start a fresh conversation without
    re-uploading the document.
    """
    st.session_state[_KEY_MESSAGES] = []
    st.session_state[_KEY_LLM] = new_llm


def reset_all() -> None:
    """
    Full reset — clears document, LLM, and messages.
    Called on PDF processing errors to ensure a clean slate.
    """
    st.session_state[_KEY_DOCUMENT_TEXT] = None
    st.session_state[_KEY_LLM] = None
    st.session_state[_KEY_MESSAGES] = []