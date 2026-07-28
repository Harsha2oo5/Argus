import logging
from typing import Dict, List, Set
from pydantic import BaseModel, Field

logger = logging.getLogger("backend.analysis.repo_graph")


class SymbolNode(BaseModel):
    """Represent an individual code symbol entity (class, function, variable)."""
    name: str
    symbol_type: str  # function, class, variable
    file_path: str
    line_number: int
    dependencies: List[str] = Field(default_factory=list)


class RepositoryKnowledgeGraph:
    """Graph structure mapping code structure hierarchies, import calls, and dependencies."""

    def __init__(self):
        self.symbols: Dict[str, SymbolNode] = {}
        # Mapping: caller_symbol_name -> Set[callee_symbol_name]
        self.call_graph: Dict[str, Set[str]] = {}
        # Mapping: file_path -> Set[import_path]
        self.dependencies: Dict[str, Set[str]] = {}

    def register_symbol(self, symbol: SymbolNode):
        self.symbols[symbol.name] = symbol
        logger.debug(f"Registered repository symbol: {symbol.symbol_type} '{symbol.name}'")

    def add_call(self, caller: str, callee: str):
        if caller not in self.call_graph:
            self.call_graph[caller] = set()
        self.call_graph[caller].add(callee)
        logger.debug(f"Call-graph edge added: {caller}() -> {callee}()")

    def add_dependency(self, file_path: str, dependency_path: str):
        if file_path not in self.dependencies:
            self.dependencies[file_path] = set()
        self.dependencies[file_path].add(dependency_path)
        logger.debug(f"Dependency edge added: '{file_path}' depends on '{dependency_path}'")

    def get_callers(self, callee: str) -> List[str]:
        callers = []
        for caller, callees in self.call_graph.items():
            if callee in callees:
                callers.append(caller)
        return callers

    def get_dependencies(self, file_path: str) -> List[str]:
        return list(self.dependencies.get(file_path, set()))
