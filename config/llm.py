from langchain_ollama import ChatOllama


def get_llm():
    """
    Returns a shared Ollama LLM instance.
    Every agent in the system will use this.
    """

    return ChatOllama(
        model="qwen2.5-coder:7b",
        temperature=0
    )