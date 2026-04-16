class CatalogUtils:
    @staticmethod
    def ensure_catalog_and_schema(spark, catalog_name, schema_name):
        try:
            # Check if catalog exists
            catalog_exists = any(row.catalog == catalog_name for row in spark.sql("SHOW CATALOGS").collect())
            if not catalog_exists:
                raise Exception(f"{catalog_name} doesn't exist. Please created catalog: {catalog_name}")
            else:
                print(f"Catalog '{catalog_name}' already exists.")

            if schema_name:
                schema_exists = any(
                    row.databaseName == schema_name
                    for row in spark.sql(f"SHOW SCHEMAS IN {catalog_name}").collect()
                )
                if not schema_exists:
                    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")
                    print(f"Created schema: {catalog_name}.{schema_name}")
                else:
                    print(f"Schema '{catalog_name}.{schema_name}' already exists.")
        except Exception as e:
            print(f"[CatalogUtils] Error ensuring catalog/schema: {e}")
            raise

    @staticmethod
    def ensure_log_table(spark, catalog, schema, table):
        table_exists = any(
            row.tableName == table
            for row in spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()
        )
        if not table_exists:
            print(f"Creating table: {catalog}.{schema}.{table}")
            spark.sql(f"""
                CREATE TABLE {catalog}.{schema}.{table} (
                    source STRING,
                    source_table STRING,
                    target_table STRING,
                    load_type STRING,
                    status STRING,
                    error_message STRING,
                    timestamp TIMESTAMP
                )
                USING DELTA
            """)
        else:
            print(f"Table '{catalog}.{schema}.{table}' already exists.")
