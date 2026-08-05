from typing import Generator, List
from inference.provider import LLMProvider


class InferenceStreamer:
    """
    Handles generator-based completion streaming across CLI, WebSocket, and Planner streaming.
    """

    @staticmethod
    def stream_completion(provider: LLMProvider, prompt: str, model: str = "") -> Generator[str, None, None]:
        for chunk in provider.stream(prompt=prompt, model=model):
            yield chunk

    @staticmethod
    def stream_to_list(provider: LLMProvider, prompt: str, model: str = "") -> List[str]:
        return list(InferenceStreamer.stream_completion(provider, prompt, model))
