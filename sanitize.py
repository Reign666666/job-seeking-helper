"""脱敏引擎：LLM 调用前，将简历中的敏感个人信息替换为占位符。

设计原则：
- 保守优先：宁可漏，不可误伤（误替换会破坏简历语义，如年份数字）。
- 仅替换「可明确判定」的字段：手机号 / 座机 / 邮箱 / 身份证 / 微信号 / 姓名 / 年龄。
- 输出：替换后的文本 + 命中的字段统计（供页面展示「即将发送给模型的内容」）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SensitiveHit:
    kind: str
    count: int
    examples: list = field(default_factory=list)


# (类型, 正则, 占位符, 是否需要上下文标签)
_RULES = [
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "【手机号】"),
    ("座机", re.compile(r"(?<!\d)0\d{2,3}-?\d{7,8}(?!\d)"), "【座机】"),
    ("邮箱", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "【邮箱】"),
    ("身份证", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "【身份证】"),
    ("微信号", re.compile(r"(?:微信号?|wechat)\s*[:：]?\s*[A-Za-z][A-Za-z0-9_-]{4,19}", re.I), "【微信号】"),
    ("QQ", re.compile(r"(?:qq|QQ)\s*[:：]?\s*[1-9]\d{4,10}"), "【QQ】"),
    ("姓名", re.compile(r"姓名\s*[:：]\s*([^\s，,。;；]{1,8})"), "【姓名】"),
    ("年龄", re.compile(r"年龄\s*[:：]\s*(\d{1,3})"), "【年龄】"),
    # 简历头部常见的「张三 | 4年经验 | 北京」形态：姓名位于行首且后随分隔符
    ("姓名", re.compile(r"(?m)^[\u4e00-\u9fa5]{2,4}(?=\s*[\|｜·•]\s*[0-9\u4e00-\u9fa5]{1,20}经验)"), "【姓名】"),
]

_PLACEHOLDER = {
    "手机号": "【手机号】", "座机": "【座机】", "邮箱": "【邮箱】", "身份证": "【身份证】",
    "微信号": "【微信号】", "QQ": "【QQ】", "姓名": "【姓名】", "年龄": "【年龄】",
}


def sanitize(text: str, mask_name: bool = True) -> tuple[str, list[SensitiveHit]]:
    """返回 (脱敏文本, 命中统计)。"""
    result = text
    hits: dict[str, SensitiveHit] = {}

    def _record(kind: str, example: str) -> None:
        h = hits.setdefault(kind, SensitiveHit(kind=kind, count=0))
        h.count += 1
        if len(h.examples) < 3:
            h.examples.append(example)

    for kind, pattern, placeholder in _RULES:
        if kind == "姓名" and not mask_name:
            continue

        def _sub(m: re.Match, _kind=kind, _ph=placeholder) -> str:
            _record(_kind, m.group(0).strip())
            return _ph

        result = pattern.sub(_sub, result)

    return result, list(hits.values())


def sanitize_preview(text: str, mask_name: bool = True, limit: int = 200) -> dict:
    """生成页面展示用的脱敏摘要。"""
    sanitized, hits = sanitize(text, mask_name=mask_name)
    head = sanitized[:limit]
    return {
        "sanitized_text": sanitized,
        "sensitive": [{"kind": h.kind, "count": h.count, "examples": h.examples} for h in hits],
        "preview": head + ("…" if len(sanitized) > limit else ""),
    }
