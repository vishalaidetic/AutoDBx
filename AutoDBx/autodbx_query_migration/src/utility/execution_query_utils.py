import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import col, lit, current_timestamp
import os
import time
from datetime import datetime


class QueryExecutionManager:
    """
    A class to manage query execution from migration results CSV file.
    Handles table creation, query execution, and result tracking.
    """
    
    def __init__(self, spark, execution_table_catalog, execution_table_schema, 
                 execution_table, csv_file_path):
        """
        Initialize the QueryExecutionManager.
        
        Args:
            spark: SparkSession object
            execution_table_catalog: Catalog name for execution table
            execution_table_schema: Schema name for execution table
            execution_table: Table name for execution table
            csv_file_path: Path to the migration results CSV file
        """
        self.spark = spark
        self.execution_table_catalog = execution_table_catalog
        self.execution_table_schema = execution_table_schema
        self.execution_table = execution_table
        self.csv_file_path = csv_file_path
        self.full_table_name = f"{execution_table_catalog}.{execution_table_schema}.{execution_table}"
        
    def check_csv_file_exists(self):
        """
        Check if the migration results CSV file exists.
        
        Raises:
            FileNotFoundError: If migration_results.csv doesn't exist
        """
        if not os.path.exists(self.csv_file_path):
            raise FileNotFoundError("migration_results.csv doesn't exist")
        print(f"CSV file found at: {self.csv_file_path}")
    
    def read_migration_results(self):
        """
        Read migration results from CSV file using pandas and convert to Spark DataFrame.
        
        Returns:
            pyspark.sql.DataFrame: DataFrame containing migration results
        """
        try:
            # Read CSV using pandas first
            pandas_df = pd.read_csv(self.csv_file_path)
            
            # Convert to Spark DataFrame
            spark_df = self.spark.createDataFrame(pandas_df)
            
            print(f"Successfully read {spark_df.count()} records from migration_results.csv")
            return spark_df
            
        except Exception as e:
            raise Exception(f"Error reading migration results CSV: {str(e)}")
    
    def check_and_create_execution_table(self):
        """
        Check if execution table exists, create it if it doesn't.
        """
        try:
            # Check if table exists
            self.spark.sql(f"DESCRIBE TABLE {self.full_table_name}")
            print(f"Execution table {self.full_table_name} already exists")
            
        except Exception:
            # Table doesn't exist, create it
            print(f"Creating execution table: {self.full_table_name}")
            
            create_table_sql = f"""
            CREATE TABLE {self.full_table_name} (
                source_query_file STRING,
                source_query STRING,
                target_query STRING,
                execution_status STRING,
                error_message STRING,
                execution_time TIMESTAMP
            ) USING DELTA
            """
            
            self.spark.sql(create_table_sql)
            print(f"Successfully created execution table: {self.full_table_name}")
    
    def get_already_executed_files(self):
        """
        Get list of source_query_files that have already been executed.
        
        Returns:
            set: Set of source_query_file values already in execution table
        """
        try:
            existing_df = self.spark.sql(f"""
                SELECT DISTINCT source_query_file 
                FROM {self.full_table_name}
            """)
            
            executed_files = set([row.source_query_file for row in existing_df.collect()])
            print(f"Found {len(executed_files)} already executed files")
            return executed_files
            
        except Exception as e:
            print(f"Error getting already executed files: {str(e)}")
            return set()
    
    def filter_pending_executions(self, migration_df):
        """
        Filter migration results to get only pending executions.
        
        Args:
            migration_df: DataFrame containing migration results
            
        Returns:
            pyspark.sql.DataFrame: Filtered DataFrame with pending executions
        """
        # Get already executed files
        executed_files = self.get_already_executed_files()
        
        # Filter for Flag = 'C' and not already executed
        filtered_df = migration_df.filter(col("Flag") == "C")
        
        if executed_files:
            filtered_df = filtered_df.filter(~col("source_query_file").isin(executed_files))
        
        pending_count = filtered_df.count()
        print(f"Found {pending_count} queries pending for execution")
        
        return filtered_df
    
    def execute_single_query(self, target_query):
        """
        Execute a single target query and return execution status.
        
        Args:
            target_query: Query string to execute
            
        Returns:
            tuple: (execution_status, error_message, execution_time)
        """
        start_time = time.time()
        execution_time = datetime.now()
        
        try:
            # Execute the query
            self.spark.sql(target_query)
            
            execution_status = "Success"
            error_message = None
            
            print(f"Query executed successfully in {time.time() - start_time:.2f} seconds")
            
        except Exception as e:
            execution_status = "Failure"
            error_message = str(e)
            
            print(f"Query execution failed: {error_message}")
        
        return execution_status, error_message, execution_time
    
    def insert_execution_result(self, source_query_file, source_query, target_query,
                              execution_status, error_message, execution_time):
        """
        Insert execution result into the execution table.
        
        Args:
            source_query_file: Source query file name
            source_query: Original source query
            target_query: Converted target query
            execution_status: Execution status (Success/Failure)
            error_message: Error message if execution failed
            execution_time: Timestamp of execution
        """
        try:
            # Define the schema explicitly to avoid type inference issues
            schema = StructType([
                StructField("source_query_file", StringType(), True),
                StructField("source_query", StringType(), True),
                StructField("target_query", StringType(), True),
                StructField("execution_status", StringType(), True),
                StructField("error_message", StringType(), True),
                StructField("execution_time", TimestampType(), True)
            ])
            
            # Handle None values properly
            error_msg = error_message if error_message is not None else ""
            
            # Create DataFrame for the result with explicit schema
            result_data = [(source_query_file, source_query, target_query,
                           execution_status, error_msg, execution_time)]
            
            result_df = self.spark.createDataFrame(result_data, schema)
            
            # Insert into execution table
            result_df.write.mode("append").saveAsTable(self.full_table_name)
            
            print(f"Successfully inserted execution result for: {source_query_file}")
            
        except Exception as e:
            print(f"Error inserting execution result: {str(e)}")
    
    def execute_pending_queries(self):
        """
        Main method to execute all pending queries from migration results.
        """
        try:
            # Check if CSV file exists
            self.check_csv_file_exists()
            
            # Read migration results
            migration_df = self.read_migration_results()
            
            # Check and create execution table
            self.check_and_create_execution_table()
            
            # Filter pending executions
            pending_df = self.filter_pending_executions(migration_df)
            
            if pending_df.count() == 0:
                print("No queries pending for execution")
                return
            
            # Process each pending query
            pending_queries = pending_df.select(
                "source_query_file", "source_query", "converted_query"
            ).collect()
            
            total_queries = len(pending_queries)
            successful_executions = 0
            failed_executions = 0
            
            print(f"Starting execution of {total_queries} queries")
            
            for i, row in enumerate(pending_queries, 1):
                source_query_file = row.source_query_file
                source_query = row.source_query
                target_query = row.converted_query
                
                print(f"Processing query {i}/{total_queries}: {source_query_file}")
                
                # Execute the query
                execution_status, error_message, execution_time = self.execute_single_query(target_query)
                
                # Insert result into execution table
                self.insert_execution_result(
                    source_query_file, source_query, target_query,
                    execution_status, error_message, execution_time
                )
                
                if execution_status == "Success":
                    successful_executions += 1
                else:
                    failed_executions += 1
            
            print(f"Execution completed. Success: {successful_executions}, Failed: {failed_executions}")
            
        except Exception as e:
            print(f"Error in execute_pending_queries: {str(e)}")
            raise