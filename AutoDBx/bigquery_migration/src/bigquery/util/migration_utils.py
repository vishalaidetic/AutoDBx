from pyspark.sql.functions import col,concat_ws,max
from datetime import datetime
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, LongType
from utility.catalog_utils import CatalogUtils

class Migration:
    def __init__(self,spark, config_catalog, config_schema, config_table, project, parentProject, credentials_base64 ,src ,logger):
        self.spark = spark
        self.config_catalog = config_catalog
        self.config_schema = config_schema
        self.config_table= config_table
        self.src=src
        self.project=project
        self.parentProject = parentProject
        self.credentials_base64 = credentials_base64
        # self.jdbc_driver = jdbc_driver
        self.logger = logger

    def update_config_table(self,source_table_full, target_table_full,current_time): 
        self.spark.sql(f"""
            UPDATE {self.config_catalog}.{self.config_schema}.{self.config_table}
            SET last_load_time = TIMESTAMP('{current_time}')
            WHERE concat_ws('.', Source_Schema, Source_table) = '{source_table_full}'
            AND concat_ws('.',target_table_catalog ,Target_table_schema, Target_table_name) = '{target_table_full}'
        """)

        print(f"Updated config_table for {source_table_full} at {current_time}")
    
    def get_last_load_time(self,source_table_full, target_table_full):
        result = self.spark.table(f"{self.config_catalog}.{self.config_schema}.{self.config_table}") \
                    .filter(( concat_ws('.',col('source_schema'),col('source_table')) == source_table_full ) &
                            ( concat_ws('.',col('target_table_catalog'),col('target_table_schema'),col('target_table_name')) == target_table_full )) \
                    .select("last_load_time").collect()
        return result[0]["last_load_time"] if result else None
    
    def read_data(self, source_schema, source_table, query):
        # jdbc_url = f"jdbc:{self.src}://{self.project}:{self.parentProject}/{source_schema}"
        table = source_schema+"."+source_table
        return self.spark.read.format("bigquery") \
                    .option("project", self.project) \
                    .option("parentProject", self.parentProject) \
                    .option("table", table)\
                    .option("query", query)\
                    .option("inferschema", "true")\
                    .option("bigNumericDefaultPrecision", "38")\
                    .option("credentials", self.credentials_base64) \
                    .load()
    
    def migrate_full_data(self,source_schema, source_table, target_table_catalog, target_table_schema, target_table):
        try:
            
            source_table_full = f"{source_schema}.{source_table}"
            target_table_full = f"{target_table_catalog}.{target_table_schema}.{target_table}"

            print(f"Starting full load: {source_table_full} -> {target_table_full}")
            
            # Fixed: Use the actual source table instead of hardcoded query
            query = f"SELECT * FROM {source_table_full}"
            
            df = self.read_data(source_schema, source_table, query)
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            df.write.format("delta").mode("overwrite") \
            .saveAsTable(target_table_full)
            print(f"Full load successful: {source_table_full}")

            self.update_config_table(source_table_full, target_table_full,current_time)
            self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "full", "success")
        except Exception as e:
            print(f"Full load failed: {source_table_full}")
            print(f"Error: {str(e)}")
            self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "full", "failed", str(e))
            self.logger.fetch_error(target_table_full, str(e))

    def migrate_incremental_data(self,source_schema, source_table, target_table_catalog, target_table_schema, target_table,incremental_col_name,PK):
        try:
            source_table_full = f"{source_schema}.{source_table}"
            print(source_table_full)
            target_table_full = f"{target_table_catalog}.{target_table_schema}.{target_table}"
            print(target_table_full)

            last_load_time = self.get_last_load_time(source_table_full, target_table_full)
            
            # Fixed: Build the query properly and pass it to read_data
            if last_load_time is None:
                query = f"SELECT * FROM {source_table_full}"
            else:
                query = f"SELECT * FROM {source_table_full} WHERE {incremental_col_name} > '{last_load_time}'"
            
            print(f"Starting incremental load: {source_table_full} -> {target_table_full} after {last_load_time}")
            print(query)
            
            # CRITICAL FIX: Must pass all 3 parameters including query
            df = self.read_data(source_schema, source_table, query)
            
            current_time = df.select(max(col(incremental_col_name)).alias(f"{incremental_col_name}")).first()[f"{incremental_col_name}"]
            
            if last_load_time is None:
                print(f"Incremental first time load successful: {source_table_full}")
                df.write.format("delta").mode("overwrite").saveAsTable(f"{target_table_full}")

                self.update_config_table(source_table_full, target_table_full,current_time)
                self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "incremental", "success")

                return

            df.createOrReplaceTempView("incremental_view")

            self.spark.sql(f"""
                MERGE INTO {target_table_full} AS target
                USING incremental_view AS source
                ON target.{PK} = source.{PK}
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
            """)

            print(f"Incremental load successful: {source_table_full}")
            self.update_config_table(source_table_full, target_table_full,current_time)
            self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "incremental", "success")
        except Exception as e:
            print(f"Incremental load failed for {source_table_full}: {e}")
            self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "incremental", "failed", str(e))
            self.logger.fetch_error(target_table_full, str(e)) 
    
        
    def main(self):
        config_df = self.spark.table(f"{self.config_catalog}.{self.config_schema}.{self.config_table}") \
                    .filter(col("source") == f"{self.src}") \
                    .select("source_schema","source_table", "target_table_catalog","target_table_schema","target_table_name", "load_type","key_column", "load_type_col_name")

        schema_ = config_df.select('target_table_schema').first()['target_table_schema']
        
        # Ensure logging target exists
        CatalogUtils.ensure_catalog_and_schema(self.spark, self.config_catalog, schema_)
        # jdbc_driver = self.jdbc_driver
    
        for row in config_df.collect():
            source_schema= row['source_schema']
            source_table = row['source_table']
            target_table_catalog = row['target_table_catalog']
            target_table_schema = row['target_table_schema']
            target_table = row['target_table_name']
            incremental_col_name = row["load_type_col_name"]
            load_type = row["load_type"]
            key_column = row["key_column"]

            if load_type == "full":
                self.migrate_full_data(source_schema, source_table, target_table_catalog, target_table_schema, target_table)
            elif load_type == "incremental":
                self.migrate_incremental_data(source_schema, source_table, target_table_catalog, target_table_schema, target_table,incremental_col_name,key_column)
            else:
                print(f"Unknown load_type for {source_table}")
                self.logger.log_load(f"{self.src}", source_table, target_table, load_type, "failed", "Unknown load_type")
                self.logger.fetch_error(target_table, "Unknown load_type")