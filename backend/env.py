import os

from dotenv import load_dotenv

load_dotenv()


class AWSConfig:
    def __init__(self):
        self.access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_REGION")
        self.s3_bucket = os.getenv("AWS_S3_BUCKET")

# Can or can't be used so commented for now.
# class DatabricksConfig:
#     def __init__(self):
#         self.instance = os.getenv("DATABRICKS_INSTANCE")
#         self.access_token = os.getenv("DATABRICKS_ACCESS_TOKEN")
#         self.sql_warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")


class PostgresConfig:
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.database = os.getenv("POSTGRES_DB")

    @property
    def database_url(self):
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class AppConfig:
    def __init__(self):
        self.aws = AWSConfig()
        # self.databricks = DatabricksConfig()
        self.postgres = PostgresConfig()


config = AppConfig()
