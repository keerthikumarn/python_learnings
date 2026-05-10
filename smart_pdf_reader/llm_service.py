import litellm
from typing import Generator
from lisette import Chat
from configuration import (
    SYSTEM_PROMPT_TEMPLATE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    OLLAMA_BASE_URL,
)


class LlmInitResult:
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
            # stream=True removed — we handle streaming via litellm directly
        )
        return LlmInitResult(llm=llm)
    except Exception as e:
        return LlmInitResult(error=f"Failed to initialize AI tutor: {str(e)}")


def stream_llm(llm: Chat, prompt: str) -> Generator[str, None, None]:
    """
    Streams tokens by calling LiteLLM directly.
    Lisette manages conversation history — we read hist from it and
    write the completed response back manually after streaming.
    """
    print("⏳ stream_llm called — using litellm directly")

    # 1. Manually append the user message to lisette's history
    llm.hist.append({"role": "user", "content": prompt})

    # 2. Build the full message list lisette would have sent
    messages = [{"role": "system", "content": llm.sp}] + llm.hist

    # 3. Call LiteLLM directly with stream=True
    response = litellm.completion(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=DEFAULT_TEMPERATURE,
        api_base=OLLAMA_BASE_URL,
        stream=True,
    )

    # 4. Yield each token as it arrives
    full_response = ""
    for chunk in response:
        token = chunk.choices[0].delta.content or ""
        if token:
            print(f"✅ token: {repr(token)}")
            full_response += token
            yield token

    # 5. Write the completed response back into lisette's history
    #    so future turns have full conversation context
    llm.hist.append({"role": "assistant", "content": full_response})
    print(f"✅ stream complete — {len(full_response)} chars")


def _build_system_prompt(document_text: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(paper_txt=document_text)