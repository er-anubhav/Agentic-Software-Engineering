import os
import unittest

from src.interfaces.platform.auth.oidc import AuthProvider, UserIdentity
from src.interfaces.platform.security.rbac import RBACEngine, Role, Permission
from src.interfaces.platform.tenant.tenant_manager import TenantManager, Tenant, TenantQuota
from src.infrastructure.storage.persistence.postgres_store import PostgresStore, JobRecord
from src.infrastructure.storage.infra.redis_client import RedisRuntime
from src.infrastructure.storage.infra.secrets_manager import SecretsManager
from src.infrastructure.storage.infra.object_storage import ObjectStorage
from src.infrastructure.storage.infra.disaster_recovery import DisasterRecoveryEngine


class TestEnterprisePlatform(unittest.TestCase):

    def setUp(self):
        self.auth_provider = AuthProvider()
        self.rbac = RBACEngine()
        self.tenant_mgr = TenantManager()
        self.postgres_store = PostgresStore()
        self.redis_runtime = RedisRuntime()
        self.secrets_mgr = SecretsManager()
        self.object_storage = ObjectStorage()
        self.dr_engine = DisasterRecoveryEngine()

    def test_oidc_auth(self):
        identity = self.auth_provider.authenticate_oidc(id_token="token_sample", provider="google")
        self.assertTrue(identity.is_authenticated)
        self.assertEqual(identity.provider, "google")

        # Test API Key registration & auth
        api_identity = UserIdentity(user_id="u123", email="user@co.org", role="ADMIN")
        self.auth_provider.register_api_key("sk_live_123456", api_identity)

        authenticated_user = self.auth_provider.authenticate_api_key("sk_live_123456")
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user.user_id, "u123")

    def test_rbac_enforcement(self):
        # Admin has all permissions
        self.assertTrue(self.rbac.has_permission("ADMIN", Permission.DEPLOY_ADMIN))
        self.assertTrue(self.rbac.has_permission("ADMIN", Permission.REPO_WRITE))

        # Reviewer cannot write code or deploy
        self.assertFalse(self.rbac.has_permission("REVIEWER", Permission.REPO_WRITE))
        self.assertFalse(self.rbac.has_permission("REVIEWER", Permission.DEPLOY_ADMIN))
        self.assertTrue(self.rbac.has_permission("REVIEWER", Permission.REPO_READ))

    def test_tenant_isolation_and_quotas(self):
        tenant_a = Tenant(tenant_id="tenant_a", org_name="Org A")
        self.tenant_mgr.register_tenant(tenant_a)

        key_a = self.tenant_mgr.get_isolated_key("tenant_a", "qdrant/collection_1")
        key_b = self.tenant_mgr.get_isolated_key("tenant_b", "qdrant/collection_1")
        self.assertNotEqual(key_a, key_b)

        # Quota checking
        self.assertTrue(self.tenant_mgr.check_quota("tenant_a", estimated_cost_usd=1.0))
        self.tenant_mgr.record_usage("tenant_a", cost_usd=499.5)
        self.assertFalse(self.tenant_mgr.check_quota("tenant_a", estimated_cost_usd=10.0))

    def test_postgresql_persistence(self):
        job = JobRecord(job_id="job_99", tenant_id="tenant_a", payload={"dag": "test"})
        self.postgres_store.save_job(job)

        retrieved = self.postgres_store.get_job("job_99")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.tenant_id, "tenant_a")

        self.postgres_store.save_checkpoint("chk_1", {"step": 2})
        chk = self.postgres_store.get_checkpoint("chk_1")
        self.assertEqual(chk["step"], 2)

    def test_redis_runtime_queues_and_locks(self):
        self.redis_runtime.push_queue("jobs_queued", "job_data_payload")
        item = self.redis_runtime.pop_queue("jobs_queued")
        self.assertEqual(item, "job_data_payload")

        locked = self.redis_runtime.acquire_lock("workflow_lock_1")
        self.assertTrue(locked)
        locked_again = self.redis_runtime.acquire_lock("workflow_lock_1")
        self.assertFalse(locked_again)

    def test_secret_retrieval(self):
        secret = self.secrets_mgr.get_secret("OPENAI_API_KEY")
        self.assertIsNotNone(secret)
        self.assertIn("sk-proj", secret)

    def test_object_storage(self):
        uri = self.object_storage.upload_object("logs/run1.log", b"log contents")
        self.assertTrue(uri.startswith("s3://"))
        data = self.object_storage.download_object("logs/run1.log")
        self.assertEqual(data, b"log contents")

    def test_disaster_recovery_backup_and_restore(self):
        snapshot = self.dr_engine.create_backup("tenant_a")
        self.assertTrue(snapshot.snapshot_id.startswith("backup_tenant_a"))

        restored = self.dr_engine.restore_backup(snapshot.snapshot_id)
        self.assertTrue(restored)

    def test_k8s_deployment_manifest_exists(self):
        manifest_path = os.path.join("src", "interfaces", "platform", "deployment", "manifests", "k8s_deployment.yaml")
        if not os.path.exists(manifest_path):
            manifest_path = os.path.join("src", "platform", "deployment", "manifests", "k8s_deployment.yaml")
        self.assertTrue(os.path.exists(manifest_path))


if __name__ == "__main__":
    unittest.main()
