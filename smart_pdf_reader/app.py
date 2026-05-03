import streamlit as st
from dotenv import load_dotenv

import session_manager as session
from pdf_service import extract_text_from_pdf
from llm_service import build_llm, query_llm

load_dotenv()


# ── App bootstrap ────────────────────────────────────────────────────────────

def configure_page() -> None:
    st.set_page_config(
        page_title="PDF Document Tutor",
        page_icon="📚",
        layout="centered",
    )


# ── Upload & processing section ──────────────────────────────────────────────

def render_upload_section() -> None:
    """Renders the PDF uploader and triggers processing on a new upload."""
    uploaded_file = st.file_uploader(
        "Upload a PDF document",
        type=["pdf"],
        help="Upload a single PDF document to analyze",
    )

    # Only process if a file was just uploaded and we haven't stored it yet
    if uploaded_file is not None and not session.has_document():
        _process_uploaded_pdf(uploaded_file)


def _process_uploaded_pdf(uploaded_file) -> None:
    """Coordinates PDF extraction → LLM init → session storage."""
    with st.spinner("Processing PDF… This may take a moment."):
        pdf_result = extract_text_from_pdf(uploaded_file)

    if not pdf_result.is_success:
        st.error(f"❌ {pdf_result.error}")
        session.reset_all()
        return

    if pdf_result.warning:
        st.warning(f"⚠️ {pdf_result.warning}")

    llm_result = build_llm(pdf_result.text)

    if not llm_result.is_success:
        st.error(f"❌ {llm_result.error}")
        session.reset_all()
        return

    session.set_document_text(pdf_result.text)
    session.set_llm(llm_result.llm)
    st.success("✅ PDF processed successfully! You can now ask questions about the paper.")


# ── Chat section ─────────────────────────────────────────────────────────────

def render_chat_section() -> None:
    """Renders the full chat interface (sidebar controls, history, input)."""
    _render_sidebar_controls()
    _render_chat_history()
    _render_chat_input()


def _render_sidebar_controls() -> None:
    """Renders sidebar buttons that operate on the current session."""
    with st.sidebar:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            _handle_clear_chat()


def _handle_clear_chat() -> None:
    """Resets chat history and reinitialises the LLM with a fresh context."""
    llm_result = build_llm(session.get_document_text())
    if llm_result.is_success:
        session.clear_chat(llm_result.llm)
        st.rerun()
    else:
        st.error(f"❌ {llm_result.error}")


def _render_chat_history() -> None:
    """Replays all stored messages as Streamlit chat bubbles."""
    for message in session.get_messages():
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def _render_chat_input() -> None:
    """Renders the chat input box and handles submission."""
    if prompt := st.chat_input("Ask a question about the paper…"):
        _handle_user_prompt(prompt)


def _handle_user_prompt(prompt: str) -> None:
    """Persists the user turn, calls the LLM, and persists the assistant turn."""
    session.append_message("user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text, error = query_llm(session.get_llm(), prompt)

        if error:
            message = f"❌ {error}"
        else:
            message = response_text

        placeholder.markdown(message)
        session.append_message("assistant", message)


# ── LLM recovery section ─────────────────────────────────────────────────────

def render_llm_recovery_section() -> None:
    """
    Shown when a document is loaded but the LLM is missing (e.g. after an
    initialisation failure). Lets the user retry without re-uploading.
    """
    st.error("⚠️ The AI tutor failed to initialize. Please try reinitializing.")
    if st.button("🔄 Reinitialize AI Tutor"):
        llm_result = build_llm(session.get_document_text())
        if llm_result.is_success:
            session.set_llm(llm_result.llm)
            st.success("✅ AI tutor reinitialized successfully!")
            st.rerun()
        else:
            st.error(f"❌ {llm_result.error}")


# ── Welcome / onboarding section ─────────────────────────────────────────────

def render_welcome_section() -> None:
    """Displayed before any document is uploaded."""
    st.info("👆 Please upload a PDF research paper to get started!")
    st.markdown("""
    ### How it works:
    1. Upload a PDF document
    2. The AI tutor will read and understand the paper
    3. Ask questions to understand the paper or PDF document better
    4. The tutor will guide you step-by-step through the concepts

    ### Features:
    - 📄 Upload any PDF document
    - 💬 Chat-style interface for questions
    - 🎓 Step-by-step learning approach
    - 🔄 Clear chat to start over
    """)


# ── Main entrypoint ──────────────────────────────────────────────────────────

def main() -> None:
    """
    Top-level orchestrator. Controls which section is rendered based on
    the current session state — mirrors a router / dispatcher pattern.
    """
    configure_page()
    st.title("📚 PDF Document Tutor")
    session.init_session_state()

    render_upload_section()

    if session.has_document():
        if session.has_llm():
            render_chat_section()
        else:
            render_llm_recovery_section()
    else:
        render_welcome_section()


if __name__ == "__main__":
    main()