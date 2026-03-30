import tiktoken
from typing import List

ENCODING_NAME = "cl100k_base"


def count_tokens(text: str) -> int:
    """计算文本的 token 数量"""
    if not text:
        return 0
    enc = tiktoken.get_encoding(ENCODING_NAME)
    return len(enc.encode(text))


def count_tokens_messages(messages: List[dict], model: str = "gpt-4") -> int:
    """计算消息列表的 token 数量"""
    enc = tiktoken.encoding_for_model(model)
    total = 0
    for msg in messages:
        total += 4
        total += len(enc.encode(msg.get("content", "")))
        total += len(enc.encode(msg.get("role", "")))
    total += 2
    return total


def truncate_context(context: str, max_tokens: int = 4000) -> str:
    """动态截断上下文，保留最新内容"""
    if not context:
        return context

    tokens = count_tokens(context)
    if tokens <= max_tokens:
        return context

    enc = tiktoken.get_encoding(ENCODING_NAME)
    tokens_list = enc.encode(context)

    truncated_tokens = tokens_list[:max_tokens]
    truncated_text = enc.decode(truncated_tokens)

    return truncated_text


def truncate_text_keep_latest(text: str, max_tokens: int = 4000) -> str:
    """从文本末尾保留最新内容，截断旧内容"""
    if not text:
        return text

    tokens = count_tokens(text)
    if tokens <= max_tokens:
        return text

    enc = tiktoken.get_encoding(ENCODING_NAME)
    tokens_list = enc.encode(text)

    truncated_tokens = tokens_list[-max_tokens:]
    return enc.decode(truncated_tokens)


def truncate_text_from_end(text: str, max_tokens: int = 4000) -> str:
    """从文本末尾往前截断，保留开头部分（已废弃，请使用 truncate_text_keep_latest）"""
    return truncate_text_keep_latest(text, max_tokens)
