"""
src.orchestration.dag_compiler — Layer 6: Dynamic Task DAG Compiler Engine.
"""
from typing import List, Dict, Any, Union
from src.domain.models.dag import DAGNode, TaskDAG


class DAGCompiler:
    """
    Production-grade Task DAG Compiler (RFC-001).
    Compiles raw planning tasks or DAG node dicts into a validated TaskDAG with
    topological sorting, parallel phase execution mapping, and cycle detection.
    """

    def compile(self, tasks: List[Union[str, DAGNode, Dict[str, Any]]], dag_id: str = "dag_execution") -> TaskDAG:
        dag = TaskDAG(dag_id=dag_id)
        raw_nodes: List[DAGNode] = []

        for i, t in enumerate(tasks, start=1):
            if isinstance(t, DAGNode):
                raw_nodes.append(t)
            elif isinstance(t, dict):
                node = DAGNode(
                    id=t.get("id", f"task_{i}"),
                    title=t.get("title", f"Task {i}"),
                    description=t.get("description", ""),
                    objective=t.get("objective", ""),
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

        # Register nodes to DAG
        for node in raw_nodes:
            dag.add_node(node)

        # Detect cycles and assign topological phases
        if dag.has_cycles():
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
