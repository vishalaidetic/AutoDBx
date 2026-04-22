import io
import logging
import os
from typing import Any, Dict, Optional

import boto3
import pandas as pd

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSFileHandler:
    def __init__(
        self, bucket_name: Optional[str] = None, region_name: Optional[str] = None
    ):
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")

        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        self.s3_client = boto3.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def upload_file(self, file_content: bytes, s3_key: str) -> str:
        """Upload a file to an S3 bucket."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=s3_key, Body=file_content
            )
            logger.info(f"Uploaded file to s3://{self.bucket_name}/{s3_key}")
            return s3_key
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise e

    def download_and_read_file(self, s3_key: str) -> Dict[str, Any]:
        """Download a file from an S3 bucket and return data as a dictionary."""
        try:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            file_content = obj["Body"].read()

            # Determine file type by extension
            if s3_key.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_content))
            elif s3_key.endswith((".xls", ".xlsx")):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                # Fallback to CSV or try to guess
                df = pd.read_csv(io.BytesIO(file_content))

            # Convert NaN to None for JSON compatibility
            df = df.where(pd.notnull(df), None)

            logger.info(f"Downloaded and read {s3_key} from S3")
            return {
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records"),
            }
        except Exception as e:
            logger.error(f"Failed to download/read {s3_key} from S3: {e}")
            raise e

    def get_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed URL for an S3 object."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            return None
