"""Read optional local KEY=value configuration without executing shell code."""

import os
from pathlib import Path


ALLOWED_KEYS = {
    "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL",
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL",
    "MODEL_TIMEOUT_SECONDS", "MODEL_MAX_TOKENS",
}


def environment(env_file: Path | None = None) -> dict[str, str]:
    values = dict(os.environ)
    if env_file is None:
        return values
    raw = env_file.read_text(encoding="utf-8")
    if len(raw) > 65536:
        raise ValueError("本地环境文件过大。")
    seen = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not separator or key not in ALLOWED_KEYS or key in seen:
            raise ValueError("环境文件仅接受已知变量的一行一个 KEY=value，不支持重复键或 shell 语法。")
        if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
            value = value[1:-1]
        values[key] = value
        seen.add(key)
    return values
