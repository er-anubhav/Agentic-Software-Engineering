from src.domain.models.state import EngineeringState
from src.application.orchestration.dag_compiler import DAGCompiler


class ExecutionPlannerAgent:
    """
    Production-grade Task DAG Execution Orchestrator (RFC-001).
    Compiles dynamically inferred planning nodes into an optimized execution DAG,
    calculates topological order, parallelizable work phases, total cost, and critical path duration.
    """

    def __init__(self):
        self.compiler = DAGCompiler()

    def execute(self, state: EngineeringState):
        nodes_to_compile = getattr(state, "planner_nodes", None) or state.tasks
        dag = self.compiler.compile(nodes_to_compile)

        sorted_nodes = dag.get_topological_sort()
        parallel_groups = dag.get_parallelizable_groups()
        total_cost = dag.get_total_estimated_cost()
        total_duration = dag.get_total_estimated_duration()

        state.execution_plan = {
            "dag_id": dag.dag_id,
            "total_estimated_cost_usd": total_cost,
            "total_estimated_duration_seconds": total_duration,
            "execution_phases_count": len(parallel_groups),
            "execution_plan": [
                {
                    "id": node.id,
                    "title": node.title,
                    "step": node.step,
                    "phase": node.phase,
                    "agent": node.owner_agent,
                    "owner_agent": node.owner_agent,
                    "objective": node.objective,
                    "priority": node.priority,
                    "estimated_cost": node.estimated_cost,
                    "estimated_duration": node.estimated_duration,
                    "required_context": node.required_context,
                    "required_tools": node.required_tools,
                    "dependencies": node.dependencies,
                    "outputs": node.outputs,
                    "validation_strategy": node.validation_strategy,
                    "rollback_strategy": node.rollback_strategy
                }
                for node in sorted_nodes
            ],
            "parallel_execution_phases": [
                [node.id for node in phase_nodes]
                for phase_nodes in parallel_groups
            ]
        }

        print(f"\n===== Execution Planner Agent =====")
        print(f"Compiled Task DAG ID             : {dag.dag_id}")
        print(f"Total Execution Nodes            : {len(sorted_nodes)}")
        print(f"Parallel Execution Phases        : {len(parallel_groups)}")
        print(f"Total Estimated Cost (USD)       : ${total_cost:.4f}")
        print(f"Total Estimated Duration (sec)   : {total_duration:.1f}s")
        for idx, phase in enumerate(parallel_groups, start=1):
            print(f"  Phase {idx} Concurrent Nodes: {[n.id for n in phase]}")

        return state