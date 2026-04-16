from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType
from sqlglot import expressions as exp
import sqlglot
import os
import sys
import traceback
import pandas as pd
from datetime import datetime


class SQLMigrationProcessor:
    """
    A class to handle SQL migration and transformation using SQLGlot and PySpark
    """
    
    def __init__(self, spark, dbutils, source_query_folder, output_folder, table_mapping_table, src_database, target_database='spark'):
        """
        Initialize the SQL Migration Processor
        
        Args:
            spark: Spark session object
            dbutils: Databricks utilities object
            source_query_folder: Folder containing SQL files to process
            output_folder: Folder to store the output CSV
            table_mapping_table: Table containing table mapping configuration
            src_database: Source database type (e.g., 'mysql', 'postgresql', 'oracle', etc.)
            target_database: Target database type (default: 'spark')
        """
        self.spark = spark
        self.dbutils = dbutils
        self.source_query_folder = source_query_folder
        self.output_folder = output_folder
        self.table_mapping_table = table_mapping_table
        self.src_database = src_database
        self.target_database = target_database
        self.output_csv_path = os.path.join(output_folder, "migration_results.csv")
        self.processed_results = []
        self.next_id = 1
        
    def ensure_directory_exists(self, directory_path):
        """Ensure the directory exists"""
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            print(f"Created directory: {directory_path}")

    def get_table_mapping(self, df, key_col, catalog_col, schema_col, table_col):
        """Build table mapping dictionary from DataFrame"""
        return {
            row[key_col]: {
                "catalog": row[catalog_col],
                "schema": row[schema_col],
                "table": row[table_col]
            }
            for row in df.collect()
        }

    def get_cte_names(self, expression):
        """Extract CTE names from the query expression"""
        cte_names = set()
        
        # Find all WITH clauses (CTEs)
        for with_clause in expression.find_all(exp.With):
            for cte in with_clause.expressions:
                if hasattr(cte, 'alias') and cte.alias:
                    cte_names.add(cte.alias)
                elif hasattr(cte, 'this') and hasattr(cte.this, 'name'):
                    cte_names.add(cte.this.name)
        
        # Also check for CTE definitions in the expression itself
        for cte in expression.find_all(exp.CTE):
            if hasattr(cte, 'alias') and cte.alias:
                cte_names.add(cte.alias)
            elif hasattr(cte, 'this') and hasattr(cte.this, 'name'):
                cte_names.add(cte.this.name)
        
        return cte_names

    def qualify_tables(self, expression, table_mapping):
        """Qualify table names using config mapping"""
        def qualify_node(node):
            if isinstance(node, exp.Table):
                table_name = node.name
                if table_name in table_mapping:
                    info = table_mapping[table_name]
                    return exp.Table(
                        this=exp.to_identifier(info["table"]),
                        db=exp.to_identifier(info["schema"]),
                        catalog=exp.to_identifier(info["catalog"]),
                        alias=node.args.get("alias")
                    )
            return node
        return expression.transform(qualify_node)

    def extract_table_name_from_insert(self, expression):
        """Extract table name from INSERT expression"""
        insert_table_name = None
        
        try:
            if hasattr(expression, 'this') and expression.this:
                table_expr = expression.this
                
                if hasattr(table_expr, 'name'):
                    insert_table_name = table_expr.name
                elif hasattr(table_expr, 'this') and hasattr(table_expr.this, 'name'):
                    insert_table_name = table_expr.this.name
                elif hasattr(table_expr, 'this'):
                    table_str = str(table_expr.this)
                    if table_str and table_str != 'None':
                        insert_table_name = table_str
                else:
                    table_str = str(table_expr)
                    if table_str and table_str != 'None':
                        insert_table_name = table_str
                
                if not insert_table_name and isinstance(table_expr, exp.Table):
                    insert_table_name = table_expr.name
                
                if not insert_table_name:
                    tables = list(expression.find_all(exp.Table))
                    if tables:
                        insert_table_name = tables[0].name
                
        except Exception as e:
            pass
        
        return insert_table_name

    def handle_query(self, query: str, df, source_file):
        """Handle individual query transformation"""
        try:
            # First, try to transpile the query from source to target dialect
            transpiled_queries = sqlglot.transpile(
                query, 
                read=self.src_database, 
                write=self.target_database,
                pretty=True
            )
            
            if not transpiled_queries:
                return None, "Failed to transpile query - no output generated"
            
            # Get the first transpiled query
            transpiled_query = transpiled_queries[0]
            
            # Now parse the transpiled query for table mapping
            expression = sqlglot.parse_one(transpiled_query, dialect=self.target_database)
            
        except Exception as e:
            return None, f"Failed to transpile/parse query: {str(e)}"

        source_tables = {row["source_table"] for row in df.select("source_table").distinct().collect()}
        target_tables = {row["target_table"] for row in df.select("target_table").distinct().collect()}
        used_table_names = {t.name for t in expression.find_all(exp.Table) if t.name}
        
        # Get CTE names to exclude from table mapping validation
        cte_names = self.get_cte_names(expression)
        if cte_names:
            print(f"Found CTEs: {cte_names}")

        if not used_table_names:
            return None, "No table found in query"

        # Handle CREATE TABLE statements
        if isinstance(expression, exp.Create):
            create_table_name = None
            try:
                if hasattr(expression, 'this') and expression.this:
                    if hasattr(expression.this, 'name'):
                        create_table_name = expression.this.name
                    elif hasattr(expression.this, 'this'):
                        create_table_name = str(expression.this.this)
                    elif isinstance(expression.this, str):
                        create_table_name = expression.this
                
                if not create_table_name:
                    tables = list(expression.find_all(exp.Table))
                    if tables:
                        create_table_name = tables[0].name
                        
                if not create_table_name:
                    identifiers = list(expression.find_all(exp.Identifier))
                    if identifiers:
                        create_table_name = str(identifiers[0])
                        
            except Exception as e:
                return None, f"Error extracting CREATE table name: {str(e)}"
            
            if not create_table_name:
                return None, "Could not extract table name from CREATE statement"
                
            if create_table_name not in target_tables:
                return None, f"Table '{create_table_name}' not present in config"

            # Exclude CTE names from source table validation
            source_table_names = used_table_names - {create_table_name} - cte_names
            missing_sources = [t for t in source_table_names if t not in source_tables | target_tables]
            if missing_sources:
                return None, f"Missing source tables in config: {', '.join(missing_sources)}"

            target_mapping = self.get_table_mapping(df, "target_table", "target_catalog", "target_schema", "target_table")
            source_mapping = self.get_table_mapping(df, "source_table", "source_catalog", "source_schema", "source_table")

            expression = self.qualify_tables(expression, target_mapping)
            expression = self.qualify_tables(expression, source_mapping)

        # Handle INSERT INTO statements
        elif isinstance(expression, exp.Insert):
            insert_table_name = self.extract_table_name_from_insert(expression)
            
            if not insert_table_name:
                return None, "Could not extract table name from INSERT statement"
                
            if insert_table_name not in target_tables:
                return None, f"Table '{insert_table_name}' not present in config"

            # Exclude CTE names from source table validation
            source_table_names = used_table_names - {insert_table_name} - cte_names
            missing_sources = [t for t in source_table_names if t not in source_tables | target_tables]
            if missing_sources:
                return None, f"Missing source tables in config: {', '.join(missing_sources)}"

            target_mapping = self.get_table_mapping(df, "target_table", "target_catalog", "target_schema", "target_table")
            source_mapping = self.get_table_mapping(df, "source_table", "source_catalog", "source_schema", "source_table")

            expression = self.qualify_tables(expression, target_mapping)
            expression = self.qualify_tables(expression, source_mapping)

        else:
            # Handle other statements (SELECT, UPDATE, DELETE, etc.)
            # Exclude CTE names from source table validation
            tables_to_validate = used_table_names - cte_names
            missing_sources = [t for t in tables_to_validate if t not in source_tables]
            if missing_sources:
                return None, f"Missing source tables in config: {', '.join(missing_sources)}"

            source_mapping = self.get_table_mapping(df, "source_table", "source_catalog", "source_schema", "source_table")
            expression = self.qualify_tables(expression, source_mapping)

        try:
            converted_sql = expression.sql(dialect=self.target_database, pretty=True)
            return converted_sql, None
        except Exception as e:
            return None, f"Error generating SQL: {str(e)}"

    def read_file_content(self, file_path):
        """Read file content from workspace path"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def parse_sql_queries(self, content):
        """Parse SQL content into individual queries"""
        if not content:
            return []
        
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        
        queries = []
        current_query = ""
        in_string = False
        string_char = None
        
        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()
            
            if not stripped or stripped.startswith("--"):
                continue
            
            current_query += line + "\n"
            
            for char in stripped:
                if char in ("'", '"') and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
                elif char == ';' and not in_string:
                    queries.append(current_query.strip())
                    current_query = ""
                    break
        
        if current_query.strip():
            queries.append(current_query.strip())
        
        return [q for q in queries if q.strip()]

    def process_file(self, file_path, file_name, table_mapping_df):
        """Process a single SQL file"""
        print(f"Processing file: {file_name}")
        
        content = self.read_file_content(file_path)
        if not content:
            print(f"Could not read content from {file_name}")
            return
        
        queries = self.parse_sql_queries(content)
        print(f"Found {len(queries)} queries in {file_name}")
        
        for query_idx, query in enumerate(queries, 1):
            if not query.strip():
                continue
            
            conversion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            record_id = self.next_id
            self.next_id += 1
            
            try:
                converted_sql, error_message = self.handle_query(query, table_mapping_df, file_name)
                
                if converted_sql:
                    # Successful conversion
                    result_record = {
                        'id': record_id,
                        'src': self.src_database,
                        'source_query_file': file_name,
                        'source_query': query,
                        'converted_query': converted_sql,
                        'exception_message': '',
                        'Flag': 'C',
                        'conversion_time': conversion_time
                    }
                    print(f"Query {query_idx} converted successfully")
                else:
                    # Failed conversion
                    result_record = {
                        'id': record_id,
                        'src': self.src_database,
                        'source_query_file': file_name,
                        'source_query': query,
                        'converted_query': '',
                        'exception_message': error_message,
                        'Flag': 'E',
                        'conversion_time': conversion_time
                    }
                    print(f"Query {query_idx} failed: {error_message}")
                
                self.processed_results.append(result_record)
                
            except Exception as e:
                # Unexpected error
                result_record = {
                    'id': record_id,
                    'src': self.src_database,
                    'source_query_file': file_name,
                    'source_query': query,
                    'converted_query': '',
                    'exception_message': f"Unexpected error: {str(e)}",
                    'Flag': 'E',
                    'conversion_time': conversion_time
                }
                self.processed_results.append(result_record)
                print(f"Query {query_idx} failed with unexpected error: {str(e)}")

    def get_existing_processed_files(self):
        """Get list of already processed files from existing CSV and set next ID"""
        if not os.path.exists(self.output_csv_path):
            self.next_id = 1
            return set()
        
        try:
            existing_df = pd.read_csv(self.output_csv_path)
            processed_files = set(existing_df['source_query_file'].unique())
            
            # Set next ID based on existing records
            if len(existing_df) > 0:
                max_id = existing_df['id'].max()
                self.next_id = max_id + 1
            else:
                self.next_id = 1
                
            print(f"Found {len(processed_files)} already processed files")
            print(f"Next ID will start from: {self.next_id}")
            return processed_files
        except Exception as e:
            print(f"Error reading existing CSV: {e}")
            self.next_id = 1
            return set()

    def save_results_to_csv(self):
        """Save processed results to CSV file"""
        if not self.processed_results:
            print("No results to save")
            return
        
        # Ensure output directory exists
        self.ensure_directory_exists(self.output_folder)
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(self.processed_results)
        
        # Append to existing CSV or create new one
        if os.path.exists(self.output_csv_path):
            results_df.to_csv(self.output_csv_path, mode='a', header=False, index=False)
            print(f"Appended {len(self.processed_results)} records to existing CSV")
        else:
            results_df.to_csv(self.output_csv_path, mode='w', header=True, index=False)
            print(f"Created new CSV with {len(self.processed_results)} records")
        
        print(f"Results saved to: {self.output_csv_path}")

    def validate_configuration(self, table_mapping_df):
        """Validate configuration"""
        required_columns = ["source_table", "source_catalog", "source_schema", 
                           "target_table", "target_catalog", "target_schema"]
        
        actual_columns = table_mapping_df.columns
        missing_columns = [col for col in required_columns if col not in actual_columns]
        
        if missing_columns:
            print(f"Missing required columns in table mapping: {missing_columns}")
            return False
        
        row_count = table_mapping_df.count()
        print(f"Table mapping configuration loaded with {row_count} entries")
        return True

    def run(self):
        """Main execution method"""
        try:
            print("Starting SQL Migration Process")
            print("=" * 60)
            print(f"Source Database: {self.src_database}")
            print(f"Target Database: {self.target_database}")
            
            # Load table mapping configuration
            print("Loading table mapping configuration...")
            table_mapping_df = self.spark.read.table(self.table_mapping_table)
            
            if not self.validate_configuration(table_mapping_df):
                print("Configuration validation failed. Exiting.")
                return
            
            # Check if source query folder exists
            if not os.path.exists(self.source_query_folder):
                print(f"Source query folder not found: {self.source_query_folder}")
                return
            
            # Get list of SQL files in source folder
            sql_files = [f for f in os.listdir(self.source_query_folder) 
                        if f.endswith(('.txt', '.sql'))]
            
            if not sql_files:
                print(f"No SQL files found in {self.source_query_folder}")
                return
            
            print(f"Found {len(sql_files)} SQL files")
            
            # Get already processed files
            processed_files = self.get_existing_processed_files()
            
            # Filter out already processed files
            files_to_process = [f for f in sql_files if f not in processed_files]
            
            if not files_to_process:
                print("All files have already been processed")
                return
            
            print(f"Processing {len(files_to_process)} new files")
            
            # Process each file
            for file_idx, file_name in enumerate(files_to_process, 1):
                try:
                    print(f"\nProcessing file {file_idx}/{len(files_to_process)}: {file_name}")
                    print("-" * 40)
                    
                    file_path = os.path.join(self.source_query_folder, file_name)
                    self.process_file(file_path, file_name, table_mapping_df)
                    
                except Exception as e:
                    print(f"Error processing file {file_name}: {e}")
                    traceback.print_exc()
            
            # Save all results to CSV
            self.save_results_to_csv()
            
            print("\nSQL Migration Process Completed!")
            print("=" * 60)
            
            # Print summary
            if self.processed_results:
                successful = sum(1 for r in self.processed_results if r['Flag'] == 'C')
                failed = sum(1 for r in self.processed_results if r['Flag'] == 'E')
                print(f"Summary: {successful} successful conversions, {failed} failed conversions")
            
        except Exception as e:
            print(f"Fatal error in main execution: {e}")
            traceback.print_exc()
