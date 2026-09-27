import os
import boto3
from langchain.tools import tool


@tool
def read_env_secret(key: str) -> str:
    """Read a secret from the environment."""
    return os.environ.get(key, "")


@tool
def upload_to_s3(bucket: str, key: str, body: str) -> bool:
    """Upload a file to an S3 bucket."""
    client = boto3.client("s3")
    client.put_object(Bucket=bucket, Key=key, Body=body)
    return True