from pyspark.sql.functions import col,concat_ws,max
from datetime import datetime
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, LongType
from utility.catalog_utils import CatalogUtils

class Migration:
    def __init__(self,spark,config_catalog,config_schema,config_table,src,logger, jdbc_driver, sfURL, sfUser, sfPassword, sfWarehouse, sfRole):
        self.spark = spark
        self.config_catalog = config_catalog
        self.config_schema = config_schema
        self.config_table= config_table
        self.src=src
        self.logger = logger
        self.jdbc_driver = jdbc_driver
        self.sfURL = sfURL
        self.sfUser = sfUser
        self.sfPassword = sfPassword                                         
        self.sfWarehouse = sfWarehouse                         
        self.sfRole = sfRole                             
            

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
    
    # def read_data(self, jdbc_driver,source_schema,source_table):
    #     # jdbc_url = f"jdbc:{self.src}://{self.host}:{self.port}/{source_schema}"

    #     return self.spark.read \
    #           .format("snowflake") \
    #           .options(**self.sfOptions) \
    #           .option("dbtable", source_table) \
    #           .load()

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

    def migrate_full_data(self,source_schema, source_table, target_table_catalog, target_table_schema, target_table,sfOptions, partition_by=None, cluster_by=None, optimize=None, z_order=None):
        try:
            
            source_table_full = f"{source_schema}.{source_table}"
            target_table_full = f"{target_table_catalog}.{target_table_schema}.{target_table}"

            print(f"Starting full load: {source_table_full} -> {target_table_full}")
            
            # jdbc_driver = jdbc_driver                
            
            df = self.spark.read \
              .format("snowflake") \
              .options(**sfOptions) \
              .option("dbtable", source_table) \
              .load()
            
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

    def migrate_incremental_data(self,source_schema, source_table, target_table_catalog, target_table_schema, target_table,incremental_col_name,PK, sfOptions, partition_by=None, cluster_by=None, optimize=None, z_order=None):
        try:
            source_table_full = f"{source_schema}.{source_table}"
            target_table_full = f"{target_table_catalog}.{target_table_schema}.{target_table}"

            last_load_time = self.get_last_load_time(source_table_full, target_table_full)
            query = f"(SELECT * FROM {source_table} WHERE {incremental_col_name} > '{last_load_time}') AS src"

            if last_load_time is None:
                query = f"(SELECT * FROM {source_table}) AS src"
            
            print(f"Starting incremental load: {source_table_full} -> {target_table_full} after {last_load_time}")

            # jdbc_driver = jdbc_driver
            
            df = self.spark.read \
              .format("snowflake") \
              .options(**sfOptions) \
              .option("query", query) \
              .load()
            # df.display()
            current_time = df.select(max(col(incremental_col_name)).alias(f"{incremental_col_name}")).first()[f"{incremental_col_name}"]
            # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", incremental_col_name)
            if current_time is None:
                current_time = self.spark.table(target_table_full).select(max(col(incremental_col_name)).alias(f"{incremental_col_name}")).first()[f"{incremental_col_name}"]

            if last_load_time is None:
                self.write_table(df, target_table_full, "overwrite", partition_by, cluster_by)
                print(f"Incremental first time load successful: {source_table_full}")
                
                self.optimize_table(target_table_full, optimize, z_order)
                # print("Optimized table for full load")
                self.update_config_table(source_table_full, target_table_full,current_time)
                # print("Updated config table for full load")
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

            print(f"Incremental load successful: {source_table_full}")
            print(f"Optimized table for incremental load {current_time}")
            self.update_config_table(source_table_full, target_table_full,current_time)
            print(f"Updated config table for incremental load {current_time}")
            self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "incremental", "success")
        except Exception as e:
            print(f"Incremental load failed for {source_table_full}: {e}")
            self.logger.log_load(f"{self.src}", source_table_full, target_table_full, "incremental", "failed", str(e))
            self.logger.fetch_error(target_table_full, str(e)) 
    
        
    def main(self):

        config_df = self.spark.table(f"{self.config_catalog}.{self.config_schema}.{self.config_table}") \
              .filter(col("source") == "snowflake") \
                    .select("source_schema", "source_database", "source_table", "target_table_catalog","target_table_schema","target_table_name", "load_type","load_type_col_name", "key_column")

        for row in config_df.collect():
            source_table = row['source_table']
            target_table = row['target_table_name']
            incremental_col_name = row["load_type_col_name"]
            load_type = row["load_type"]
            primary_key = row["key_column"]
            sfDatabase = row['source_database']
            sfSchema = row['source_schema']
            target_table_schema = row['target_table_schema']
            target_table_catalog = row['target_table_catalog']

            sfOptions = {
            "sfDatabase" : sfDatabase,
            "sfURL" : self.sfURL,
            "sfUser" : self.sfUser,                           
            "sfPassword" : self.sfPassword,              
            "sfSchema": sfSchema,                              
            "sfWarehouse": self.sfWarehouse,                         
            "sfRole": self.sfRole                             
            }
            
            if load_type == "full":
                self.migrate_full_data(source_schema=sfSchema, source_table=source_table, target_table_catalog=target_table_catalog, target_table_schema=target_table_schema, target_table=target_table, sfOptions=sfOptions, partition_by=None, cluster_by=None, optimize=None, z_order=None)
            elif load_type == "incremental":
                self.migrate_incremental_data(source_schema=sfSchema, source_table=source_table, target_table_catalog=target_table_catalog, target_table_schema=target_table_schema, target_table=target_table, incremental_col_name=incremental_col_name,PK=primary_key, sfOptions=sfOptions, partition_by=None, cluster_by=None, optimize=None, z_order=None)
            else:
                print(f"Unknown load_type for {source_table}")
                self.logger.log_load(f"{self.src}", source_table, target_table, load_type, "failed", "Unknown load_type")
                self.logger.fetch_error(target_table, "Unknown load_type")