from datetime import datetime
from pyspark.sql.functions import col, mean
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, LongType
import json
from utility.catalog_utils import CatalogUtils

class Validation:
    def __init__(self, spark, config_catalog, config_schema, config_table, validation_catalog, validation_schema, validation_table, host, port, user_name, password, src, jdbc_driver, hostNameInCertificate):
        self.spark = spark
        self.config_catalog = config_catalog
        self.config_schema = config_schema
        self.config_table = config_table
        self.validation_catalog = validation_catalog
        self.validation_schema = validation_schema
        self.validation_table = validation_table
        self.src = src
        self.host = host
        self.port = port
        self.user_name = user_name
        self.user_password = password
        self.jdbc_driver = jdbc_driver
        self.hostNameInCertificate = hostNameInCertificate

        # Simplified validation schema - removed median, mode, sum, string_length_sum fields
        self.val_schema = StructType([
            StructField("source", StringType(), True),
            StructField("source_full_table_name", StringType(), True),
            StructField("target_full_table_name", StringType(), True),
            StructField("load_time", TimestampType(), True),
            StructField("row_count_source", LongType(), True),
            StructField("row_count_target", LongType(), True),
            StructField("row_count_match", StringType(), True),
            StructField("distinct_count_source", LongType(), True),
            StructField("distinct_count_target", LongType(), True),
            StructField("distinct_count_match", StringType(), True),
            StructField("column_count_source", LongType(), True),
            StructField("column_count_target", LongType(), True),
            StructField("column_count_match", StringType(), True),
            StructField("source_column_type_count", StringType(), True),
            StructField("target_column_type_count", StringType(), True),
            StructField("column_type_count_match", StringType(), True),
            StructField("schema_match", StringType(), True),
            StructField("source_schema", StringType(), True),
            StructField("target_schema", StringType(), True),
            StructField("schema_structure_match", StringType(), True),
            StructField("source_mean", StringType(), True),
            StructField("target_mean", StringType(), True),
            StructField("mean_match", StringType(), True),
            StructField("final_status", StringType(), True)
        ])

        # Ensure logging target exists
        CatalogUtils.ensure_catalog_and_schema(self.spark, self.validation_catalog, self.validation_schema)

    def read_data(self, jdbc_driver,source_schema,source_table):
        jdbc_url = f"jdbc:{self.src}://{self.host}:{self.port};databaseName={source_schema};encrypt=true;trustServerCertificate=true;hostNameInCertificate={self.hostNameInCertificate}"
        if len(source_table.split(" ")) == 1:
            return self.spark.read.format("jdbc") \
                    .option("url", jdbc_url) \
                    .option("driver", jdbc_driver) \
                    .option("dbtable", source_table) \
                    .option("user", self.user_name) \
                    .option("password", self.user_password).load()
        else:
            return self.spark.read.format("jdbc") \
                    .option("url", jdbc_url) \
                    .option("driver", jdbc_driver) \
                    .option("query", source_table) \
                    .option("user", self.user_name) \
                    .option("password", self.user_password).load()

    def validate_row_counts(self, target_df, source_df):
        """
        Validate row counts between source and target tables
        """
        row_count_target = target_df.count()
        row_count_source = source_df.count()
        
        if row_count_target == row_count_source:
            print(f"Row counts match: {row_count_target}")
            row_count_match = "Pass"
        elif row_count_target > row_count_source:
            print(f"Row count mismatch: {row_count_target} (target) vs {row_count_source} (source)")
            print(f"Target has {row_count_target - row_count_source} extra rows")
            row_count_match = "Fail"
        else:
            print(f"Row count mismatch: {row_count_target} (target) vs {row_count_source} (source)")
            print(f"Source has {row_count_source - row_count_target} extra rows")
            row_count_match = "Fail"
        
        return row_count_target, row_count_source, row_count_match

    def validate_distinct_counts(self, target_df, source_df):
        """
        Validate distinct row counts between source and target tables
        """
        distinct_count_target = target_df.distinct().count()
        distinct_count_source = source_df.distinct().count()
        
        if distinct_count_target == distinct_count_source:
            print(f"Distinct counts match: {distinct_count_target}")
            distinct_count_match = "Pass"
        else:
            print(f"Distinct count mismatch: {distinct_count_target} (target) vs {distinct_count_source} (source)")
            distinct_count_match = "Fail"
        
        return distinct_count_target, distinct_count_source, distinct_count_match

    def validate_column_counts(self, target_df, source_df):
        """
        Validate column counts between source and target tables
        """
        col_count_target = len(target_df.columns)
        col_count_source = len(source_df.columns)
        
        if col_count_target == col_count_source:
            print(f"Column counts match: {col_count_target}")
            col_count_match = "Pass"
        else:
            print(f"Column count mismatch: {col_count_target} (target) vs {col_count_source} (source)")
            col_count_match = "Fail"
        
        return col_count_target, col_count_source, col_count_match

    def validate_schema_match(self, target_df, source_df):
        """
        Validate schema match between source and target tables
        """
        schema_target = {field.name.lower(): field.dataType.simpleString() for field in target_df.schema}
        schema_source = {field.name.lower(): field.dataType.simpleString() for field in source_df.schema}
        
        if schema_target.keys() == schema_source.keys():
            print("Column names match")
        else:
            print("Column names mismatch")
            print(f"Columns in target but not in source: {schema_target.keys() - schema_source.keys()}")
            print(f"Columns in source but not in target: {schema_source.keys() - schema_target.keys()}")
        
        schema_match = "Pass"
        for col_name in schema_target.keys() & schema_source.keys():
            if schema_target[col_name] != schema_source[col_name]:
                print(f"Data type mismatch for column '{col_name}': {schema_target[col_name]} (target) vs {schema_source[col_name]} (source)")
                schema_match = "Fail"
        
        return schema_match, json.dumps(schema_target), json.dumps(schema_source)

    def get_numeric_columns(self, df):
        """
        Get numeric columns (integer and double types) from dataframe
        """
        numeric_types = ['int', 'bigint', 'float', 'double', 'decimal']
        numeric_cols = []
        
        for field in df.schema:
            if any(num_type in field.dataType.simpleString().lower() for num_type in numeric_types):
                numeric_cols.append(field.name)
        
        return numeric_cols

    def get_column_type_counts(self, df):
        """
        Count the number of integer, string, and double type columns and return as JSON
        """
        integer_count = 0
        string_count = 0
        double_count = 0
        
        for field in df.schema:
            data_type = field.dataType.simpleString().lower()
            
            # Count integer types
            if any(int_type in data_type for int_type in ['int', 'bigint']):
                integer_count += 1
            # Count string types  
            elif 'string' in data_type:
                string_count += 1
            # Count double/float types
            elif any(float_type in data_type for float_type in ['float', 'double', 'decimal']):
                double_count += 1
        
        return json.dumps({
            "integer_columns": integer_count,
            "string_columns": string_count,
            "double_columns": double_count
        })

    def compare_column_type_counts(self, source_counts, target_counts):
        """
        Compare column type counts between source and target
        """
        source_dict = json.loads(source_counts)
        target_dict = json.loads(target_counts)
        
        if source_dict == target_dict:
            print(f"Column type count match: {source_dict}")
            return "Pass"
        else:
            print(f"Column type count mismatch:")
            print(f"Source: {source_dict}")
            print(f"Target: {target_dict}")
            return "Fail"

    def compare_schemas(self, source_schema, target_schema):
        """
        Compare schema structures and return pass/fail status
        """
        source_dict = json.loads(source_schema)
        target_dict = json.loads(target_schema)
        
        if source_dict == target_dict:
            print("Schema structure match: Pass")
            return "Pass"
        else:
            print("Schema structure match: Fail")
            return "Fail"

    def compare_statistics(self, source_stats, target_stats, stat_name):
        """
        Compare statistical values between source and target
        """
        source_dict = json.loads(source_stats)
        target_dict = json.loads(target_stats)
        
        if source_dict == target_dict:
            print(f"{stat_name} match: Pass")
            return "Pass"
        else:
            print(f"{stat_name} match: Fail")
            return "Fail"

    def calculate_mean_statistics(self, df, numeric_cols):
        """
        Calculate only mean for numeric columns
        """
        if not numeric_cols:
            return "{}"
        
        # Calculate mean only
        mean_values = {}
        for col_name in numeric_cols:
            try:
                mean_val = df.select(mean(col(col_name)).alias("mean")).collect()[0]["mean"]
                mean_values[col_name] = float(mean_val) if mean_val is not None else None
            except:
                mean_values[col_name] = None
        
        return json.dumps(mean_values)

    def calculate_final_status(self, status_list):
        """
        Calculate final status based on all individual status checks
        """
        if all(status == "Pass" for status in status_list):
            print("Final validation status: Pass")
            return "Pass"
        else:
            print("Final validation status: Fail")
            return "Fail"

    def validate_tables(self, jdbc_driver, target_table, source_table):
        """
        Main validation function that orchestrates all validation checks
        """
        print(f"Starting validation for {source_table} -> {target_table}")
        
        try:
            source_schema, source_table_name = source_table.split(".")
            source_df = self.read_data(jdbc_driver, source_schema, source_table_name)
        except Exception as e:
            print(f"Connection cant be established for {source_table} because: {e}")
            return

        target_df = self.spark.read.table(target_table)
        
        # Perform validations
        row_count_target, row_count_source, row_count_match = self.validate_row_counts(target_df, source_df)
        distinct_count_target, distinct_count_source, distinct_count_match = self.validate_distinct_counts(target_df, source_df)
        col_count_target, col_count_source, col_count_match = self.validate_column_counts(target_df, source_df)
        schema_match, target_schema, source_schema = self.validate_schema_match(target_df, source_df)
        
        # Get column type counts in JSON format
        source_column_type_count = self.get_column_type_counts(source_df)
        target_column_type_count = self.get_column_type_counts(target_df)
        column_type_count_match = self.compare_column_type_counts(source_column_type_count, target_column_type_count)
        
        # Schema structure comparison
        schema_structure_match = self.compare_schemas(source_schema, target_schema)
        
        # Get numeric columns for mean calculation only
        source_numeric_cols = self.get_numeric_columns(source_df)
        target_numeric_cols = self.get_numeric_columns(target_df)
        
        # Calculate only mean statistics
        source_mean = self.calculate_mean_statistics(source_df, source_numeric_cols)
        target_mean = self.calculate_mean_statistics(target_df, target_numeric_cols)
        
        # Compare mean statistics
        mean_match = self.compare_statistics(source_mean, target_mean, "Mean")
        
        # Print summary of all status checks
        print("\n--- Validation Status Summary ---")
        print(f"Row count match: {row_count_match}")
        print(f"Distinct count match: {distinct_count_match}")
        print(f"Column count match: {col_count_match}")
        print(f"Column type count match: {column_type_count_match}")
        print(f"Schema match: {schema_match}")
        print(f"Schema structure match: {schema_structure_match}")
        print(f"Mean match: {mean_match}")
        
        # Calculate final status (simplified list)
        all_status_checks = [
            row_count_match,
            distinct_count_match,
            col_count_match,
            column_type_count_match,
            schema_match,
            schema_structure_match,
            mean_match
        ]
        
        final_status = self.calculate_final_status(all_status_checks)
        
        # Prepare data for validation table (simplified data)
        data = [
            (
                f"{self.src}", 
                source_table, 
                target_table, 
                datetime.now(),
                row_count_source, 
                row_count_target, 
                row_count_match,
                distinct_count_source,
                distinct_count_target,
                distinct_count_match,
                col_count_source, 
                col_count_target, 
                col_count_match,
                source_column_type_count,
                target_column_type_count,
                column_type_count_match,
                schema_match,
                source_schema,
                target_schema,
                schema_structure_match,
                source_mean,
                target_mean,
                mean_match,
                final_status
            )
        ]
        
        # Save validation results
        val_df = self.spark.createDataFrame(data, self.val_schema)
        val_df.write.mode("append").saveAsTable(f"{self.validation_catalog}.{self.validation_schema}.{self.validation_table}")
        
        print("Validation complete.")
        print("-" * 50)

    def main(self):
        """
        Main execution method that reads config and runs validation for all tables
        """
        jdbc_driver = self.jdbc_driver
        config_df = self.spark.table(f"{self.config_catalog}.{self.config_schema}.{self.config_table}") \
                    .filter(col("source") == f"{self.src}") \
                    .select("source_schema", "source_table", "target_table_catalog", "target_table_schema", "target_table_name", "load_type", "key_column", "load_type_col_name")
        
        for row in config_df.collect():
            source_table = f"{row['source_schema']}.{row['source_table']}"
            target_table = f"{row['target_table_catalog']}.{row['target_table_schema']}.{row['target_table_name']}"

            self.validate_tables(jdbc_driver, target_table, source_table)
            print(f"Validation Done for {target_table}")