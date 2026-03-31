from typing import AsyncGenerator, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.config import get_settings
from app.tools.rag_tool import search_notes
from app.tools.note_reader import read_note
from app.tools.user_info import get_user_info, get_current_user_info

settings = get_settings()

SYSTEM_PROMPT = """你是一个智能助手，专门帮助用户探索 only-students 平台上的笔记内容。

你可以使用的工具：
1. search_notes: 搜索站内笔记内容。当用户询问关于某个主题的笔记时使用。
2. read_note: 读取指定笔记的详细内容。当需要获取某篇笔记的完整内容时使用。
3. get_user_info: 获取用户详细信息。当需要了解某个用户的个人信息时使用。
4. get_current_user_info: 获取当前登录用户的信息。

工作流程（Plan-Act 模式）：
1. 先理解用户问题，思考需要哪些步骤
2. 按需调用工具获取信息
3. 整合所有信息生成答案

请用友好、专业的方式回答用户的问题。
如果需要调用工具，请直接调用，不要询问用户确认。
"""


class AgentService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            streaming=True,
            temperature=0.7,
        )

        self.tools = [search_notes, read_note, get_user_info, get_current_user_info]

        self.system_message = SYSTEM_PROMPT

        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_message,
        )

    async def chat_stream(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        history = history or []

        messages = []

        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=message))

        try:
            # 实时返回 Agent 执行过程中的各种事件。
            async for event in self.agent.astream_events(
                {"messages": messages},
                version="v1",
            ):
                """
                event = {
                    "event": "on_chat_model_stream",    # 事件类型（字符串）
                    "name": "ChatOpenAI",               # 模型/工具名
                    "data": {                           # 数据（字典）
                        "chunk": {                      # 内容块（字典）
                            "content": "你好"           # 实际文本
                        }
                    }
                }
                """
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield {"type": "content", "content": content}
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    yield {"type": "tool_start", "tool": tool_name}
                elif kind == "on_tool_end":
                    tool_name = event["name"]
                    yield {"type": "tool_end", "tool": tool_name}
        except Exception as e:
            yield {"type": "error", "content": str(e)}


agent_service = AgentService()
