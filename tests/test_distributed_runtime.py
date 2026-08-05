import os
import shutil
import unittest
from orchestrator.dag_compiler import DAGCompiler, DAGNode, TaskDAG
from runtime.job_queue import DurableJobQueue, Job, JobStatus
from runtime.event_bus import EventBus, Event, EventType
from runtime.checkpoint_manager import CheckpointManager, Checkpoint
from runtime.worker import Worker, WorkerRole, WorkerPool
from runtime.scheduler import DistributedScheduler


class TestDistributedRuntime(unittest.TestCase):

    def setUp(self):
        self.test_dir = "/tmp/test_distributed_runtime"
        self.queue_dir = os.path.join(self.test_dir, "queues")
        self.checkpoint_dir = os.path.join(self.test_dir, "checkpoints")
        os.makedirs(self.queue_dir, exist_ok=True)
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_durable_job_queue_and_dlq(self):
        queue = DurableJobQueue(storage_dir=self.queue_dir)
        job = Job(workflow_id="wf_01", node_id="node_db", role="DatabaseAgent", max_retries=2)

        queue.enqueue(job)
        dequeued = queue.dequeue("DatabaseAgent")
        self.assertIsNotNone(dequeued)
        self.assertEqual(dequeued.status, JobStatus.RUNNING)

        # First failure -> Retry
        j1 = queue.handle_failure(job.id, "Connection timeout")
        self.assertEqual(j1.retry_count, 1)

        # Dequeue for attempt 2
        dequeued2 = queue.dequeue("DatabaseAgent")
        self.assertIsNotNone(dequeued2)

        # Second failure -> Retry
        j2 = queue.handle_failure(job.id, "Connection timeout")
        self.assertEqual(j2.retry_count, 2)

        # Dequeue for attempt 3
        dequeued3 = queue.dequeue("DatabaseAgent")
        self.assertIsNotNone(dequeued3)

        # Third failure -> Exceeds max_retries -> DLQ
        j3 = queue.handle_failure(job.id, "Fatal connection refusal")
        self.assertEqual(j3.status, JobStatus.FAILED)
        self.assertTrue(os.path.exists(os.path.join(self.queue_dir, "dlq", f"{job.id}_dlq.json")))

    def test_event_bus_pub_sub(self):
        event_bus = EventBus.get_instance()
        received_events = []

        def listener(evt: Event):
            received_events.append(evt)

        event_bus.subscribe(EventType.JOB_QUEUED, listener)
        event_bus.publish(Event(event_type=EventType.JOB_QUEUED, workflow_id="wf_10", job_id="job_10"))

        self.assertGreater(len(received_events), 0)
        self.assertEqual(received_events[-1].workflow_id, "wf_10")

    def test_checkpoint_manager_atomic_save_and_restore(self):
        chk_mgr = CheckpointManager(storage_dir=self.checkpoint_dir)
        chk_mgr.save_checkpoint(
            workflow_id="wf_crash_test",
            completed_nodes=["step_db", "step_api"],
            state_snapshot={"user": "admin"}
        )

        restored = chk_mgr.load_checkpoint("wf_crash_test")
        self.assertIsNotNone(restored)
        self.assertEqual(len(restored.completed_nodes), 2)
        self.assertIn("step_db", restored.completed_nodes)
        self.assertEqual(restored.state_snapshot["user"], "admin")

    def test_worker_pool_concurrency(self):
        pool = WorkerPool(max_workers=2)
        job = Job(workflow_id="wf_pool", node_id="node_1")

        def mock_handler(j: Job):
            return {"result": "OK"}

        fut = pool.submit_job(job, mock_handler)
        res = fut.result(timeout=2.0)
        self.assertEqual(res["result"], "OK")
        pool.shutdown()

    def test_distributed_scheduler_parallel_dag_and_crash_recovery(self):
        compiler = DAGCompiler()
        n1 = DAGNode(id="step_db", title="Database", owner_agent="DatabaseAgent", dependencies=[])
        n2 = DAGNode(id="step_api", title="API Routes", owner_agent="APIAgent", dependencies=["step_db"])
        dag = compiler.compile([n1, n2])

        scheduler = DistributedScheduler(
            queue_dir=self.queue_dir,
            checkpoint_dir=self.checkpoint_dir,
            max_workers=2
        )

        # 1. Execute workflow up to step 1 checkpoint
        chk_mgr = CheckpointManager(storage_dir=self.checkpoint_dir)
        chk_mgr.save_checkpoint("wf_recovery", ["step_db"], {"requirement": "Build API"})

        # 2. Run scheduler — should skip step_db and resume step_api from checkpoint
        result = scheduler.execute_dag("wf_recovery", dag, {"requirement": "Build API"})

        self.assertEqual(result["status"], "COMPLETED")
        self.assertIn("step_db", result["completed_nodes"])
        self.assertIn("step_api", result["completed_nodes"])


if __name__ == "__main__":
    unittest.main()
