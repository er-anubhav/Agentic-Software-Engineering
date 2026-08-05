"""
src.models.dag — Layer 1: Directed Acyclic Graph (DAG) Domain Models & Data Transfer Objects.
"""
from typing import List, Dict, Any, Set, Optional
from pydantic import BaseModel, Field


class DAGNode(BaseModel):
    id: str
    title: str = ""
    description: str = ""
    objective: str = ""
    owner_agent: str = "CodeGenerationAgent"
    agent: str = "CodeGenerationAgent"  # Backward compatibility alias for owner_agent
    priority: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
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
    status: str = Field(default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, FAILED, ABORTED
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
    dag_id: str = "dag_execution"
    nodes: Dict[str, DAGNode] = Field(default_factory=dict)

    def add_node(self, node: DAGNode) -> None:
        self.nodes[node.id] = node

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
