from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator
import json
import httpx

from app.config import Settings
from app.orchestration_guidance import SUPERVISOR_PROMPT


@dataclass(frozen=True)
class HermesRunResult:
    hermes_thread_id: str | None
    initial_event: dict[str, Any]


class HermesClient:
    """Boundary to Hermes API server.

    Hermes remains the only agent runtime. This app stores synthetic product records
    in its own database, while Hermes profile-scoped state stays inside the
    `digital-recovery` profile and Hermes API server process.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def start_recovery_run(self, *, session_id: str, prompt: str, context: dict[str, Any]) -> HermesRunResult:
        if not self.settings.hermes_enabled:
            return HermesRunResult(
                hermes_thread_id=None,
                initial_event={
                    "mode": "synthetic-dev",
                    "message": "Hermes API call skipped because DERA_HERMES_ENABLED=false.",
                    "session_id": session_id,
                    "prompt": prompt,
                    "context_keys": sorted(context.keys()),
                },
            )

        payload = {
            "model": self.settings.hermes_model,
            "messages": [
                {
                    "role": "system",
                    "content": SUPERVISOR_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "metadata": {
                "dera_session_id": session_id,
                "context": context,
            },
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.settings.hermes_api_key}"}
        async with httpx.AsyncClient(base_url=self.settings.hermes_base_url, timeout=60) as client:
            response = await client.post("/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return HermesRunResult(
            hermes_thread_id=data.get("id"),
            initial_event={"mode": "hermes-api", "response": data},
        )

    async def hermes_chat(self, *, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Ask Hermes about the current incident through the configured API server.

        The product backend owns the safe demo incident state. Hermes is the reasoning
        boundary when enabled; callers may still provide deterministic local fallback
        answers when the API server is unavailable so the cockpit remains usable.
        """
        if not self.settings.hermes_enabled:
            return {"mode": "hermes-compatible-local-adapter", "content": "Hermes API is disabled for this local run."}
        payload = {
            "model": self.settings.hermes_model,
            "messages": [
                {"role": "system", "content": f"{SUPERVISOR_PROMPT}\n\nAnswer style: {context.get('answer_style', 'Be concise by default.')}"},
                {"role": "user", "content": f"Current incident state:\n{context}\n\nOperator question:\n{prompt}"},
            ],
            "metadata": {"dera_chat": True, "context": context},
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.settings.hermes_api_key}"}
        async with httpx.AsyncClient(base_url=self.settings.hermes_base_url, timeout=25) as client:
            response = await client.post("/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        content = ""
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            content = str(data)
        return {"mode": "hermes-api", "content": content, "raw_id": data.get("id")}

    async def hermes_delegate_task(self, *, task: str, context: dict[str, Any]) -> dict[str, Any]:
        return await self.hermes_chat(prompt=f"Delegate specialist task: {task}", context=context)

    async def hermes_chat_stream(self, *, prompt: str, context: dict[str, Any]) -> AsyncIterator[str]:
        """Yield live text chunks from Hermes API server when streaming is available."""
        if not self.settings.hermes_enabled:
            yield "Hermes API is disabled for this local run."
            return
        payload = {
            "model": self.settings.hermes_model,
            "messages": [
                {"role": "system", "content": f"{SUPERVISOR_PROMPT}\n\nAnswer style: {context.get('answer_style', 'Be concise by default.')}"},
                {"role": "user", "content": f"Current incident state:\n{context}\n\nOperator question:\n{prompt}"},
            ],
            "metadata": {"dera_chat": True, "context": context, "streaming": True},
            "stream": True,
        }
        headers = {"Authorization": f"Bearer {self.settings.hermes_api_key}"}
        async with httpx.AsyncClient(base_url=self.settings.hermes_base_url, timeout=90) as client:
            async with client.stream("POST", "/v1/chat/completions", json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content") or choices[0].get("message", {}).get("content") or ""
                    if content:
                        yield content

    async def hermes_get_profile_state(self) -> dict[str, Any]:
        return {"hermes_enabled": self.settings.hermes_enabled, "base_url": self.settings.hermes_base_url}

    async def hermes_stream_events(self) -> dict[str, Any]:
        return {"mode": "backend-sse", "events": "Incident events are streamed from the product backend."}
