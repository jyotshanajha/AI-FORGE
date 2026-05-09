from collections.abc import AsyncGenerator
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage, HumanMessage

from app.ai.llm import llm

logger = logging.getLogger(__name__)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a concise and helpful assistant."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{human_input}"),
    ]
)

chain: Runnable | None = None
if llm is not None:
    chain = prompt | llm | StrOutputParser()
else:
    logger.warning("LLM not initialized - chat functionality will be unavailable")


async def stream_chat_response(
    message: str,
    history: list[dict[str, str]],
    user_email: str,
) -> AsyncGenerator[str, None]:
    if chain is None:
        yield "I apologize, but the AI service is currently unavailable. Please try again later."
        return
        
    history_messages = []
    for item in history:
        if item["role"] == "user":
            history_messages.append(HumanMessage(content=item["content"]))
        else:
            history_messages.append(AIMessage(content=item["content"]))

    async for chunk in chain.astream(
        {"human_input": message, "history": history_messages},
        config={"metadata": {"user_email": user_email}},
    ):
        yield chunk
