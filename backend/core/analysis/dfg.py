import re
from typing import Dict, List, Set
from pydantic import BaseModel, Field


class DataDependency(BaseModel):
    """Represent data propagation link between two variables or constants."""
    source_var: str
    target_var: str
    line_number: int


class DFGGraph(BaseModel):
    """Represent the complete data dependency graph."""
    dependencies: List[DataDependency] = Field(default_factory=list)


class DFGConstructor:
    """Traverses code strings to compile data flow dependencies."""

    def construct(self, lines: List[str]) -> DFGGraph:
        dfg = DFGGraph()
        
        # Track active definitions
        # Mapping: variable_name -> last_line_assigned
        active_defs: Dict[str, int] = {}

        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            if not stripped:
                continue

            # Check for assignments: e.g. x = y + z;
            m = re.match(r'^\b(\w+)\b\s*=\s*(.+);', stripped)
            if m:
                target_var = m.group(1)
                source_expr = m.group(2)

                # Find source variables referenced in the assignment RHS
                sources = re.findall(r'\b(\w+)\b', source_expr)
                for src in sources:
                    # Ignore numeric literals
                    if not src.isdigit() and src not in ["true", "false"]:
                        dfg.dependencies.append(
                            DataDependency(
                                source_var=src,
                                target_var=target_var,
                                line_number=line_num
                            )
                        )
                
                # Update definition line
                active_defs[target_var] = line_num

        return dfg
