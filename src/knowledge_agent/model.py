"""DeepSeek and optional OpenAI Chat Completions function-calling adapters."""

import json
import math
import os
import urllib.error
import urllib.request
from typing import Mapping
from urllib.parse import urlsplit

from .types import Action, ModelError, ModelProtocolError


class OpenAICompatibleModel:
    execution_mode = "live_model"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1", timeout: float = 30, max_tokens: int = 4096):
        if not api_key.strip() or not model.strip():
            raise ValueError("真实模型模式需要 OPENAI_API_KEY 和 OPENAI_MODEL。")
        parsed = urlsplit(base_url)
        if (
            not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or (parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1")))
        ):
            raise ValueError("OPENAI_BASE_URL 必须是 HTTPS 地址；仅本机测试允许 HTTP。")
        if not math.isfinite(timeout) or not 0 < timeout <= 60 or type(max_tokens) is not int or not 1 <= max_tokens <= 32768:
            raise ValueError("timeout 必须为 0–60 秒，max_tokens 必须为 1–32768。")
        self._api_key = api_key
        self.model = model
        self.name = "openai-compatible:" + model
        self.endpoint = base_url.rstrip("/") + "/chat/completions"
        self.timeout = timeout
        self.max_tokens = max_tokens

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "OpenAICompatibleModel":
        env = os.environ if environ is None else environ
        try:
            return cls(
                env.get("OPENAI_API_KEY", ""), env.get("OPENAI_MODEL", ""),
                env.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                float(env.get("MODEL_TIMEOUT_SECONDS", "30")),
                int(env.get("MODEL_MAX_TOKENS", "4096")),
            )
        except (TypeError, ValueError) as exc:
            # Do not echo environment values, including a malformed URL containing a key.
            raise ValueError("模型配置无效；请检查密钥、模型名、HTTPS 地址和数值范围。") from exc

    def build_payload(self, messages: list[dict], tools: list[dict]) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "required",
            "parallel_tool_calls": False,
            "max_completion_tokens": self.max_tokens,
        }

    def choose(self, messages: list[dict], tools: list[dict]) -> Action:
        payload = self.build_payload(messages, tools)
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self._api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ModelProtocolError("模型响应超过大小上限。")
        except urllib.error.HTTPError as exc:
            raise ModelError(f"模型 API 返回 HTTP {exc.code}；未自动重试，也未切换为 Mock。") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ModelError("模型 API 网络错误或超时；未自动重试，也未切换为 Mock。") from None
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ModelProtocolError("模型 API 没有返回有效 JSON。") from None
        return self.parse_response(data)

    @staticmethod
    def parse_response(data: object) -> Action:
        try:
            if not isinstance(data, dict):
                raise ValueError
            choice = data["choices"][0]
            if choice.get("finish_reason") not in ("tool_calls", "stop"):
                raise ValueError
            calls = choice["message"].get("tool_calls", [])
            if not isinstance(calls, list) or len(calls) != 1:
                raise ValueError
            call = calls[0]
            if call["type"] != "function" or not isinstance(call["id"], str) or not call["id"]:
                raise ValueError
            name = call["function"]["name"]
            raw_arguments = call["function"]["arguments"]
            if not isinstance(name, str) or not isinstance(raw_arguments, str) or len(raw_arguments) > 50000:
                raise ValueError
            arguments = json.loads(raw_arguments)
            if not isinstance(arguments, dict):
                raise ValueError
            metadata = {key: data[key] for key in ("id", "model") if isinstance(data.get(key), str)}
            usage = data.get("usage")
            if isinstance(usage, dict):
                metadata["usage"] = {
                    key: usage[key] for key in ("prompt_tokens", "completion_tokens", "total_tokens")
                    if type(usage.get(key)) is int and usage[key] >= 0
                }
            # Deliberately discard reasoning_content and free-form assistant content.
            return Action(name, arguments, call["id"], metadata)
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            raise ModelProtocolError("需要且仅接受一个有效的 function tool call；请按 schema 重新选择动作。") from None


class DeepSeekModel(OpenAICompatibleModel):
    """Standard endpoint, non-thinking mode; no Beta strict-mode dependency."""

    def __init__(self, api_key: str, model: str = "deepseek-flash", base_url: str = "https://api.deepseek.com", timeout: float = 30, max_tokens: int = 4096):
        super().__init__(api_key, model, base_url, timeout, max_tokens)
        self.name = "deepseek:" + model

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "DeepSeekModel":
        env = os.environ if environ is None else environ
        try:
            return cls(
                env.get("DEEPSEEK_API_KEY", ""),
                env.get("DEEPSEEK_MODEL", "deepseek-flash"),
                env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                float(env.get("MODEL_TIMEOUT_SECONDS", "30")),
                int(env.get("MODEL_MAX_TOKENS", "4096")),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("DeepSeek 配置无效；请设置 DEEPSEEK_API_KEY，并检查模型名、HTTPS 地址和数值范围。") from exc

    def build_payload(self, messages: list[dict], tools: list[dict]) -> dict:
        copied_tools = json.loads(json.dumps(tools))
        for tool in copied_tools:
            tool["function"].pop("strict", None)
        return {
            "model": self.model,
            "messages": messages,
            "tools": copied_tools,
            "tool_choice": "required",
            "thinking": {"type": "disabled"},
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }
