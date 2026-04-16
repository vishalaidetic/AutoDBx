from datetime import datetime
from utility.catalog_utils import CatalogUtils
class Logger:
    def __init__(self, spark,catalog, schema, table):
        self.catalog = catalog
        self.schema = schema
        self.table = table
        self.spark = spark
        self.errors = {}
        
        # Ensure logging target exists
        CatalogUtils.ensure_catalog_and_schema(self.spark, self.catalog, self.schema)
        CatalogUtils.ensure_log_table(self.spark, self.catalog, self.schema, self.table)
    
    def fetch_error(self, table, error):
        self.errors[table] = error
    
    def return_error(self):
        return self.errors

    def log_load(self, source, source_table, target_table, load_type, status, error_msg=""):

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sanitized_error = error_msg.replace("'", "''")  # Escape single quotes

        self.spark.sql(f"""
            INSERT INTO {self.catalog}.{self.schema}.{self.table}
            VALUES (
                '{source}',
                '{source_table}',
                '{target_table}',
                '{load_type}',
                '{status}',
                '{sanitized_error}',
                TIMESTAMP('{timestamp}')
            )
        """)