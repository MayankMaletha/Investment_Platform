"""
services/chat_service.py — Conversational AI service using LangChain + tools.

The chat endpoint uses a tool-calling agent that can:
- Look up stock prices and technical data
- Fetch and analyze news
- Query the user's portfolio
- Answer financial questions via RAG

This is distinct from the analysis workflow: it's a conversational interface
that calls tools on demand, whereas the analysis workflow is a structured pipeline.
"""

import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.logging import logger
from memory.memory_manager import MemoryManager
from tools.financial_tools import ALL_FINANCIAL_TOOLS


CHAT_SYSTEM_PROMPT = """You are an expert AI investment advisor with deep knowledge of:
- Equity and cryptocurrency markets
- Technical and fundamental analysis
- Portfolio management and risk assessment
- Financial news and market sentiment

You have access to real-time tools for stock prices, technical indicators, and news.
Always ground your advice in current data. When analyzing stocks, always use the tools.

Be conversational but professional. Provide clear, actionable insights.
Acknowledge uncertainty when data is insufficient.
Always remind users that this is not financial advice and they should consult a professional."""


class ChatService:
    """Manages conversational AI sessions with memory and tool access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _build_agent(self):
        """Build a LangChain tool-calling agent with financial tools."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain.agents import create_tool_calling_agent, AgentExecutor
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=settings.OPENAI_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                streaming=False,
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", CHAT_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ])

            agent = create_tool_calling_agent(llm, ALL_FINANCIAL_TOOLS, prompt)
            return AgentExecutor(
                agent=agent,
                tools=ALL_FINANCIAL_TOOLS,
                max_iterations=5,
                verbose=settings.DEBUG,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
            )
        except Exception as e:
            logger.warning("Agent build failed, using simple LLM", error=str(e))
            return None

    async def process_message(
        self,
        user_id: str,
        session_id: str,
        message: str,
        context: dict,
    ) -> dict:
        """
        Process a user message through the conversational agent.
        Returns response, agent steps, and tools used.
        """
        memory_mgr = MemoryManager(user_id)

        # Load conversation history
        history = await memory_mgr.get_recent_messages(session_id, limit=10, db=self.db)

        # Retrieve relevant long-term memories
        user_context = await memory_mgr.get_user_context_summary(message)

        # Enrich message with any inline context (e.g. currently viewed symbol)
        enriched_message = message
        if context.get("symbol"):
            enriched_message += f"\n[Context: User is looking at {context['symbol']}]"
        if user_context:
            enriched_message += f"\n{user_context}"

        agent = self._build_agent()
        response_text = ""
        tools_used = []
        steps = []

        if agent:
            # Convert history to LangChain message format
            from langchain_core.messages import HumanMessage, AIMessage
            chat_history = []
            for msg in history:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))

            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: agent.invoke({
                        "input": enriched_message,
                        "chat_history": chat_history,
                    }),
                )
                response_text = result.get("output", "")
                intermediate = result.get("intermediate_steps", [])
                for action, observation in intermediate:
                    tool_name = getattr(action, "tool", str(action))
                    tools_used.append(tool_name)
                    steps.append(f"Used tool: {tool_name}")
            except Exception as e:
                logger.error("Agent invocation failed", error=str(e))
                response_text = await self._fallback_response(message)
        else:
            response_text = await self._fallback_response(message)

        # Persist both turns to memory
        await memory_mgr.save_message(session_id, "user", message, db=self.db)
        await memory_mgr.save_message(session_id, "assistant", response_text, db=self.db)

        return {
            "response": response_text,
            "steps": steps,
            "tools_used": list(set(tools_used)),
        }

    async def _fallback_response(self, message: str) -> str:
        """Simple LLM response when agent is unavailable."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage
            llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.3, api_key=settings.OPENAI_API_KEY)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: llm.invoke([
                    SystemMessage(content=CHAT_SYSTEM_PROMPT),
                    HumanMessage(content=message),
                ])
            )
            return response.content
        except Exception as e:
            return (
                f"I apologize, but I'm having trouble processing your request right now. "
                f"Please try again or use the /analyze-stock endpoint for detailed analysis. "
                f"Error: {str(e)}"
            )
