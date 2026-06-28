from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from .base import StorageService


class S3StorageService(StorageService):
    """
    AWS S3 implementation of StorageService.

    DESIGN NOTES:
    - storage_key == S3 object key (not a URL)
    - no local filesystem dependency
    - safe for ECS / EC2 / Lambda
    - supports IAM roles (recommended in production)
    """

    def __init__(
        self,
        bucket_name: str,
        region: str,
        # access_key: str | None = None,
        # secret_key: str | None = None,
    ):
        self.bucket_name = bucket_name

# When you deploy on EC2, ECS, or EKS, do not pass access_key and secret_key. 
# Attach an IAM Role to the compute instance instead.
        self.client = boto3.client(
            "s3",
            region_name=region,
            # aws_access_key_id=access_key,
            # aws_secret_access_key=secret_key,
        )
# This is sync I/O inside async methods.

# For MVP it's fine.

# For production scaling, later you should upgrade to:

# aioboto3 OR
# run_in_threadpool wrapper

# Example improvement:

# from starlette.concurrency import run_in_threadpool

# await run_in_threadpool(
#     self.client.upload_fileobj,
#     BytesIO(content),
#     self.bucket_name,
#     key,
# )
    # -------------------------------------------------
    # CORE API (your abstraction)
    # -------------------------------------------------

    async def save(
        self,
        filename: str,
        content: bytes,
    ) -> str:
        """
        Save file to S3 and return storage key.
        """
        key = filename

        self.client.upload_fileobj(
            Fileobj=BytesIO(content),
            Bucket=self.bucket_name,
            Key=key,
        )

        return key

    async def upload(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> str:
        """
        Alias of save() for semantic clarity.
        """
        return await self.save(filename, content)

    async def read(
        self,
        path: str,
    ) -> bytes:
        """
        Download file bytes from S3.
        """
        try:
            obj = self.client.get_object(
                Bucket=self.bucket_name,
                Key=path,
            )
            return obj["Body"].read()

        except ClientError as exc:
            raise FileNotFoundError(f"S3 object not found: {path}") from exc

    async def download(
        self,
        storage_key: str,
    ) -> bytes:
        """
        Alias of read().
        """
        return await self.read(storage_key)

    async def delete(
        self,
        storage_key: str,
    ) -> None:
        """
        Delete object from S3.
        """
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=storage_key,
        )

    async def exists(
        self,
        storage_key: str,
    ) -> bool:
        """
        Check if object exists in S3.
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )
            return True

        except ClientError as exc:
            if exc.response["Error"]["Code"] == "404":
                return False
            raise