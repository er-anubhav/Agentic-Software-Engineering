from models.state import EngineeringState
from orchestrator.dag_compiler import DAGCompiler


class ExecutionPlannerAgent:
    """
    Builds a dynamic Task DAG execution pipeline for engineering agents.
    """

    def __init__(self):
        self.compiler = DAGCompiler()

    def execute(self, state: EngineeringState):

        dag = self.compiler.compile(state.tasks)

        sorted_nodes = dag.get_topological_sort()

        state.execution_plan = {
            "dag_id": dag.dag_id,
            "execution_plan": [
                {
                    "id": node.id,
                    "step": node.step,
                    "agent": node.agent,
                    "objective": node.objective,
                    "dependencies": node.dependencies
                }
                for node in sorted_nodes
            ]
        }

        print(f"\n===== Execution Planner Agent =====")
        print(f"Compiled Task DAG with {len(sorted_nodes)} execution nodes.")

        return state