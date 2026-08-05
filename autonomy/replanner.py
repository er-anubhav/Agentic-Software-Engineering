from typing import List, Dict, Any, Optional
from orchestrator.dag_compiler import TaskDAG, DAGNode, DAGCompiler
from autonomy.observation_engine import Observation
from autonomy.progress_engine import ProgressReport


class DynamicReplanner:
    """
    Dynamic Replanner updating task DAG nodes dynamically without workflow restart.
    """

    def __init__(self):
        self.compiler = DAGCompiler()

    def replan(
        self,
        current_dag: TaskDAG,
        completed_nodes: List[str],
        observations: List[Observation],
        progress: ProgressReport
    ) -> TaskDAG:
        # Retain uncompleted nodes
        remaining_node_ids = set(progress.remaining_nodes)

        updated_nodes: List[DAGNode] = []
        for nid, node in current_dag.nodes.items():
            if nid in remaining_node_ids:
                # If stagnant, insert dynamic diagnostic/repair node
                if progress.is_stagnant:
                    node.priority = "HIGH"
                updated_nodes.append(node)

        # If no remaining nodes, append validation node
        if not updated_nodes:
            val_node = DAGNode(
                id="goal_final_validation",
                title="Final Goal Validation",
                owner_agent="ValidationAgent",
                dependencies=[]
            )
            updated_nodes.append(val_node)

        return self.compiler.compile(updated_nodes)
