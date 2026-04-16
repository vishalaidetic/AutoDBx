from pyspark.sql.functions import col,concat_ws,max
from datetime import datetime
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, LongType
from utility.catalog_utils import CatalogUtils

class Migration:
    def __init__(self,spark,config_catalog,config_schema,config_table, host,port, user_name, password,src,logger, jdbc_driver):
        self.spark = spark
        self.config_catalog = config_catalog
        self.config_schema = config_schema
        self.config_table= config_table
        self.src=src
        self.host=host
        self.port = port
        self.user_name = user_name
        self.user_password = password
        self.jdbc_driver = jdbc_driver
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
    
    def read_data(self, jdbc_driver,source_schema,source_table):
        jdbc_url = f"jdbc:{self.src}://{self.host}:{self.port}/{source_schema}"

        return self.spark.read.format("jdbc") \
                    .option("url", jdbc_url) \
                    .option("driver", jdbc_driver) \
                    .option("dbtable", source_table) \
                    .option("user", self.user_name) \
                    .option("password", self.user_password).load()

    def write_table(self, df, target_table_full, mode, partition_by=None, cluster_by=None):
        writer = df.write.option("overwriteSchema", "true").format("delta").mode(mode)
        
        if partition_by:
            partition_cols = [col.strip() for col in partition_by.split(",")]
            writer = writer.partitionBy(*partition_cols)
        
        if cluster_by:
            cluster_cols = [col.strip() for col in cluster_by.split(",")]
            writer = writer.clusterBy(*cluster_cols)
        
        writer.saveAsTable(target_table_full)

    def optimize_table(self, target_table_full, optimize, z_order):
        if z_order:
            z_order_cols = [col.strip() for col in z_order.split(",")]
            self.spark.sql(f"OPTIMIZE {target_table_full} ZORDER BY ({','.join(z_order_cols)})")
            print(f"Performed optimization on {target_table_full} with z order on {z_order_cols}")
        elif optimize:
            self.spark.sql(f"OPTIMIZE {target_table_full}")
            print(f"Performed optimization on {target_table_full}")

    def migrate_full_data(self,source_schema, source_table, target_table_catalog, target_table_schema, target_table, jdbc_driver, partition_by=None, cluster_by=None, optimize=None, z_order=None):
        try:
            
            source_table_full = f"{source_schema}.{source_table}"
            target_table_full = f"{target_table_catalog}.{target_table_schema}.{target_table}"

            print(f"Starting full load: {source_table_full} -> {target_table_full}")
            
            jdbc_driver = jdbc_driver                
            
            df = self.read_data(jdbc_driver,source_schema, source_table)
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.write_table(df, target_table_full, "overwrite", partition_by, cluster_by)
            print(f"Full load successful: {source_table_full}")

            self.optimize_table(target_table_full, optimize, z_order)

            self.update_config_table(source_table_full, target_table_full,current_time)
            self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "full", "success")
        except Exception as e:
            print(f"Full load failed: {source_table_full}")
            print(f"Error: {str(e)}")
            self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "full", "failed", str(e))
            self.logger.fetch_error(target_table_full, str(e))

    def migrate_incremental_data(self,source_schema, source_table, target_table_catalog, target_table_schema, target_table,incremental_col_name,PK, jdbc_driver, partition_by=None, cluster_by=None, optimize=None, z_order=None):
        try:
            source_table_full = f"{source_schema}.{source_table}"
            target_table_full = f"{target_table_catalog}.{target_table_schema}.{target_table}"

            last_load_time = self.get_last_load_time(source_table_full, target_table_full)
            query = f"(SELECT * FROM {source_table} WHERE {incremental_col_name} > '{last_load_time}') AS src"

            if last_load_time is None:
                query = f"(SELECT * FROM {source_table}) AS src"
            
            print(f"Starting incremental load: {source_table_full} -> {target_table_full} after {last_load_time}")

            jdbc_driver = jdbc_driver
            
            df = self.read_data(jdbc_driver,source_schema, query)
            
            current_time = df.select(max(col(incremental_col_name)).alias(f"{incremental_col_name}")).first()[f"{incremental_col_name}"]
            
            if last_load_time is None:
                print(f"Incremental first time load successful: {source_table_full}")
                self.write_table(df, target_table_full, "overwrite", partition_by, cluster_by)

                self.optimize_table(target_table_full, optimize, z_order)

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

            self.optimize_table(target_table_full, optimize, z_order)
            if current_time is None:
                current_time = self.spark.table(target_table_full).select(max(col(incremental_col_name)).alias(f"{incremental_col_name}")).first()[f"{incremental_col_name}"]
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
                    .select("source_schema","source_table", "target_table_catalog","target_table_schema","target_table_name", "load_type","key_column", "load_type_col_name", "Optimize", "PartitionBy", "ClusterBy", "Z-Order")

        schema_ = config_df.select('target_table_schema').first()['target_table_schema']
        
        CatalogUtils.ensure_catalog_and_schema(self.spark, self.config_catalog, schema_)
        jdbc_driver = self.jdbc_driver
    
        for row in config_df.collect():
            source_schema= row['source_schema']
            source_table = row['source_table']
            target_table_catalog = row['target_table_catalog']
            target_table_schema = row['target_table_schema']
            target_table = row['target_table_name']
            incremental_col_name = row["load_type_col_name"]
            load_type = row["load_type"]
            key_column = row["key_column"]
            optimize = row["Optimize"]
            partition_by = row["PartitionBy"]
            cluster_by = row["ClusterBy"]
            z_order = row["Z-Order"]

            if load_type == "full":
                self.migrate_full_data(source_schema, source_table, target_table_catalog, target_table_schema, target_table, jdbc_driver, partition_by, cluster_by, optimize, z_order)
            elif load_type == "incremental":
                self.migrate_incremental_data(source_schema, source_table, target_table_catalog, target_table_schema, target_table,incremental_col_name,key_column, jdbc_driver, partition_by, cluster_by, optimize, z_order)
            else:
                print(f"Unknown load_type for {source_table}")
                self.logger.log_load(f"{self.src}", source_table, target_table, load_type, "failed", "Unknown load_type")
                self.logger.fetch_error(target_table, "Unknown load_type")
