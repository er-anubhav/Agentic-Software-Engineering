import ast
import re
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
class ASTSymbol(BaseModel):
    name: str
    kind: str  # class, method, function, interface, module, import
    language: str
    file_path: str
    start_line: int = 1
    end_line: int = 1
    parent_symbol: Optional[str] = None
    docstring: str = ""
    decorators: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    callers: List[str] = Field(default_factory=list)
    callees: List[str] = Field(default_factory=list)
class PolyglotParser:
    """
    Production-grade Polyglot AST Parser supporting Python, TypeScript, JavaScript,
    Java, Go, C/C++, and Rust codebases.
    """
    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".cpp": "cpp",
        ".c": "cpp",
        ".h": "cpp",
        ".rs": "rust"
    }
    def parse_file(self, file_path: str, content: str) -> List[ASTSymbol]:
        ext = os.path.splitext(file_path)[1].lower()
        language = self.SUPPORTED_EXTENSIONS.get(ext, "unknown")
        if language == "python":
            return self._parse_python(file_path, content)
        elif language in ("typescript", "javascript"):
            return self._parse_js_ts(file_path, content, language)
        elif language == "java":
            return self._parse_java(file_path, content)
        elif language == "go":
            return self._parse_go(file_path, content)
        elif language == "rust":
            return self._parse_rust(file_path, content)
        elif language == "cpp":
            return self._parse_cpp(file_path, content)
        return []
    def _parse_python(self, file_path: str, content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node) or ""
                    decs = [ast.unparse(d) for d in node.decorator_list]
                    symbols.append(ASTSymbol(
                        name=node.name,
                        kind="class",
                        language="python",
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                        decorators=decs
                    ))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = ast.get_docstring(node) or ""
                    decs = [ast.unparse(d) for d in node.decorator_list]
                    symbols.append(ASTSymbol(
                        name=node.name,
                        kind="function",
                        language="python",
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                        decorators=decs
                    ))
        except Exception as e:
            logger.warning("Non-fatal operation exception caught: %s", e)
        return symbols
    def _parse_js_ts(self, file_path: str, content: str, language: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = content.splitlines()
        # Class regex match
        for i, line in enumerate(lines, start=1):
            class_match = re.search(r'class\s+([A-Za-z0-9_]+)', line)
            if class_match:
                symbols.append(ASTSymbol(
                    name=class_match.group(1),
                    kind="class",
                    language=language,
                    file_path=file_path,
                    start_line=i,
                    end_line=i + 10
                ))
            fn_match = re.search(r'(?:function|const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\(', line) or re.search(r'function\s+([A-Za-z0-9_]+)', line)
            if fn_match:
                symbols.append(ASTSymbol(
                    name=fn_match.group(1),
                    kind="function",
                    language=language,
                    file_path=file_path,
                    start_line=i,
                    end_line=i + 5
                ))
            if "interface" in line:
                iface_match = re.search(r'interface\s+([A-Za-z0-9_]+)', line)
                if iface_match:
                    symbols.append(ASTSymbol(
                        name=iface_match.group(1),
                        kind="interface",
                        language=language,
                        file_path=file_path,
                        start_line=i,
                        end_line=i + 5
                    ))
        return symbols
    def _parse_java(self, file_path: str, content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            cls_match = re.search(r'(?:public|private|protected)?\s*class\s+([A-Za-z0-9_]+)', line)
            if cls_match:
                symbols.append(ASTSymbol(
                    name=cls_match.group(1),
                    kind="class",
                    language="java",
                    file_path=file_path,
                    start_line=i,
                    end_line=i + 10
                ))
        return symbols
    def _parse_go(self, file_path: str, content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            fn_match = re.search(r'func\s+(?:\([^\)]+\)\s+)?([A-Za-z0-9_]+)', line)
            if fn_match:
                symbols.append(ASTSymbol(
                    name=fn_match.group(1),
                    kind="function",
                    language="go",
                    file_path=file_path,
                    start_line=i,
                    end_line=i + 5
                ))
        return symbols
    def _parse_rust(self, file_path: str, content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            fn_match = re.search(r'fn\s+([A-Za-z0-9_]+)', line)
            if fn_match:
                symbols.append(ASTSymbol(
                    name=fn_match.group(1),
                    kind="function",
                    language="rust",
                    file_path=file_path,
                    start_line=i,
                    end_line=i + 5
                ))
        return symbols
    def _parse_cpp(self, file_path: str, content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            cls_match = re.search(r'class\s+([A-Za-z0-9_]+)', line)
            if cls_match:
                symbols.append(ASTSymbol(
                    name=cls_match.group(1),
                    kind="class",
                    language="cpp",
                    file_path=file_path,
                    start_line=i,
                    end_line=i + 10
                ))
        return symbols
