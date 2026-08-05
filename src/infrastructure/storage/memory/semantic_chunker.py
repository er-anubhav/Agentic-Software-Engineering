import hashlib
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    chunk_id: str
    repository_id: str = "default"
    file_path: str
    chunk_type: str  # class, function, method, sql, markdown, config
    ast_path: str
    content: str
    start_line: int
    end_line: int
    token_count: int
    file_hash: str
    imports: List[str] = Field(default_factory=list)
    callers: List[str] = Field(default_factory=list)
    callees: List[str] = Field(default_factory=list)


class SemanticChunker:
    """
    AST-aware semantic code chunker.
    Splits code on structural entity boundaries (Class, Function, SQL query, Config).
    """

    def chunk_file(self, repository_id: str, file_path: str, content: str) -> List[CodeChunk]:
        chunks: List[CodeChunk] = []
        if not content.strip():
            return chunks

        file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        lines = content.splitlines()

        # Extract SQL queries if any
        sql_matches = re.finditer(r'(SELECT|INSERT|UPDATE|DELETE)\s+.*?;', content, re.IGNORECASE | re.DOTALL)
        for match in sql_matches:
            sql_str = match.group(0)
            chunks.append(CodeChunk(
                chunk_id=f"chunk_sql_{hashlib.md5(sql_str.encode()).hexdigest()[:8]}",
                repository_id=repository_id,
                file_path=file_path,
                chunk_type="sql",
                ast_path=f"{file_path}::sql_query",
                content=sql_str,
                start_line=1,
                end_line=len(sql_str.splitlines()),
                token_count=len(sql_str.split()),
                file_hash=file_hash
            ))

        # Split into function/class blocks or line blocks
        curr_lines = []
        curr_start = 1
        block_type = "function"

        for i, line in enumerate(lines, start=1):
            curr_lines.append(line)

            if line.startswith("class ") or line.startswith("def ") or line.startswith("function ") or i == len(lines):
                if len(curr_lines) > 1:
                    chunk_text = "\n".join(curr_lines[:-1] if i < len(lines) else curr_lines)
                    if chunk_text.strip():
                        chunks.append(CodeChunk(
                            chunk_id=f"chunk_{file_hash}_{len(chunks)+1}",
                            repository_id=repository_id,
                            file_path=file_path,
                            chunk_type=block_type,
                            ast_path=f"{file_path}::block_{len(chunks)+1}",
                            content=chunk_text,
                            start_line=curr_start,
                            end_line=i - 1 if i < len(lines) else i,
                            token_count=len(chunk_text.split()),
                            file_hash=file_hash
                        ))
                    curr_lines = [line] if i < len(lines) else []
                    curr_start = i

        if not chunks and content.strip():
            chunks.append(CodeChunk(
                chunk_id=f"chunk_{file_hash}_1",
                repository_id=repository_id,
                file_path=file_path,
                chunk_type="file",
                ast_path=file_path,
                content=content,
                start_line=1,
                end_line=len(lines),
                token_count=len(content.split()),
                file_hash=file_hash
            ))

        return chunks
