"""Provider management for multiple LLM providers."""

import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

import httpx


class ProviderType(str, Enum):
    """Supported LLM providers."""

    GEMINI = "gemini"
    GPT4 = "gpt4"
    CLAUDE = "claude"


class LLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    @abstractmethod
    async def complete(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Complete a prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass

    @abstractmethod
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Get cost per 1k tokens (input, output)."""
        pass

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for a request."""
        costs = self.get_cost_per_1k_tokens()
        return (prompt_tokens / 1000 * costs["input"]) + (
            completion_tokens / 1000 * costs["output"]
        )


class GeminiProvider(LLMProvider):
    """Google Gemini provider (via Vertex AI)."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        super().__init__(api_key)
        self.model = "gemini-2.5-flash"
        self.project_id = os.getenv("GCP_PROJECT_ID", "demo-project")
        self.location = os.getenv("GCP_LOCATION", "us-central1")

    async def complete(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Complete using Gemini."""

        if not self.api_key:
            return self._mock_response(prompt, max_tokens)

        url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            if "candidates" not in data or not data["candidates"]:
                raise Exception("No candidates in response")

            candidate = data["candidates"][0]
            finish_reason = candidate.get("finishReason", "")

            # Handle MAX_TOKENS case
            if finish_reason == "MAX_TOKENS":
                payload["generationConfig"]["maxOutputTokens"] = max_tokens * 2
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                candidate = data["candidates"][0]

            if "content" not in candidate:
                raise Exception(f"No content in candidate: {candidate}")

            content = candidate["content"]
            if "parts" not in content or not content["parts"]:
                raise Exception(f"No parts in content: {content}")

            parts = content["parts"]
            if not parts or "text" not in parts[0]:
                raise Exception(f"No text in parts: {parts}")

            text = parts[0]["text"]

            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", len(prompt.split()))
            completion_tokens = usage.get("candidatesTokenCount", len(text.split()))

            return {
                "text": text,
                "model": self.model,
                "tokens_used": {
                    "prompt": prompt_tokens,
                    "completion": completion_tokens,
                    "total": prompt_tokens + completion_tokens,
                },
                "cost": self.estimate_cost(prompt_tokens, completion_tokens),
            }

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}") from e

    def is_available(self) -> bool:
        return True

    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.000075, "output": 0.0003}

    def _mock_response(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        text = f"[GEMINI DEMO] Mock response to: '{prompt[:50]}...'"
        return {
            "text": text,
            "model": f"{self.model}-demo",
            "tokens_used": {
                "prompt": len(prompt.split()),
                "completion": len(text.split()),
                "total": len(prompt.split()) + len(text.split()),
            },
            "cost": 0.0001,
        }


class GPT4Provider(LLMProvider):
    """OpenAI GPT-4 provider."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        super().__init__(api_key)
        self.model = "gpt-4o-mini"

    async def complete(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> Dict[str, Any]:

        if not self.api_key:
            return self._mock_response(prompt, max_tokens)

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            text = data["choices"][0]["message"]["content"]
            usage = data["usage"]

            return {
                "text": text,
                "model": self.model,
                "tokens_used": {
                    "prompt": usage["prompt_tokens"],
                    "completion": usage["completion_tokens"],
                    "total": usage["total_tokens"],
                },
                "cost": self.estimate_cost(
                    usage["prompt_tokens"], usage["completion_tokens"]
                ),
            }

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}") from e

    def is_available(self) -> bool:
        return True

    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.00015, "output": 0.0006}

    def _mock_response(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        text = f"[GPT-4 DEMO] Mock response to: '{prompt[:50]}...'"
        return {
            "text": text,
            "model": f"{self.model}-demo",
            "tokens_used": {
                "prompt": len(prompt.split()),
                "completion": len(text.split()),
                "total": len(prompt.split()) + len(text.split()),
            },
            "cost": 0.0002,
        }


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key)
        self.model = "claude-sonnet-4-5-20250929"

    async def complete(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> Dict[str, Any]:

        if not self.api_key:
            return self._mock_response(prompt, max_tokens)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            text = data["content"][0]["text"]
            usage = data["usage"]

            return {
                "text": text,
                "model": self.model,
                "tokens_used": {
                    "prompt": usage["input_tokens"],
                    "completion": usage["output_tokens"],
                    "total": usage["input_tokens"] + usage["output_tokens"],
                },
                "cost": self.estimate_cost(
                    usage["input_tokens"], usage["output_tokens"]
                ),
            }

        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}") from e

    def is_available(self) -> bool:
        return True

    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.003, "output": 0.015}

    def _mock_response(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        text = f"[CLAUDE DEMO] Mock response to: '{prompt[:50]}...'"
        return {
            "text": text,
            "model": f"{self.model}-demo",
            "tokens_used": {
                "prompt": len(prompt.split()),
                "completion": len(text.split()),
                "total": len(prompt.split()) + len(text.split()),
            },
            "cost": 0.0005,
        }


class ProviderManager:
    """Manages multiple LLM providers."""

    def __init__(self):
        self.providers: Dict[ProviderType, LLMProvider] = {
            ProviderType.GEMINI: GeminiProvider(),
            ProviderType.GPT4: GPT4Provider(),
            ProviderType.CLAUDE: ClaudeProvider(),
        }

    def get_provider(self, provider_type: ProviderType) -> LLMProvider:
        return self.providers[provider_type]

    def get_available_providers(self) -> list[ProviderType]:
        return [
            ptype
            for ptype, provider in self.providers.items()
            if provider.is_available()
        ]
