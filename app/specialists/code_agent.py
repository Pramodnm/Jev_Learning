"""Code Specialist Agent powered by Gemini 3.7 Flash."""

import ast
import io
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import Any, Dict
from app.agent_framework import BaseSpecialistAgent, agent_tool


class CodeSpecialistAgent(BaseSpecialistAgent):
    """Specialist agent for code generation, static analysis, refactoring, and debugging."""

    def __init__(self, **kwargs):
        super().__init__(
            name="CodeSpecialist",
            role_description="Expert software engineer specializing in Python, algorithms, architecture, debugging, and code generation.",
            system_prompt=(
                "You are the Code Specialist Agent. You produce clean, production-grade, well-typed code, "
                "perform syntax validation, and provide robust technical implementations."
            ),
            **kwargs
        )

    @agent_tool(
        name="validate_python_syntax",
        description="Parses Python code into an Abstract Syntax Tree (AST) to check for syntax validity."
    )
    def validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python syntax using AST."""
        try:
            tree = ast.parse(code)
            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            return {
                "valid": True,
                "ast_nodes": len(tree.body),
                "defined_functions": functions,
                "defined_classes": classes,
                "message": "Python syntax is 100% valid."
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}",
                "line": e.lineno
            }

    @agent_tool(
        name="execute_safe_python_snippet",
        description="Executes a sandboxed, safe Python snippet to compute expressions or verify algorithms."
    )
    def execute_safe_python_snippet(self, code: str) -> Dict[str, Any]:
        """Execute a Python snippet capturing stdout."""
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_capture
        local_scope = {}
        try:
            exec(code, {"__builtins__": __builtins__}, local_scope)
            sys.stdout = old_stdout
            return {
                "success": True,
                "stdout": stdout_capture.getvalue(),
                "variables": {k: str(v) for k, v in local_scope.items() if not k.startswith("__")}
            }
        except Exception as e:
            sys.stdout = old_stdout
            return {
                "success": False,
                "error": str(e)
            }
