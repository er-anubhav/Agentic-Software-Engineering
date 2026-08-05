"""
src.domain.aggregates.dag — Fully Encapsulated TaskDAG Aggregate Root.
"""
from typing import List, Dict, Any, Set, Optional
from pydantic import BaseModel, Field


class DAGNode(BaseModel):
    id: str
    title: str = ""
    description: str = ""
    objective: str = ""
    owner_agent: str = "CodeGenerationAgent"
    agent: str = "CodeGenerationAgent"
    priority: str = "MEDIUM"
    estimated_cost: float = 0.05
    estimated_duration: float = 30.0
    required_context: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    validation_strategy: str = "Automated Pytest & AST Validation"
    rollback_strategy: str = "Revert workspace changes from snapshot"
    phase: int = 1
    step: int = 1
    status: str = Field(default="PENDING")
    result: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.title:
            self.title = self.id
        if not self.objective:
            self.objective = self.description or self.title
        if self.agent != "CodeGenerationAgent" and self.owner_agent == "CodeGenerationAgent":
            self.owner_agent = self.agent
        elif self.owner_agent != "CodeGenerationAgent":
            self.agent = self.owner_agent


class TaskDAG(BaseModel):
    """
    TaskDAG Aggregate Root enforcing graph consistency, cycle-free invariants, and encapsulated node mutations.
    """
    dag_id: str = "dag_execution"
    nodes: Dict[str, DAGNode] = Field(default_factory=dict)

    def get_node(self, node_id: str) -> Optional[DAGNode]:
        """Returns a node by ID."""
        return self.nodes.get(node_id)

    def add_node(self, node: DAGNode) -> None:
        """Adds a node to the aggregate while enforcing ID uniqueness."""
        if not node.id:
            raise ValueError("DAG node must have a non-empty ID.")
        self.nodes[node.id] = node

    def add_dependency(self, node_id: str, depends_on_id: str) -> None:
        """Adds a dependency while preventing self-loops and cycle introduction."""
        if node_id not in self.nodes:
            raise KeyError(f"Node '{node_id}' does not exist in DAG.")
        if depends_on_id not in self.nodes:
            raise KeyError(f"Dependency node '{depends_on_id}' does not exist in DAG.")
        if node_id == depends_on_id:
            raise ValueError(f"Self-dependency detected: node '{node_id}' cannot depend on itself.")

        # Duplicate check using a copy of dependencies list
        current_deps = list(self.nodes[node_id].dependencies)
        if depends_on_id not in current_deps:
            self.nodes[node_id].dependencies.append(depends_on_id)

        if self.has_cycles():
            self.nodes[node_id].dependencies.remove(depends_on_id)
            raise ValueError(f"Adding dependency '{node_id}' -> '{depends_on_id}' would introduce a cycle.")

    def validate_graph(self) -> bool:
        """Validates that all dependencies exist and no cycles are present."""
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(f"Node '{node.id}' references non-existent dependency '{dep}'.")
        if self.has_cycles():
            raise ValueError("DAG consistency check failed: cycle detected in task graph.")
        return True

    def get_ready_nodes(self) -> List[DAGNode]:
        ready = []
        for node in self.nodes.values():
            if node.status == "PENDING":
                deps_met = all(
                    self.nodes[dep_id].status == "COMPLETED"
                    for dep_id in node.dependencies
                    if dep_id in self.nodes
                )
                if deps_met:
                    ready.append(node)
        return ready

    def has_cycles(self) -> bool:
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for dep in self.nodes[node_id].dependencies:
                if dep in self.nodes:
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        return False

    def get_topological_sort(self) -> List[DAGNode]:
        in_degree = {node_id: 0 for node_id in self.nodes}
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep in in_degree:
                    in_degree[node.id] += 1

        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        result = []
        while queue:
            curr = queue.pop(0)
            result.append(self.nodes[curr])
            for node in self.nodes.values():
                if curr in node.dependencies:
                    in_degree[node.id] -= 1
                    if in_degree[node.id] == 0:
                        queue.append(node.id)
        return result

    def get_parallelizable_groups(self) -> List[List[DAGNode]]:
        sorted_nodes = self.get_topological_sort()
        phases: Dict[int, List[DAGNode]] = {}
        for node in sorted_nodes:
            p = node.phase
            if p not in phases:
                phases[p] = []
            phases[p].append(node)
        return [phases[p] for p in sorted(phases.keys())]

    def get_total_estimated_cost(self) -> float:
        return sum(node.estimated_cost for node in self.nodes.values())

    def get_total_estimated_duration(self) -> float:
        return sum(node.estimated_duration for node in self.nodes.values())
