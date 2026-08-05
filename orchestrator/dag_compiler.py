from typing import List, Dict, Any, Set, Optional
from pydantic import BaseModel, Field


class DAGNode(BaseModel):
    id: str
    step: int
    agent: str
    objective: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = Field(default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    result: Optional[Dict[str, Any]] = None


class TaskDAG(BaseModel):
    dag_id: str = "dag_default"
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


class DAGCompiler:
    """
    Compiles software architecture design and tasks into a TaskDAG.
    """

    def compile(self, tasks: List[str]) -> TaskDAG:
        dag = TaskDAG(dag_id="dag_execution")

        db_node = DAGNode(
            id="step_db",
            step=1,
            agent="DatabaseAgent",
            objective="Generate database schema and ORM models",
            dependencies=[]
        )
        api_node = DAGNode(
            id="step_api",
            step=2,
            agent="APIAgent",
            objective="Generate OpenAPI specification and REST API routes",
            dependencies=[]
        )
        val_node = DAGNode(
            id="step_val_pre",
            step=3,
            agent="ValidationAgent",
            objective="Validate preliminary design artifacts",
            dependencies=["step_db", "step_api"]
        )
        human_node = DAGNode(
            id="step_approval",
            step=4,
            agent="HumanApprovalAgent",
            objective="Obtain human approval before code generation",
            dependencies=["step_val_pre"]
        )
        code_node = DAGNode(
            id="step_codegen",
            step=5,
            agent="CodeGenerationAgent",
            objective="Generate production-ready FastAPI source code",
            dependencies=["step_approval"]
        )
        test_node = DAGNode(
            id="step_testgen",
            step=6,
            agent="TestGenerationAgent",
            objective="Generate dynamic Pytest unit and integration test suite",
            dependencies=["step_codegen"]
        )
        val_post_node = DAGNode(
            id="step_val_post",
            step=7,
            agent="ValidationAgent",
            objective="Perform end-to-end sandbox verification of generated application",
            dependencies=["step_codegen", "step_testgen"]
        )
        summary_node = DAGNode(
            id="step_summary",
            step=8,
            agent="SummaryAgent",
            objective="Generate final engineering summary",
            dependencies=["step_val_post"]
        )

        for node in [db_node, api_node, val_node, human_node, code_node, test_node, val_post_node, summary_node]:
            dag.add_node(node)

        return dag
