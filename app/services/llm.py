from typing import AsyncGenerator, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatGenerationChunk

from app.config import get_settings
from app.utils.tokenizer import count_tokens, truncate_text_keep_latest

settings = get_settings()


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            streaming=True,
            temperature=0.7,
        )
        self.system_prompt = """你是一个智能助手，专门帮助用户探索 only-students 平台上的笔记内容。

        你可以：
        1. 根据用户的提问，从笔记库中搜索相关内容并推荐
        2. 总结和解释笔记内容
        3. 回答用户关于笔记的问题
        4. 提供学习建议和资源推荐

        请用友好、专业的方式回答用户的问题。"""

    # 流式
    async def chat_stream(
        self,
        message: str,
        history: List[Dict[str, str]],
        context: str = "",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        system_prompt = self.system_prompt
        system_tokens = count_tokens(system_prompt)

        context_to_use = context
        if context:
            available_tokens = settings.max_context_tokens - system_tokens - 200
            if available_tokens > 0:
                context_tokens = count_tokens(context)
                if context_tokens > available_tokens:
                    context_to_use = truncate_text_keep_latest(context, available_tokens)
                    print(
                        f"[Token Control] Context truncated: {context_tokens} -> {available_tokens} tokens"
                    )

        messages = [SystemMessage(content=system_prompt)]

        if context_to_use:
            messages.append(SystemMessage(content=f"相关笔记内容：\n{context_to_use}"))

        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=message))

        # 这里一次性发给llm，流式一点点返回
        async for chunk in self.llm.astream(messages):
            if isinstance(chunk, ChatGenerationChunk):
                yield {"type": "content", "content": chunk.content}

    # 非流式
    def chat(self, message: str, context: str = "") -> str:
        system_prompt = self.system_prompt
        system_tokens = count_tokens(system_prompt)

        context_to_use = context
        if context:
            available_tokens = settings.max_context_tokens - system_tokens - 200
            if available_tokens > 0:
                context_tokens = count_tokens(context)
                if context_tokens > available_tokens:
                    context_to_use = truncate_text_keep_latest(context, available_tokens)

        messages = [SystemMessage(content=system_prompt)]

        if context_to_use:
            messages.append(SystemMessage(content=f"相关笔记内容：\n{context_to_use}"))

        messages.append(HumanMessage(content=message))

        response = self.llm.invoke(messages)
        return response.content


llm_service = LLMService()
