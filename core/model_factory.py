"""
Agnostic model factory — swap providers via MODEL_PROVIDER env var.
Supported: groq (default) | mistral | openai | anthropic | bedrock | gemini | ollama
"""
import os
from config.settings import MODEL_PROVIDER


def get_model():
    provider = MODEL_PROVIDER.lower()

    if provider == "groq":
        from strands.models.openai import OpenAIModel
        return OpenAIModel(
            client_args={
                "api_key": os.getenv("GROQ_API_KEY"),
                "base_url": "https://api.groq.com/openai/v1",
            },
            model_id=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            params={"temperature": 0.7, "max_tokens": 2048},
        )

    if provider == "mistral":
        from litellm import completion
        # LiteLLM wraps Mistral as an OpenAI-compatible model
        class LiteLLMModel:
            """Thin wrapper so Strands can call LiteLLM models."""
            def __init__(self, model_id: str):
                self.model_id = model_id

            def __call__(self, messages, **kwargs):
                resp = completion(
                    model=f"mistral/{self.model_id}",
                    messages=messages,
                    api_key=os.getenv("MISTRAL_API_KEY"),
                    **kwargs,
                )
                return resp.choices[0].message.content

        return LiteLLMModel("mistral-7b-instruct")

    elif provider == "ollama":
        # Local Mistral-7B via Ollama (zero cost)
        from strands.models.openai import OpenAIModel
        return OpenAIModel(
            client_args={
                "api_key": "ollama",
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            },
            model_id="mistral",
        )

    elif provider == "openai":
        from strands.models.openai import OpenAIModel
        return OpenAIModel(
            client_args={"api_key": os.getenv("OPENAI_API_KEY")},
            model_id="gpt-4o-mini",
        )

    elif provider == "anthropic":
        from strands.models.anthropic import AnthropicModel
        return AnthropicModel(
            client_args={"api_key": os.getenv("ANTHROPIC_API_KEY")},
            model_id="claude-3-5-sonnet-20241022",
            max_tokens=2048,
        )

    elif provider == "gemini":
        from strands.models.gemini import GeminiModel
        return GeminiModel(
            client_args={"api_key": os.getenv("GOOGLE_API_KEY")},
            model_id="gemini-2.5-flash",
        )

    elif provider == "bedrock":
        from strands.models import BedrockModel
        return BedrockModel(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

    else:
        raise ValueError(f"Unknown MODEL_PROVIDER: {provider}")
