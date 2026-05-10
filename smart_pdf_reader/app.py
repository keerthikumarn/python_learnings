from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

import session_manager as session
from pdf_service import extract_text_from_pdf
from llm_service import build_llm, stream_llm

load_dotenv()


# ── App bootstrap ────────────────────────────────────────────────────────────

def configure_page() -> None:
    st.set_page_config(
        page_title="SmartDocReader — PDF Tutor",
        page_icon="📖",
        layout="centered",
        initial_sidebar_state="expanded",
    )


def inject_custom_css() -> None:
    """
    Reads styles.css from the project root and injects it into the page.

    Keeping CSS in a dedicated file means:
    - IDE syntax highlighting and linting works properly
    - No Python string escaping headaches
    - Designers can edit styles.css without touching Python
    - Analogous to a static resource in Spring Boot's /resources/static/
    """
    css_path = Path(__file__).parent / "styles.css"
    with open(css_path, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)




def render_header() -> None:
    st.markdown("""
    <div class="app-header">
        <div class="wordmark">Smart<span>DocReader</span></div>
        <div class="tagline">PDF Intelligence Tutor</div>
    </div>
    """, unsafe_allow_html=True)


# ── Upload & processing section ──────────────────────────────────────────────

def render_upload_section() -> None:
    st.markdown(
        '<p style="font-family:var(--font-mono);font-size:0.72rem;'
        'letter-spacing:0.12em;text-transform:uppercase;'
        'color:var(--text-muted);margin-bottom:0.5rem;">Upload PDF</p>',
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        label="pdf",
        type=["pdf"],
        help="Upload a single PDF document to analyze",
        label_visibility="hidden",
    )

    if uploaded_file is not None and not session.has_document():
        _process_uploaded_pdf(uploaded_file)


def _process_uploaded_pdf(uploaded_file) -> None:
    with st.spinner("Extracting document… analysing structure…"):
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
    st.success("✅ Document loaded — ask anything below.")


# ── Chat section ─────────────────────────────────────────────────────────────

def render_chat_section() -> None:
    _render_sidebar_controls()
    _render_chat_history()
    _render_chat_input()


def _render_sidebar_controls() -> None:
    from configuration import DEFAULT_MODEL
    with st.sidebar:
        st.markdown('<div class="sidebar-section-title">Model</div>', unsafe_allow_html=True)
        model_display = DEFAULT_MODEL.replace("ollama/", "")
        st.markdown(f"""
        <div class="model-badge">
            <div class="label">Active</div>
            <div class="value"><span class="status-dot"></span>{model_display}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section-title">Session</div>', unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("🗑️  Clear Chat", use_container_width=True):
            _handle_clear_chat()


def _handle_clear_chat() -> None:
    llm_result = build_llm(session.get_document_text())
    if llm_result.is_success:
        session.clear_chat(llm_result.llm)
        st.rerun()
    else:
        st.error(f"❌ {llm_result.error}")


def _render_chat_history() -> None:
    for message in session.get_messages():
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def _render_chat_input() -> None:
    if prompt := st.chat_input("Ask a question about the document…"):
        _handle_user_prompt(prompt)


def _handle_user_prompt(prompt: str) -> None:
    session.append_message("user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            for token in stream_llm(session.get_llm(), prompt):
                full_response += token
                placeholder.markdown(full_response + "▌")   # typing cursor
            placeholder.markdown(full_response)              # final render, no cursor
        except Exception as e:
            full_response = f"❌ Error generating response: {str(e)}"
            placeholder.markdown(full_response)

        session.append_message("assistant", full_response)


# ── LLM recovery section ─────────────────────────────────────────────────────

def render_llm_recovery_section() -> None:
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
    st.markdown("""
    <div class="welcome-card">
        <h3>Get started</h3>
        <ol>
            <li>Upload any PDF document above</li>
            <li>Wait a moment while the model reads it</li>
            <li>Ask questions in plain language</li>
            <li>Use <em>Clear Chat</em> in the sidebar to reset</li>
        </ol>
        <div class="features">
            <span class="badge">📄 any PDF</span>
            <span class="badge">💬 conversational</span>
            <span class="badge">🏠 100% local</span>
            <span class="badge">🔒 no data leaves your machine</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Main entrypoint ──────────────────────────────────────────────────────────

def main() -> None:
    configure_page()
    inject_custom_css()
    render_header()
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