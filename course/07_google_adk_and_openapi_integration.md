# Chapter 7: Google ADK and OpenAPI Integration

This chapter covers building production-ready tool definitions, OpenAPI function schemas, and agent execution interfaces that conform to both the Google Agent Development Kit (ADK) and OpenAI standards.

---

## 7.1 OpenAPI-Compliant Tool Schemas

To enable specialist agents to interact with environments, functions must be decorated with standard OpenAPI parameter types:

```python
import inspect
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel

def agent_tool(name: Optional[str] = None, description: Optional[str] = None):
    """Decorator exposing Python functions as OpenAPI / Google ADK tools."""
    def decorator(fn: Callable[..., Any]):
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or "").strip()
        sig = inspect.signature(fn)
        
        properties: Dict[str, Any] = {}
        required: List[str] = []

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
            properties[p_name] = {
                "type": type_map.get(py_type, "string"),
                "description": f"Parameter {p_name}"
            }
            if param.default == inspect.Parameter.empty:
                required.append(p_name)

        fn._tool_def = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_desc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
        return fn
    return decorator
```

---

## 7.2 FastAPI OpenAPI Surface

In `app/api.py`, our application automatically serves full Swagger UI and ReDoc documentation:
- Interactive UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`
- OpenAPI JSON Spec: `http://localhost:8000/openapi.json`

This enables immediate integration with external agent frameworks, LangChain, LlamaIndex, AutoGen, and enterprise API gateways.
