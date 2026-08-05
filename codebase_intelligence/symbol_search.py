import re
from typing import List, Dict, Any, Optional
from codebase_intelligence.scip_index import SCIPDatabase, SCIPSymbol
from codebase_intelligence.polyglot_parser import ASTSymbol


class SymbolSearchEngine:
    """
    Symbol Search Engine providing code intelligence queries across indexed repositories.
    """

    def __init__(self, scip_db: SCIPDatabase):
        self.scip_db = scip_db

    def find_callers(self, symbol_name: str) -> List[SCIPSymbol]:
        results = []
        for sym in self.scip_db.symbols.values():
            if symbol_name.lower() in sym.symbol_id.lower() or symbol_name.lower() in sym.definition_snippet.lower():
                results.append(sym)
        return results

    def find_sql_queries(self) -> List[Dict[str, Any]]:
        sql_matches = []
        for sym in self.scip_db.symbols.values():
            if any(k in sym.definition_snippet.upper() for k in ("SELECT", "INSERT", "UPDATE", "DELETE", "JOIN")):
                sql_matches.append({
                    "symbol_id": sym.symbol_id,
                    "file_path": sym.file_path,
                    "snippet": sym.definition_snippet
                })
        return sql_matches

    def find_middleware(self) -> List[SCIPSymbol]:
        middleware = []
        for sym in self.scip_db.symbols.values():
            if "middleware" in sym.symbol_id.lower() or "auth" in sym.symbol_id.lower() or "jwt" in sym.symbol_id.lower():
                middleware.append(sym)
        return middleware

    def find_unused_methods(self) -> List[SCIPSymbol]:
        unused = []
        for sym in self.scip_db.symbols.values():
            if sym.kind in ("function", "method") and len(sym.callers) == 0 and not sym.symbol_id.startswith("test_"):
                unused.append(sym)
        return unused

    def find_dead_code(self) -> List[SCIPSymbol]:
        return self.find_unused_methods()

    def find_cyclic_imports(self) -> List[Dict[str, str]]:
        cycles = []
        for s1_id, s1 in self.scip_db.symbols.items():
            for s2_id in s1.callees:
                s2 = self.scip_db.get_symbol(s2_id)
                if s2 and s1_id in s2.callees:
                    cycles.append({"from": s1_id, "to": s2_id})
        return cycles

    def find_endpoints(self) -> List[SCIPSymbol]:
        endpoints = []
        for sym in self.scip_db.symbols.values():
            if any(kw in sym.definition_snippet.lower() for kw in ("@app.get", "@app.post", "router.", "endpoint", "/api/")):
                endpoints.append(sym)
        return endpoints
