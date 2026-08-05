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
        visited = set()
        rec_stack = set()

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
        """
        Groups nodes into execution phases that can be run concurrently by worker agents.
        """
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


class DAGCompiler:
    """
    Dynamic DAG Compiler that transforms inferred task specifications or rich DAGNode
    objects into an optimized, topological TaskDAG without hardcoded tasks.
    """

    def compile(self, tasks: Any) -> TaskDAG:
        dag = TaskDAG(dag_id="dag_execution")

        if not tasks:
            return dag

        raw_nodes: List[DAGNode] = []

        # 1. Standardize input tasks into DAGNode instances
        for i, t in enumerate(tasks, start=1):
            if isinstance(t, DAGNode):
                raw_nodes.append(t)
            elif isinstance(t, dict):
                node_id = t.get("id") or f"task_{i}"
                node = DAGNode(
                    id=node_id,
                    title=t.get("title", f"Task {i}"),
                    description=t.get("description", str(t)),
                    objective=t.get("objective", t.get("description", f"Objective for {node_id}")),
                    owner_agent=t.get("owner_agent", t.get("agent", "CodeGenerationAgent")),
                    agent=t.get("agent", t.get("owner_agent", "CodeGenerationAgent")),
                    priority=t.get("priority", "MEDIUM"),
                    estimated_cost=float(t.get("estimated_cost", 0.05)),
                    estimated_duration=float(t.get("estimated_duration", 30.0)),
                    required_context=t.get("required_context", []),
                    required_tools=t.get("required_tools", []),
                    dependencies=t.get("dependencies", []),
                    outputs=t.get("outputs", []),
                    validation_strategy=t.get("validation_strategy", "Automated Pytest & AST Validation"),
                    rollback_strategy=t.get("rollback_strategy", "Revert workspace changes from snapshot"),
                    phase=int(t.get("phase", 1)),
                    step=i
                )
                raw_nodes.append(node)
            elif isinstance(t, str):
                # Dynamically infer agent owner and dependencies based on task title
                agent_name = "CodeGenerationAgent"
                deps = []
                lower_t = t.lower()

                if "db" in lower_t or "database" in lower_t or "schema" in lower_t:
                    agent_name = "DatabaseAgent"
                elif "api" in lower_t or "route" in lower_t or "endpoint" in lower_t:
                    agent_name = "APIAgent"
                    deps = [n.id for n in raw_nodes if n.owner_agent == "DatabaseAgent"]
                elif "test" in lower_t or "pytest" in lower_t:
                    agent_name = "TestGenerationAgent"
                    deps = [n.id for n in raw_nodes if n.owner_agent in ("DatabaseAgent", "APIAgent", "CodeGenerationAgent")]
                elif "validat" in lower_t:
                    agent_name = "ValidationAgent"
                    deps = [n.id for n in raw_nodes if n.id != f"task_{i}"]

                node = DAGNode(
                    id=f"task_{i}",
                    title=t,
                    description=t,
                    objective=f"Execute {t}",
                    owner_agent=agent_name,
                    agent=agent_name,
                    dependencies=deps,
                    step=i
                )
                raw_nodes.append(node)

        # 2. Register nodes to DAG
        for node in raw_nodes:
            dag.add_node(node)

        # 3. Detect cycles and assign topological phases
        if dag.has_cycles():
            # Break cycles by clearing problematic dependencies
            for node in dag.nodes.values():
                node.dependencies = [d for d in node.dependencies if d != node.id]

        topological_nodes = dag.get_topological_sort()
        depth_map: Dict[str, int] = {}

        for node in topological_nodes:
            if not node.dependencies:
                depth_map[node.id] = 1
            else:
                max_dep_depth = max([depth_map.get(d, 1) for d in node.dependencies], default=0)
                depth_map[node.id] = max_dep_depth + 1
            node.phase = depth_map[node.id]
            node.step = list(topological_nodes).index(node) + 1

        return dag
