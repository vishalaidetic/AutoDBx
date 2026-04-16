import pandas as pd
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import re

class DataQuality:
    """
    Dynamic Data Quality Framework for Spark DataFrames
    Works on any Spark DataFrame without knowing column names
    Returns results as Pandas DataFrame showing pass/fail for each of 7 DQ dimensions
    """
    
    def __init__(self,spark,data_quality_catalog,data_quality_schema,data_quality_table):
        self.spark = spark
        self.data_quality_catalog = data_quality_catalog
        self.data_quality_schema = data_quality_schema
        self.data_quality_table = data_quality_table
        
    def validate_dataframe(self, df, layer_name):
        """
        Validate any Spark dataframe dynamically and return results as DataFrame
        Returns DataFrame with 7 DQ dimensions and their pass/fail status
        """
        results = {
            'Layer': layer_name,
            'Completeness': 'PASS',
            'Validity': 'PASS', 
            'Consistency': 'PASS',
            'Uniqueness': 'PASS',
            'Accuracy': 'PASS',
            'Timeliness': 'PASS',
            'Integrity': 'PASS'
        }
        
        # Check each dimension dynamically
        results['Completeness'] = self._check_completeness(df)
        results['Validity'] = self._check_validity(df)
        results['Consistency'] = self._check_consistency(df)
        results['Uniqueness'] = self._check_uniqueness(df)
        results['Accuracy'] = self._check_accuracy(df)
        results['Timeliness'] = self._check_timeliness(df)
        results['Integrity'] = self._check_integrity(df)
        
        return pd.DataFrame([results])
    
    def _check_completeness(self, df):
        """Check completeness - null checks across all columns"""
        try:
            total_rows = df.count()
            if total_rows == 0:
                return 'FAIL'
            
            total_columns = len(df.columns)
            total_cells = total_rows * total_columns
            
            # Count nulls across all columns
            null_counts = []
            for col in df.columns:
                null_count = df.filter(F.col(col).isNull()).count()
                null_counts.append(null_count)
            
            total_nulls = sum(null_counts)
            completeness_ratio = (total_cells - total_nulls) / total_cells
            
            # Pass if completeness is above 80%
            return 'PASS' if completeness_ratio >= 0.8 else 'FAIL'
            
        except Exception:
            return 'FAIL'
    
    def _check_validity(self, df):
        """Check validity - data type consistency and format validation"""
        try:
            validity_issues = 0
            schema = df.schema
            
            for field in schema.fields:
                col_name = field.name
                col_type = field.dataType
                
                # Check string columns for mixed formats
                if isinstance(col_type, StringType):
                    # Check if column might contain numeric data stored as strings
                    numeric_pattern = r'^-?\d+\.?\d*$'
                    
                    # Sample some data to check format consistency
                    sample_data = df.select(col_name).filter(
                        F.col(col_name).isNotNull()
                    ).limit(1000).collect()
                    
                    if len(sample_data) > 10:  # Need reasonable sample size
                        values = [row[col_name] for row in sample_data]
                        
                        # Check for mixed numeric/string formats
                        numeric_matches = sum(1 for val in values if re.match(numeric_pattern, str(val).strip()))
                        total_values = len(values)
                        
                        # If some values look numeric and others don't, it's inconsistent
                        if 0 < numeric_matches < total_values:
                            validity_issues += 1
                
                # Check for data type mismatches in numeric columns
                elif isinstance(col_type, (IntegerType, LongType, FloatType, DoubleType)):
                    # Check for infinite values
                    inf_count = df.filter(
                        F.col(col_name).isNotNull() & 
                        (F.isnan(F.col(col_name)) | F.col(col_name).isin([float('inf'), float('-inf')]))
                    ).count()
                    
                    if inf_count > 0:
                        validity_issues += 1
            
            # Pass if less than 10% of columns have validity issues
            total_columns = len(df.columns)
            validity_threshold = max(1, total_columns * 0.1)
            return 'PASS' if validity_issues <= validity_threshold else 'FAIL'
            
        except Exception:
            return 'FAIL'
    
    def _check_consistency(self, df):
        """Check consistency - range validation and outlier detection"""
        try:
            consistency_issues = 0
            schema = df.schema
            
            # Get numeric columns
            numeric_columns = [
                field.name for field in schema.fields 
                if isinstance(field.dataType, (IntegerType, LongType, FloatType, DoubleType))
            ]
            
            for col_name in numeric_columns:
                # Calculate quartiles for outlier detection
                quartiles = df.select(
                    F.expr(f"percentile_approx({col_name}, 0.25)").alias("q1"),
                    F.expr(f"percentile_approx({col_name}, 0.75)").alias("q3")
                ).collect()[0]
                
                q1, q3 = quartiles['q1'], quartiles['q3']
                
                if q1 is not None and q3 is not None and q3 > q1:
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    # Count outliers
                    total_non_null = df.filter(F.col(col_name).isNotNull()).count()
                    outlier_count = df.filter(
                        F.col(col_name).isNotNull() & 
                        ((F.col(col_name) < lower_bound) | (F.col(col_name) > upper_bound))
                    ).count()
                    
                    if total_non_null > 0:
                        outlier_percentage = outlier_count / total_non_null
                        # Flag if more than 15% are outliers
                        if outlier_percentage > 0.15:
                            consistency_issues += 1
            
            # Check string columns for length consistency
            string_columns = [
                field.name for field in schema.fields 
                if isinstance(field.dataType, StringType)
            ]
            
            for col_name in string_columns:
                # Get length statistics
                length_stats = df.select(
                    F.avg(F.length(F.col(col_name))).alias("avg_length"),
                    F.stddev(F.length(F.col(col_name))).alias("std_length")
                ).collect()[0]
                
                avg_length = length_stats['avg_length']
                std_length = length_stats['std_length']
                
                if avg_length and std_length and avg_length > 0:
                    # High coefficient of variation indicates inconsistent lengths
                    cv = std_length / avg_length
                    if cv > 2.0:
                        consistency_issues += 1
            
            # Pass if less than 20% of columns have consistency issues
            total_relevant_columns = len(numeric_columns) + len(string_columns)
            if total_relevant_columns == 0:
                return 'PASS'
                
            consistency_threshold = max(1, total_relevant_columns * 0.2)
            return 'PASS' if consistency_issues <= consistency_threshold else 'FAIL'
            
        except Exception:
            return 'FAIL'
    
    def _check_uniqueness(self, df):
        """Check uniqueness - detect duplicate patterns"""
        try:
            uniqueness_issues = 0
            total_rows = df.count()
            
            if total_rows == 0:
                return 'PASS'
            
            # Check for completely duplicate rows
            distinct_rows = df.distinct().count()
            duplicate_percentage = (total_rows - distinct_rows) / total_rows
            
            if duplicate_percentage > 0.05:  # More than 5% duplicate rows
                uniqueness_issues += 1
            
            # Check individual columns for potential key violations
            for col_name in df.columns:
                # Get unique count and total count for the column
                stats = df.select(
                    F.countDistinct(col_name).alias("unique_count"),
                    F.count(F.when(F.col(col_name).isNotNull(), 1)).alias("non_null_count")
                ).collect()[0]
                
                unique_count = stats['unique_count']
                non_null_count = stats['non_null_count']
                
                if non_null_count > 0:
                    uniqueness_ratio = unique_count / non_null_count
                    
                    # If column has high uniqueness (>80%) but still has duplicates
                    # it might be intended as a key column
                    if uniqueness_ratio > 0.8 and uniqueness_ratio < 1.0:
                        duplicate_count = non_null_count - unique_count
                        duplicate_ratio = duplicate_count / non_null_count
                        if duplicate_ratio > 0.1:  # More than 10% duplicates
                            uniqueness_issues += 1
            
            return 'PASS' if uniqueness_issues == 0 else 'FAIL'
            
        except Exception:
            return 'FAIL'
    
    def _check_accuracy(self, df):
        """Check accuracy - business logic and statistical validation"""
        try:
            accuracy_issues = 0
            schema = df.schema
            
            # Get numeric columns
            numeric_columns = [
                field.name for field in schema.fields 
                if isinstance(field.dataType, (IntegerType, LongType, FloatType, DoubleType))
            ]
            
            for col_name in numeric_columns:
                column_lower = col_name.lower()
                
                # Age-like columns shouldn't be negative or > 150
                if any(age_word in column_lower for age_word in ['age', 'year', 'old']):
                    invalid_count = df.filter(
                        F.col(col_name).isNotNull() & 
                        ((F.col(col_name) < 0) | (F.col(col_name) > 150))
                    ).count()
                    if invalid_count > 0:
                        accuracy_issues += 1
                
                # Count/quantity columns shouldn't be negative
                elif any(count_word in column_lower for count_word in ['count', 'qty', 'quantity', 'num', 'total']):
                    negative_count = df.filter(
                        F.col(col_name).isNotNull() & (F.col(col_name) < 0)
                    ).count()
                    if negative_count > 0:
                        accuracy_issues += 1
                
                # Percentage columns should be between 0-100 or 0-1
                elif any(pct_word in column_lower for pct_word in ['percent', 'pct', 'rate', 'ratio']):
                    min_max = df.select(
                        F.min(col_name).alias("min_val"),
                        F.max(col_name).alias("max_val")
                    ).collect()[0]
                    
                    min_val, max_val = min_max['min_val'], min_max['max_val']
                    
                    if min_val is not None and max_val is not None:
                        # Check if values are in valid percentage ranges
                        valid_0_1 = (0 <= min_val <= 1 and 0 <= max_val <= 1)
                        valid_0_100 = (0 <= min_val <= 100 and 0 <= max_val <= 100)
                        
                        if not (valid_0_1 or valid_0_100):
                            accuracy_issues += 1
            
            # Check string columns for basic format issues
            string_columns = [
                field.name for field in schema.fields 
                if isinstance(field.dataType, StringType)
            ]
            
            for col_name in string_columns:
                column_lower = col_name.lower()
                
                # Email-like columns should have basic email format
                if any(email_word in column_lower for email_word in ['email', 'mail']):
                    # Basic email pattern check
                    invalid_emails = df.filter(
                        F.col(col_name).isNotNull() & 
                        ~F.col(col_name).rlike(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                    ).count()
                    
                    total_emails = df.filter(F.col(col_name).isNotNull()).count()
                    if total_emails > 0 and (invalid_emails / total_emails) > 0.1:  # More than 10% invalid
                        accuracy_issues += 1
            
            return 'PASS' if accuracy_issues == 0 else 'FAIL'
            
        except Exception:
            return 'FAIL'
    
    def _check_timeliness(self, df):
        """Check timeliness - date validation"""
        try:
            timeliness_issues = 0
            schema = df.schema
            
            # Get date/timestamp columns
            date_columns = [
                field.name for field in schema.fields 
                if isinstance(field.dataType, (DateType, TimestampType))
            ]
            
            current_date = datetime.now()
            future_cutoff = current_date + timedelta(days=365)
            past_cutoff = datetime(1900, 1, 1)
            
            for col_name in date_columns:
                # Check for future dates (beyond current date + 1 year)
                future_dates = df.filter(
                    F.col(col_name).isNotNull() & 
                    (F.col(col_name) > F.lit(future_cutoff))
                ).count()
                
                # Check for very old dates (before year 1900)
                old_dates = df.filter(
                    F.col(col_name).isNotNull() & 
                    (F.col(col_name) < F.lit(past_cutoff))
                ).count()
                
                if future_dates > 0 or old_dates > 0:
                    timeliness_issues += 1
            
            return 'PASS' if timeliness_issues == 0 else 'FAIL'
            
        except Exception:
            return 'FAIL'
    
    def _check_integrity(self, df):
        """Check integrity - basic referential integrity"""
        try:
            integrity_issues = 0
            schema = df.schema
            
            # Check for foreign key-like columns (columns ending with '_id')
            id_columns = [
                field.name for field in schema.fields 
                if field.name.lower().endswith('_id') and field.name.lower() != 'id'
                and isinstance(field.dataType, (IntegerType, LongType))
            ]
            
            for col_name in id_columns:
                # Check if foreign key values are reasonable (not all zeros or negative)
                non_positive_count = df.filter(
                    F.col(col_name).isNotNull() & (F.col(col_name) <= 0)
                ).count()
                
                total_non_null = df.filter(F.col(col_name).isNotNull()).count()
                
                if total_non_null > 0 and non_positive_count == total_non_null:
                    integrity_issues += 1
            
            return 'PASS' if integrity_issues == 0 else 'FAIL'
            
        except Exception:
            return 'FAIL'
    
    def process_layer(self, df, layer_name):
        """
        Process a data layer with quality checks
        Returns (overall_passed, original_spark_dataframe, results_dataframe)
        """
        # Get validation results
        results_df = self.validate_dataframe(df, layer_name)
        
        # Check if all dimensions passed
        dimensions = ['Completeness', 'Validity', 'Consistency', 'Uniqueness', 
                     'Accuracy', 'Timeliness', 'Integrity']
        
        all_passed = all(results_df[dim].iloc[0] == 'PASS' for dim in dimensions)
        
        return all_passed, df, results_df
    
    def layers_check(self, catalog, database,layer):
        results = {}
        list_of_tbl = self.spark.sql(f"SHOW TABLES IN {catalog}.{database}").select('tableName').collect()
        for tbl_nm in list_of_tbl:
            tbl= tbl_nm['tableName']
            # print(f"***********************{tbl}****************")
            spark_df = self.spark.sql(f"select * from {catalog}.{database}.{tbl}")
        
            # Process bronze layer
            bronze_passed, bronze_df, bronze_results = self.process_layer(spark_df, layer)
            results[f'{catalog}.{database}.{tbl}'] = (f"{'PASSED' if bronze_passed else 'FAILED'}",bronze_results.iloc[0].to_dict())

        return results
    
    def dq_check(self,catalog, database,layer_name):
        layer_result = self.layers_check(catalog, database,layer_name)

        # add results into table

        flattened = []
        current_time = datetime.now()

        for table_name, (overall_result, details) in layer_result.items():
            flattened.append((
                table_name.split('.')[0],
                table_name.split('.')[1],
                table_name.split('.')[2],
                details.get('Layer'),
                details.get('Completeness'),
                details.get('Validity'),
                details.get('Consistency'),
                details.get('Uniqueness'),
                details.get('Accuracy'),
                details.get('Timeliness'),
                details.get('Integrity'),
                overall_result,
                current_time
            ))

        
        # Define the schema
        schema = StructType([
            StructField("catalog_name", StringType(), True),
            StructField("schema_name", StringType(), True),
            StructField("table_name", StringType(), True),
            StructField("layer_name", StringType(), True),
            StructField("completeness", StringType(), True),
            StructField("validity", StringType(), True),
            StructField("consistency", StringType(), True),
            StructField("uniqueness", StringType(), True),
            StructField("accuracy", StringType(), True),
            StructField("timeliness", StringType(), True),
            StructField("integrity", StringType(), True),
            StructField("overall_result", StringType(), True),
            StructField("current_timestamp", TimestampType(), True)
        ])

        # Create Spark DataFrame
        spark_df = self.spark.createDataFrame(flattened, schema=schema)

        spark_df.write.mode("append").saveAsTable(f"{self.data_quality_catalog}.{self.data_quality_schema}.{self.data_quality_table}")
        print(f"Data Quality Checks are Done, check table for logs : {self.data_quality_catalog}.{self.data_quality_schema}.{self.data_quality_table}")