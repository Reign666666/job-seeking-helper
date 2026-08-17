"""LLM 客户端：OpenAI 兼容接口（DeepSeek / 通义 / GLM / OpenAI 等）。

- 通过 httpx 直连，不依赖各家 SDK。
- response_format=json_object 仅对部分服务商可用：若服务商返回 400，
  自动降级为纯文本后本地解析 JSON。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import httpx


@dataclass
class LLMConfig:
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-chat"

    def is_ready(self) -> bool:
        return bool(self.api_key.strip())


class LLMError(Exception):
    pass


def _extract_json(text: str) -> dict:
    """从模型输出中稳健提取 JSON 对象。"""
    text = text.strip()
    # 去掉可能的 markdown 代码围栏
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    # 直接尝试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 提取第一个 { ... } 平衡块
    start = text.find("{")
    if start == -1:
        snippet = f"（返回内容开头：{text[:100]}…）" if text.strip() else "（返回内容为空）"
        raise LLMError(f"模型输出中未找到 JSON 内容{snippet}。若刚修改过 Base URL，请检查地址是否正确（应指向 OpenAI 兼容接口，如 …/v1）。")
    depth, end = 0, -1
    in_str, esc = False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        raise LLMError("模型输出 JSON 结构不完整")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        raise LLMError(f"模型输出 JSON 解析失败：{e}")


def _post(config: LLMConfig, system: str, user: str, timeout: float, json_mode: bool) -> str:
    """发起 chat/completions 请求，返回模型输出的原始文本。"""
    if not config.is_ready():
        raise LLMError("尚未配置大模型 API Key，请先点击右上角「模型设置」完成配置。")

    url = config.base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key.strip()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.model.strip(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            if json_mode:
                # 优先尝试 json_object 模式；部分服务商不支持会 400，降级重试
                payload["response_format"] = {"type": "json_object"}
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code == 400 and "response_format" in payload:
                    payload.pop("response_format")
                    resp = client.post(url, json=payload, headers=headers)
            else:
                resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        body = e.response.text[:300]
        status = e.response.status_code
        if status in (401, 403):
            raise LLMError("API Key 无效或无权限（401/403），请检查模型设置中的 Key。")
        if status == 404:
            raise LLMError("接口地址或模型名不正确（404）。常见原因：base_url 未以 /v1 结尾，或模型名拼写错误。")
        if status == 429:
            raise LLMError("请求过于频繁或额度不足（429），请稍后重试或检查账户余额。")
        # 400 等错误：优先展示服务商自己的提示（通常包含可用模型名等）
        try:
            detail = (e.response.json().get("error") or {}).get("message") or body
        except Exception:  # noqa: BLE001
            detail = body
        raise LLMError(f"模型接口返回错误 {status}：{detail}")
    except httpx.ConnectError:
        raise LLMError("无法连接到模型服务，请检查 base_url 与网络连接。")
    except httpx.TimeoutException:
        raise LLMError("模型响应超时，请稍后重试（可尝试更换模型）。")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise LLMError(f"模型返回格式异常：{e}")


def chat(config: LLMConfig, system: str, user: str, timeout: float = 240.0) -> dict:
    """调用对话接口并返回解析后的 JSON 对象（用于分析等结构化场景）。"""
    content = _post(config, system, user, timeout, json_mode=True)
    return _extract_json(content)


def chat_raw(config: LLMConfig, system: str, user: str, timeout: float = 240.0) -> str:
    """调用对话接口，返回模型原始文本（不要求 JSON）。"""
    return _post(config, system, user, timeout, json_mode=False)


def ping(config: LLMConfig, timeout: float = 60.0) -> str:
    """连通性测试：让模型回一个词，走纯文本通道，不要求 JSON。"""
    content = chat_raw(config, "你是一个连通性测试助手。", "请只回复两个字：正常", timeout=timeout)
    if content and content.strip():
        return "模型连通正常"
    raise LLMError("模型返回内容为空，请检查 Base URL 与模型名。")
