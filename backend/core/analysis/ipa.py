import re
import logging
from typing import Dict, List, Set
from pydantic import BaseModel, Field

logger = logging.getLogger("backend.analysis.ipa")


class CallEdge(BaseModel):
    """Represent an interprocedural call link between caller and callee."""
    caller: str
    callee: str
    line_number: int


class InterproceduralCallGraph(BaseModel):
    """Call graph trace registry mapping caller linkages."""
    edges: List[CallEdge] = Field(default_factory=list)


class IPATracer:
    """Traces calls across procedures and modules."""

    def trace_calls(self, code: str) -> InterproceduralCallGraph:
        graph = InterproceduralCallGraph()
        lines = code.split("\n")

        current_func = "global"

        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            if not stripped:
                continue

            # Detect function declarations: e.g. void myFunc() {
            func_decl = re.match(r'^\w+\s+(\w+)\s*\(.*\)\s*\{', stripped)
            if func_decl:
                current_func = func_decl.group(1)
                continue

            # Detect function calls inside body: e.g. delay(10);
            calls = re.findall(r'\b(\w+)\s*\(', stripped)
            for callee in calls:
                # Ignore control keywords
                if callee not in ["if", "while", "for", "switch", "if", "return", "sizeof"]:
                    graph.edges.append(
                        CallEdge(
                            caller=current_func,
                            callee=callee,
                            line_number=line_num
                        )
                    )

            if stripped == "}":
                current_func = "global"

        return graph
