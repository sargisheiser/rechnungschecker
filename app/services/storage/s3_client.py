"""AWS S3 storage client with async support."""

import fnmatch
import logging

import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3StorageClient:
    """Async client for AWS S3 operations."""

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str = "eu-central-1",
    ):
        """Initialize S3 client with credentials.

        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region (default: eu-central-1)
        """
        self.session = aioboto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )
        self.region = region

    async def test_connection(self, bucket_name: str) -> bool:
        """Test if credentials work and bucket is accessible.

        Args:
            bucket_name: Name of the S3 bucket to test

        Returns:
            True if connection successful

        Raises:
            ClientError: If bucket doesn't exist or access denied
            NoCredentialsError: If credentials are invalid
        """
        try:
            async with self.session.client("s3") as s3:
                await s3.head_bucket(Bucket=bucket_name)
                return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise ValueError(f"Bucket '{bucket_name}' does not exist")
            elif error_code == "403":
                raise PermissionError(f"Access denied to bucket '{bucket_name}'")
            raise
        except NoCredentialsError:
            raise ValueError("Invalid AWS credentials")

    async def list_files(
        self,
        bucket: str,
        prefix: str = "",
        pattern: str = "*.xml",
    ) -> list[dict]:
        """List files matching pattern in bucket/prefix.

        Args:
            bucket: S3 bucket name
            prefix: Key prefix to filter by (e.g., "invoices/pending/")
            pattern: Glob pattern to match filenames (e.g., "*.xml")

        Returns:
            List of dicts with keys: key, name, size, last_modified
        """
        files = []
        try:
            async with self.session.client("s3") as s3:
                paginator = s3.get_paginator("list_objects_v2")
                async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    for obj in page.get("Contents", []):
                        key = obj["Key"]
                        # Skip "directories" (keys ending with /)
                        if key.endswith("/"):
                            continue
                        file_name = key.rsplit("/", 1)[-1]
                        if fnmatch.fnmatch(file_name.lower(), pattern.lower()):
                            files.append(
                                {
                                    "key": key,
                                    "name": file_name,
                                    "size": obj["Size"],
                                    "last_modified": obj["LastModified"],
                                }
                            )
        except ClientError as e:
            logger.error(f"Failed to list files in s3://{bucket}/{prefix}: {e}")
            raise

        logger.info(
            f"Found {len(files)} files matching '{pattern}' in s3://{bucket}/{prefix}"
        )
        return files

    async def download_file(self, bucket: str, key: str) -> bytes:
        """Download file content from S3.

        Args:
            bucket: S3 bucket name
            key: Full S3 key (path) to the file

        Returns:
            File content as bytes
        """
        try:
            async with self.session.client("s3") as s3:
                response = await s3.get_object(Bucket=bucket, Key=key)
                content = await response["Body"].read()
                logger.debug(f"Downloaded {len(content)} bytes from s3://{bucket}/{key}")
                return content
        except ClientError as e:
            logger.error(f"Failed to download s3://{bucket}/{key}: {e}")
            raise

    async def delete_file(self, bucket: str, key: str) -> None:
        """Delete a file from S3.

        Args:
            bucket: S3 bucket name
            key: Full S3 key (path) to the file
        """
        try:
            async with self.session.client("s3") as s3:
                await s3.delete_object(Bucket=bucket, Key=key)
                logger.info(f"Deleted s3://{bucket}/{key}")
        except ClientError as e:
            logger.error(f"Failed to delete s3://{bucket}/{key}: {e}")
            raise

    async def move_file(self, bucket: str, source_key: str, dest_key: str) -> None:
        """Move file to new location within same bucket.

        Args:
            bucket: S3 bucket name
            source_key: Current S3 key of the file
            dest_key: Destination S3 key
        """
        try:
            async with self.session.client("s3") as s3:
                # Copy to new location
                await s3.copy_object(
                    Bucket=bucket,
                    CopySource={"Bucket": bucket, "Key": source_key},
                    Key=dest_key,
                )
                # Delete original
                await s3.delete_object(Bucket=bucket, Key=source_key)
                logger.info(f"Moved s3://{bucket}/{source_key} -> s3://{bucket}/{dest_key}")
        except ClientError as e:
            logger.error(
                f"Failed to move s3://{bucket}/{source_key} -> {dest_key}: {e}"
            )
            raise

    async def upload_file(
        self,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Upload file content to S3.

        Args:
            bucket: S3 bucket name
            key: Destination S3 key (path)
            content: File content as bytes
            content_type: MIME type of the file
        """
        try:
            async with self.session.client("s3") as s3:
                await s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=content,
                    ContentType=content_type,
                )
                logger.info(f"Uploaded {len(content)} bytes to s3://{bucket}/{key}")
        except ClientError as e:
            logger.error(f"Failed to upload to s3://{bucket}/{key}: {e}")
            raise
