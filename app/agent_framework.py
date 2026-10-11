"""Google ADK & OpenAPI-Compatible Agent Framework.

Provides base classes, tool schemas, and ReAct execution loops for
specialist agents powered by Gemini 3.7 Flash.
"""

from __future__ import annotations
import inspect
import json
import sys
import time
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type
import httpx
from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import settings


# ---------------------------------------------------------------------------
# Tool & Message Schemas
# ---------------------------------------------------------------------------

class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    fn: Optional[Callable[..., Any]] = Field(default=None, exclude=True)


class AgentMessage(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class AgentRunResult(BaseModel):
    agent_name: str
    output: str
    model: str
    tool_executions: List[Dict[str, Any]] = Field(default_factory=list)
    total_tokens: int = 0
    reasoning_tokens: int = 0
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Tool Decorator
# ---------------------------------------------------------------------------

def agent_tool(name: Optional[str] = None, description: Optional[str] = None):
    """Decorator to expose Python functions as OpenAPI / Google ADK compliant tools."""
    def decorator(fn: Callable[..., Any]):
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or "").strip()
        sig = inspect.signature(fn)
        
        properties: Dict[str, Any] = {}
        required_params: List[str] = []

        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }

        for p_name, param in sig.parameters.items():
            if p_name in ("self", "cls"):
                continue
            py_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            schema_type = type_map.get(py_type, "string")
            properties[p_name] = {
                "type": schema_type,
                "description": f"Parameter {p_name}"
            }
            if param.default == inspect.Parameter.empty:
                required_params.append(p_name)

        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_desc,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required_params
            },
            fn=fn
        )
        fn._tool_def = tool_def
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Base Specialist Agent
# ---------------------------------------------------------------------------

class BaseSpecialistAgent(ABC):
    """Base class for all specialist agents running with Gemini 3.7 Flash."""

    def __init__(
        self,
        name: str,
        role_description: str,
        system_prompt: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.name = name
        self.role_description = role_description
        self.system_prompt = system_prompt
        self.model = model or settings.specialist_model
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.api_key = api_key or settings.api_key
        
        self.openai_client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            http_client=httpx.Client(timeout=60.0)
        )
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_decorated_tools()

    def _register_decorated_tools(self):
        """Automatically register methods decorated with @agent_tool."""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_tool_def"):
                tool_def: ToolDefinition = getattr(attr, "_tool_def")
                tool_def.fn = attr
                self.tools[tool_def.name] = tool_def

    def register_tool(self, tool: ToolDefinition):
        """Register an external tool definition."""
        self.tools[tool.name] = tool

    def get_openapi_tools_schema(self) -> List[Dict[str, Any]]:
        """Return tools in standard OpenAPI / OpenAI Function format."""
        schema_list = []
        for tool in self.tools.values():
            schema_list.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return schema_list

    def execute_task(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> AgentRunResult:
        """Execute a user task with ReAct tool calling and Gemini 3.7 Flash."""
        start_time = time.perf_counter()
        tool_executions: List[Dict[str, Any]] = []
        total_tokens = 0
        reasoning_tokens = 0

        # Construct message history
        full_system_prompt = f"{self.system_prompt}\n\nAgent Name: {self.name}\nRole: {self.role_description}"
        if context:
            full_system_prompt += f"\n\nTask Context:\n{json.dumps(context, indent=2)}"

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        tools_schema = self.get_openapi_tools_schema()

        # Multi-turn tool calling loop (max 5 iterations)
        max_iterations = 5
        final_content = ""

        for iteration in range(max_iterations):
            req_kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2
            }
            if tools_schema:
                req_kwargs["tools"] = tools_schema
                req_kwargs["tool_choice"] = "auto"

            try:
                response = self.openai_client.chat.completions.create(**req_kwargs)
            except Exception as e:
                # If error occurs, fallback response
                final_content = f"[{self.name}] Error invoking execution model {self.model}: {str(e)}"
                break

            choice = response.choices[0]
            message = choice.message
            
            # Track usage
            if response.usage:
                total_tokens += response.usage.total_tokens or 0
                if hasattr(response.usage, "completion_tokens_details") and response.usage.completion_tokens_details:
                    reasoning_tokens += getattr(response.usage.completion_tokens_details, "reasoning_tokens", 0) or 0

            # Check if tools were called
            if message.tool_calls:
                # Append assistant tool call message
                messages.append(message.model_dump(exclude_none=True))

                for tool_call in message.tool_calls:
                    fn_name = tool_call.function.name
                    raw_args = tool_call.function.arguments
                    try:
                        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except Exception:
                        args = {}

                    # Execute tool
                    if fn_name in self.tools:
                        try:
                            tool_result = self.tools[fn_name].fn(**args)
                            result_str = json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)
                        except Exception as tool_err:
                            result_str = f"Error executing {fn_name}: {str(tool_err)}"
                    else:
                        result_str = f"Error: Tool '{fn_name}' not found."

                    tool_executions.append({
                        "iteration": iteration + 1,
                        "tool": fn_name,
                        "arguments": args,
                        "result": result_str
                    })

                    # Append tool result message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": result_str
                    })
            else:
                # No more tools called, final answer produced
                final_content = message.content or ""
                break

        latency = (time.perf_counter() - start_time) * 1000.0

        return AgentRunResult(
            agent_name=self.name,
            output=final_content,
            model=self.model,
            tool_executions=tool_executions,
            total_tokens=total_tokens,
            reasoning_tokens=reasoning_tokens,
            latency_ms=round(latency, 2)
        )
