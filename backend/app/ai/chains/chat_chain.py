from collections.abc import AsyncGenerator
from typing import Any, Literal
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.ai.llm import llm

logger = logging.getLogger(__name__)

# System prompt for RAG mode (document-aware)
RAG_SYSTEM_PROMPT = """You are a concise and helpful assistant for Amzur employees.

When the user attaches files, follow these rules strictly:
- PDF documents: you may have access to extracted text from these via the provided context. Answer questions based on that context.
- Images: analyse the image content directly and respond to the user's question about it.
- Video files: analyse the provided video frames and describe what you see accurately. The frames are extracted evenly across the full video.
- Excel / CSV / spreadsheet files: the data will be provided to you as a text table. Answer questions based on that data.
- Code files: you can discuss and help with code; ask the user to paste the code or describe the issue.
- Other files: acknowledge the attachment by name and type, and tell the user you cannot read its contents directly.

Never fabricate or guess the contents of any attached file unless the data has been explicitly provided to you in the conversation."""

# System prompt for LLM mode (general knowledge, no document context)
LLM_SYSTEM_PROMPT = """You are a concise and helpful assistant for Amzur employees.
Provide helpful, accurate answers based on your knowledge only. 
Do NOT reference, analyze, or claim to have access to any attached documents or files.
If asked about a document, explain that you don't have access to attachments in this mode."""

rag_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", RAG_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{human_input}"),
    ]
)

llm_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", LLM_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{human_input}"),
    ]
)

rag_chain: Runnable | None = None
llm_chain: Runnable | None = None
if llm is not None:
    rag_chain = rag_prompt | llm | StrOutputParser()
    llm_chain = llm_prompt | llm | StrOutputParser()
else:
    logger.warning("LLM not initialized - chat functionality will be unavailable")


async def stream_chat_response(
    message: str,
    history: list[dict[str, str]],
    user_email: str,
    multimodal_parts: list[dict[str, Any]] | None = None,
    response_mode: Literal["rag", "llm", "sql"] = "rag",
) -> AsyncGenerator[str, None]:
    """Stream a chat response.

    When multimodal_parts is provided the human message is built as a list of
    content parts and sent directly to the LLM — bypassing ChatPromptTemplate
    so the list type is preserved (template formatting would stringify it).
    
    Args:
        message: The user's message
        history: Conversation history
        user_email: Email of the user for tracking
        multimodal_parts: Optional multimodal content (images, video frames, etc.)
        response_mode: "rag" for document-aware responses, "llm" for general knowledge only
    """
    if llm is None:
        yield "I apologize, but the AI service is currently unavailable. Please try again later."
        return

    history_messages: list[AIMessage | HumanMessage] = []
    for item in history:
        if item["role"] == "user":
            history_messages.append(HumanMessage(content=item["content"]))
        else:
            history_messages.append(AIMessage(content=item["content"]))

    if multimodal_parts:
        # Build the full message list manually so the content list type is preserved.
        system_prompt = RAG_SYSTEM_PROMPT if response_mode == "rag" else LLM_SYSTEM_PROMPT
        messages: list[SystemMessage | AIMessage | HumanMessage] = [
            SystemMessage(content=system_prompt),
            *history_messages,
            HumanMessage(content=[{"type": "text", "text": message}] + multimodal_parts),
        ]
        async for chunk in llm.astream(
            messages,
            config={"metadata": {"user_email": user_email}},
        ):
            content = chunk.content if hasattr(chunk, "content") else ""
            if isinstance(content, str) and content:
                yield content
    else:
        chain = rag_chain if response_mode == "rag" else llm_chain
        if chain is None:
            yield "I apologize, but the AI service is currently unavailable. Please try again later."
            return
        async for chunk in chain.astream(
            {"human_input": message, "history": history_messages},
            config={"metadata": {"user_email": user_email}},
        ):
            yield chunk

