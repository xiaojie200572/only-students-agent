import httpx
import json
import sys

# 设置 UTF-8 编码
sys.stdout.reconfigure(encoding="utf-8")


def parse_sse_line(line):
    """解析 SSE 行，提取并返回易读的格式"""
    if not line or not line.startswith("data:"):
        return None

    try:
        data_str = line[5:].strip()
        data = json.loads(data_str)
        data_type = data.get("type")

        if data_type == "status":
            return f"[状态] {data.get('content')}"
        elif data_type == "content":
            return f"[内容] {data.get('content')}"
        elif data_type == "source":
            sources = data.get("sources", [])
            return f"[来源] {len(sources)} 条"
        elif data_type == "tool":
            tool_name = data.get("tool", "")
            tool_event = data.get("type", "")
            return f"[工具] {tool_event}: {tool_name}"
        elif data_type == "done":
            content = data.get("content", "")
            sources = data.get("sources", [])
            tools = data.get("tools", [])
            result = f"\n[完成]\n回复: {content}\n"
            result += f"来源: {len(sources)} 条\n" if sources else ""
            result += f"工具: {tools}\n" if tools else ""
            return result
        elif data_type == "error":
            return f"[错误] {data.get('message')}"
        else:
            return f"[{data_type}] {data}"
    except:
        return None


print("=" * 50)
print("测试 RAG 模式 (use_rag=True)")
print("=" * 50)

with httpx.stream(
    "POST",
    "http://localhost:8000/api/agent/chat",
    json={"session_id": "test", "message": "你好", "use_rag": True},
    timeout=60.0,
) as response:
    for line in response.iter_lines():
        if line:
            parsed = parse_sse_line(line)
            if parsed:
                print(parsed)

print("\n" + "=" * 50)
print("测试 Agent 模式 (use_agent=True)")
print("=" * 50)

with httpx.stream(
    "POST",
    "http://localhost:8000/api/agent/chat",
    json={"session_id": "test2", "message": "找一些Python学习的笔记", "use_agent": True},
    timeout=60.0,
) as response:
    for line in response.iter_lines():
        if line:
            parsed = parse_sse_line(line)
            if parsed:
                print(parsed)
