from typing import Dict, Any, Optional


class ObjectStorage:
    """
    Unified Object Storage Abstraction for S3, GCS, Azure Blob, and MinIO.
    Used for storing Repositories, Benchmarks, Checkpoints, Artifacts, Logs, and Trace Exports.
    """

    def __init__(self, provider: str = "s3", bucket_name: str = "enterprise-agentic-artifacts"):
        self.provider = provider
        self.bucket_name = bucket_name
        self.storage: Dict[str, bytes] = {}

    def upload_object(self, key: str, data: bytes) -> str:
        self.storage[key] = data
        return f"{self.provider}://{self.bucket_name}/{key}"

    def download_object(self, key: str) -> Optional[bytes]:
        return self.storage.get(key)

    def delete_object(self, key: str) -> bool:
        if key in self.storage:
            del self.storage[key]
            return True
        return False
