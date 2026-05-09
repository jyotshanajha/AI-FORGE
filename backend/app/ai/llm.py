import logging
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

llm = None
client = None
embeddings = None

try:
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        base_url=settings.LITELLM_PROXY_URL,
        api_key=settings.LITELLM_API_KEY,
        timeout=30,
        max_retries=2,
    )
    logger.info("LLM initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize LLM: {e}. LLM features will be unavailable.")

try:
    client = OpenAI(
        api_key=settings.LITELLM_API_KEY,
        base_url=settings.LITELLM_PROXY_URL,
    )
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize OpenAI client: {e}")

try:
    embeddings = OpenAIEmbeddings(
        model=settings.LITELLM_EMBEDDING_MODEL,
        base_url=settings.LITELLM_PROXY_URL,
        api_key=settings.LITELLM_API_KEY,
    )
    logger.info("Embeddings initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize embeddings: {e}")
