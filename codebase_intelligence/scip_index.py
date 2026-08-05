import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SCIPSymbol(BaseModel):
    symbol_id: str
    repository: str = "default"
    file_path: str
    range_lines: List[int] = Field(default_factory=lambda: [1, 1])  # [start_line, end_line]
    kind: str = "function"
    language: str = "python"
    visibility: str = "public"
    definition_snippet: str = ""
    references: List[str] = Field(default_factory=list)  # List of file paths referencing symbol
    callers: List[str] = Field(default_factory=list)     # List of symbol IDs calling this symbol
    callees: List[str] = Field(default_factory=list)     # List of symbol IDs called by this symbol


class SCIPDatabase(BaseModel):
    """
    Sourcegraph SCIP-style Code Intelligence Symbol Database.
    """
    repository_id: str = "default"
    symbols: Dict[str, SCIPSymbol] = Field(default_factory=dict)

    def register_symbol(self, symbol: SCIPSymbol) -> None:
        self.symbols[symbol.symbol_id] = symbol

    def add_reference(self, symbol_id: str, referencing_file: str) -> None:
        if symbol_id in self.symbols:
            if referencing_file not in self.symbols[symbol_id].references:
                self.symbols[symbol_id].references.append(referencing_file)

    def add_call_edge(self, caller_id: str, callee_id: str) -> None:
        if caller_id in self.symbols and callee_id in self.symbols:
            if callee_id not in self.symbols[caller_id].callees:
                self.symbols[caller_id].callees.append(callee_id)
            if caller_id not in self.symbols[callee_id].callers:
                self.symbols[callee_id].callers.append(caller_id)

    def get_symbol(self, symbol_id: str) -> Optional[SCIPSymbol]:
        return self.symbols.get(symbol_id)

    def find_callers(self, symbol_id: str) -> List[str]:
        sym = self.get_symbol(symbol_id)
        return sym.callers if sym else []

    def find_callees(self, symbol_id: str) -> List[str]:
        sym = self.get_symbol(symbol_id)
        return sym.callees if sym else []
