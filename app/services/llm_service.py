from typing import Type

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    google_api_key=settings.gemini_api_key,
    temperature=0.3,
)

async def call_llm(
    system: str,
    prompt: str,
    response_schema: Type[BaseModel] | None = None,
    json_mode: bool = True,
):
    messages = [
        SystemMessage(content=system),
        HumanMessage(content=prompt),
    ]

    if not json_mode:
        response = await llm.ainvoke(messages)
        content = response.content
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            )
        return str(content).strip() if content else ""

    if response_schema is None:
        raise ValueError("response_schema is required when json_mode=True")

    llm_with_structured_output = llm.with_structured_output(
        response_schema,
        method="json_schema",
    )

    try:
        response = await llm_with_structured_output.ainvoke(messages)
    except Exception:
        logger.exception("Structured LLM call failed")
        return {}

    if isinstance(response, BaseModel):
        return response.model_dump()
    if isinstance(response, dict):
        return response

    logger.warning("Unexpected structured output type: %s", type(response))
    return {}


def to_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}
