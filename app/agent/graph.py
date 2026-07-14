"""LangGraph ReAct agent for code review."""

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from loguru import logger

from app.agent.tools.git_diff_tool import get_git_diff
from app.agent.tools.linters_tool import run_linters
from app.agent.tools.semgrep_tool import run_semgrep
from app.agent.tools.tree_sitter_tool import parse_ast
from app.config import get_settings

settings = get_settings()

# All tools available to the ReAct agent
REVIEW_TOOLS = [run_semgrep, run_linters, parse_ast, get_git_diff]


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
        max_tokens=4096,
    )


def _extract_json_from_response(text: str) -> dict:
    """Extract JSON block from LLM response text."""
    # Try to find JSON code block first
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try to parse the whole response as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: extract innermost {...}
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning("Could not extract JSON from LLM response")
    return {"summary": text, "issues": []}


async def run_review_agent(
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    """Run the LangGraph ReAct agent and return the structured review result.

    Returns a dict with keys: summary (str), issues (list[dict]).
    """
    llm = _build_llm()
    agent = create_react_agent(llm, REVIEW_TOOLS)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    logger.info("Starting LangGraph review agent")
    try:
        result = await agent.ainvoke({"messages": messages})
        # The final message from the agent is the last AIMessage
        final_messages = result.get("messages", [])
        response_text = ""
        for msg in reversed(final_messages):
            if hasattr(msg, "content") and isinstance(msg.content, str):
                response_text = msg.content
                break

        return _extract_json_from_response(response_text)
    except Exception as exc:
        logger.error(f"LangGraph agent error: {exc}")
        return {"summary": f"Agent error: {exc}", "issues": []}
