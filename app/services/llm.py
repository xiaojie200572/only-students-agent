from typing import AsyncGenerator, List, Dict, Any
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatGenerationChunk

from app.config import get_settings

settings = get_settings()


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
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

    async def chat_stream(
        self,
        message: str,
        history: List[Dict[str, str]],
        context: str = "",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        messages = [SystemMessage(content=self.system_prompt)]
        
        if context:
            messages.append(SystemMessage(content=f"相关笔记内容：\n{context}"))
        
        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=message))
        
        async for chunk in self.llm.astream(messages):
            if isinstance(chunk, ChatGenerationChunk):
                yield {"type": "content", "content": chunk.content}

    def chat(self, message: str, context: str = "") -> str:
        messages = [SystemMessage(content=self.system_prompt)]
        
        if context:
            messages.append(SystemMessage(content=f"相关笔记内容：\n{context}"))
        
        messages.append(HumanMessage(content=message))
        
        response = self.llm.invoke(messages)
        return response.content


llm_service = LLMService()
