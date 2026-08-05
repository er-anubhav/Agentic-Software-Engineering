import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from src.application.orchestration.dag_compiler import DAGCompiler, DAGNode
from src.infrastructure.sandboxes.runtime.scheduler import DistributedScheduler


def run_high_concurrency_stress_test(num_workflows: int = 50):
    print("\n=================================================")
    print(f"    HIGH-CONCURRENCY STRESS TEST ({num_workflows} DAGs)   ")
    print("=================================================\n")

    test_dir = f"/tmp/stress_test_{int(time.time())}"
    queue_dir = os.path.join(test_dir, "queues")
    chk_dir = os.path.join(test_dir, "checkpoints")
    os.makedirs(queue_dir, exist_ok=True)
    os.makedirs(chk_dir, exist_ok=True)

    compiler = DAGCompiler()
    n1 = DAGNode(id="step_db", title="Database", owner_agent="DatabaseAgent", dependencies=[])
    n2 = DAGNode(id="step_api", title="API Routes", owner_agent="APIAgent", dependencies=["step_db"])
    dag_template = compiler.compile([n1, n2])

    scheduler = DistributedScheduler(queue_dir=queue_dir, checkpoint_dir=chk_dir, max_workers=10)

    start_time = time.time()

    def run_dag_worker(idx: int):
        wf_id = f"wf_stress_{idx}"
        return scheduler.execute_dag(wf_id, dag_template, {"requirement": f"Stress Goal {idx}"})

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(run_dag_worker, i) for i in range(num_workflows)]
        results = [f.result() for f in futures]

    total_duration = time.time() - start_time
    passed_count = sum(1 for r in results if r["status"] == "COMPLETED")
    throughput = num_workflows / total_duration

    print(f"Results Summary:")
    print(f"  - Total Workflows Executed : {num_workflows}")
    print(f"  - Successful Completions   : {passed_count}/{num_workflows} ({passed_count/num_workflows*100:.1f}%)")
    print(f"  - Total Wall-Clock Time    : {total_duration:.2f} seconds")
    print(f"  - System Throughput        : {throughput:.2f} DAGs/sec\n")

    if os.path.exists(test_dir):
        shutil.rmtree(test_dir, ignore_errors=True)

    return passed_count == num_workflows


if __name__ == "__main__":
    run_high_concurrency_stress_test(50)
