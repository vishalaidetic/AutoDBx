# AutoDBx - Automated Database Migration Framework
AutoDBx is a comprehensive, automated migration framework designed to seamlessly transfer data from various database systems to Databricks using Asset Bundles. This framework supports multiple source systems including MySQL, PostgreSQL, BigQuery, Redshift, MSSQL, and more.

## Architecture Overview

The AutoDBx framework follows a modular architecture where each database migration is organized in separate folders:

```
AutoDBx/
├── bigquery_migration/
├── mssql_migration/
├── mysql_migration/
├── postgresql_migration/
├── redshift_migration/
├── snowflake_migration/
└── ... (other migration types)
```

Each migration folder contains:
- **managing_secret_scopes/**: Secret management utilities
- **resources/**: Job and dashboard YAML configurations
- **src/**: Source code and configuration files
- **databricks.yml**: Main bundle configuration

## Prerequisites

Before starting, ensure you have the following installed:
- **Python 3.8+**: Ensure Python is installed on your system
- **Git**: For cloning the repository
- **VS Code**: Recommended IDE for development
- **Databricks workspace access**: With appropriate permissions

## Getting started

1. Install the Databricks CLI from https://docs.databricks.com/dev-tools/cli/databricks-cli.html

2. Authenticate to your Databricks workspace, if you have not done so already:
    ```
    $ databricks configure
    ```

3. Install the Databricks extension for Visual Studio Code for local development from https://docs.databricks.com/dev-tools/vscode-ext.html. This extension will help you:
    - Configure your virtual environment
    - Setup Databricks Connect for running unit tests locally
    - Provide better code editing experience with syntax highlighting
    - Enable direct notebook editing and execution from VS Code

4. Clone only the specific migration folder you need instead of the entire repository:
    ```
    # Clone the repository with no checkout
    $ git clone --no-checkout https://github.com/Aidetic/AutoDBx.git
    $ cd AutoDBx
    
    # Initialize sparse-checkout
    $ git sparse-checkout init --cone
    
    # Set the specific folder you want (e.g., redshift_migration)
    $ git sparse-checkout set redshift_migration
    
    # Checkout the files
    $ git checkout main
    ```
    This will clone only the `redshift_migration` folder. Replace `redshift_migration` with your desired migration type such as:
    - `mysql_migration` for MySQL migrations
    - `bigquery_migration` for Google BigQuery migrations
    - `postgresql_migration` for PostgreSQL migrations
    - `mssql_migration` for Microsoft SQL Server migrations
    - `snowflake_migration` for Snowflake migrations
    - And so on for other supported database types

5. Navigate to the cloned migration folder:
    ```
    $ cd redshift_migration
    ```

## Step 1: Secret Scope Management

1. Set up secret scopes by navigating to the `managing_secret_scopes` folder:
    ```
    $ cd managing_secret_scopes
    ```

2. Install the required Python dependencies:
    ```
    $ pip install -r requirements.txt
    ```

3. Create a `.env` file in the `managing_secret_scopes` folder with the following structure:
    ```
    # Databricks Configuration (Keywords - Don't change these names)
    DATABRICKS_INSTANCE=https://adb-XXXXXXXXXXXXX.16.azuredatabricks.net
    DATABRICKS_TOKEN=dapi7fcXXXXXXXXXXXXXcf90f
    SCOPE_NAME=AutoDbx
    
    # Database Credentials (These will become secrets)
    mssql_user=dbXXXXXer01
    mssql_password=HbXXXXXXXXXz3
    mssql_host=10.00.0.5
    mssql_port=1000
    
    # Add other database-specific credentials as needed
    # mysql_user=your_mysql_user
    # mysql_password=your_mysql_password
    # mysql_host=your_mysql_host
    # redshift_user=your_redshift_user
    # redshift_password=your_redshift_password
    # postgres_user=your_postgres_user
    # postgres_password=your_postgres_password
    # etc.
    ```
    **Important Notes:**
    - `DATABRICKS_INSTANCE`, `DATABRICKS_TOKEN`, and `SCOPE_NAME` are treated as keywords by the framework and should not be changed
    - All other entries will be created as secrets in the Databricks secret scope
    - Replace the example values with your actual database credentials
    - Add credentials for your specific database type (MySQL, Redshift, etc.)

4. Run the secret manager to create the secret scope and populate it with your credentials:
    ```
    $ python databricks_secret_manager.py
    ```
    This script will:
    - Create a secret scope named as specified in `SCOPE_NAME`
    - Add all your database credentials as secrets within that scope
    - Validate the connection to Databricks using your token

## Step 2: Configure Databricks Bundle

1. Navigate back to the root of your migration folder:
    ```
    $ cd ..
    ```

2. Update the `databricks.yml` file with your workspace details:
    - Open `databricks.yml` in your preferred editor
    - Update `workspace_host` with your Databricks workspace URL
    - Update `warehouse_id` with your SQL warehouse ID
    
    Example configuration:
    ```yaml
    workspace:
      host: https://adb-242XXXXXXXXXXXXX6.16.azuredatabricks.net
    
    targets:
      dev:
        default: true
        compute_id: your-sql-warehouse-id
    ```

## Step 3: Configure Migration Parameters

1. Configure your migration parameters by navigating to the database-specific folder:
    ```
    $ cd src/redshift  # Replace 'redshift' with your database type (mysql, bigquery, etc.)
    ```

2. Update the configuration files in the `util` folder:
    
    **a) Edit `util/config.csv`:**
    - This file defines which tables/data to migrate from your source database
    - Update the configuration according to your migration requirements
    - **Critical: Do not change the CSV structure/column headers**
    - Only modify the data rows with your specific table and migration details
    - Each row represents a table or dataset to be migrated
    
    **b) Edit `util/parameters.yml`:**
    - Update `catalog_name` with an existing catalog in your Databricks workspace
    - Update schema names for Bronze, Silver, and Gold layers (will be created if they don't exist)
    - Update secret scope references to match your setup
    - Ensure all parameters align with your Databricks environment
    
    Example `parameters.yml`:
    ```yaml
    catalog_name: "your_existing_catalog"
    schema_names:
      bronze: "bronze_schema"
      silver: "silver_schema"
      gold: "gold_schema"
    secret_scope: "AutoDbx"
    source_database: "your_source_db"
    ```
    
    **Critical Requirements:**
    - The catalog specified in `catalog_name` **must already exist** in your Databricks workspace
    - Schemas will be created automatically during migration if they don't exist
    - Secret scope name must match what you created in Step 1

## Step 4: Validation and Deployment

1. Navigate back to the migration root folder:
    ```
    $ cd ../..
    ```

2. Validate your bundle configuration to check for any errors:
    ```
    $ databricks bundle validate
    ```
    This command will verify:
    - YAML syntax correctness
    - Resource configurations
    - Dependencies and references
    - Access permissions

3. Deploy a development copy of this project:
    ```
    $ databricks bundle deploy --target dev
    ```
    (Note that "dev" is the default target, so the `--target` parameter is optional here.)
    
    This deployment will:
    - Create all job definitions in your Databricks workspace
    - Deploy dashboard configurations
    - Set up the necessary compute resources
    - Configure job dependencies and schedules
    
    You can find the deployed jobs by opening your workspace and clicking on **Workflows**.

4. Similarly, to deploy a production copy, type:
    ```
    $ databricks bundle deploy --target prod
    ```
    Note that production deployments may have different configurations such as larger cluster sizes, different schedules, or enhanced monitoring.

## Step 5: Execute Migration Jobs

1. After deployment, first create the configuration table from your CSV file:
    ```
    $ databricks bundle run config_table_creation
    ```
    This command will:
    - Read your `config.csv` file
    - Create a configuration table in Databricks
    - Validate the configuration entries
    - Prepare the migration metadata

2. Run the main migration job:
    ```
    $ databricks bundle run migration_job
    ```
    
    The migration job consists of 4 tasks that run sequentially:
    - **main_task (Migration)**: Performs the actual data migration from source to Databricks.
    - **validation_task (Data Validation)**: Validates data integrity, row counts, and schema consistency between source and target systems.
    - **data_quality_task (Quality Checks)**: Performs comprehensive data quality checks including null checks, duplicate detection, and business rule validation.
    - **logging_task (Audit Logging)**: Stores detailed table-level and job-level execution logs for monitoring and compliance.

## Migration Architecture Details

Each migration also includes:
- **ACID transactions** using Delta Lake
- **Schema evolution** support
- **Time travel** capabilities for data recovery
- **Automated data quality monitoring**
- **Cost tracking and optimization**

## Supported Migration Types

- **MySQL → Databricks** (`mysql_migration`)
- **PostgreSQL → Databricks** (`postgresql_migration`)
- **Microsoft SQL Server → Databricks** (`mssql_migration`)
- **Amazon Redshift → Databricks** (`redshift_migration`)
- **Google BigQuery → Databricks** (`bigquery_migration`)
- **Snowflake → Databricks** (`snowflake_migration`)
- **etc

## Monitoring and Troubleshooting

### View Job Execution
- Navigate to your Databricks workspace
- Go to **Workflows** section
- Look for jobs with prefix `[dev]` or `[prod]` depending on your deployment target
- Monitor real-time execution progress and logs

### Check Migration Logs
- Job execution logs are available in the Databricks job runs interface
- Table-level migration logs are stored by the logging_task in your Gold schema
- Use the deployed dashboards for visual monitoring of migration progress
- Access detailed error logs and performance metrics through the Databricks UI

### Common Issues and Solutions

1. **Secret Scope Issues**: 
   - Verify `.env` file is properly formatted with correct syntax
   - Ensure `databricks_secret_manager.py` ran successfully without errors
   - Check Databricks permissions for secret scope creation

2. **Catalog Not Found Error**: 
   - Verify the catalog specified in `parameters.yml` exists in your Databricks workspace
   - Ensure you have proper permissions to access the catalog
   - Create the catalog manually if it doesn't exist

3. **Database Connection Issues**: 
   - Verify database credentials in the secret scope are correct
   - Test network connectivity from Databricks to your source database
   - Check firewall and security group configurations

4. **Bundle Validation Errors**: 
   - Review `databricks.yml` configuration for syntax errors
   - Verify workspace URL and warehouse ID are correct
   - Ensure all referenced resources exist

5. **Configuration File Issues**:
   - Verify `config.csv` follows the exact structure without modifying headers
   - Check `parameters.yml` for proper YAML syntax
   - Ensure all required fields are populated

### Performance Optimization Tips

- Monitor cluster utilization during migration
- Adjust cluster size based on data volume
- Use partitioning strategies for large tables
- Implement incremental loading for ongoing synchronization

## Security Best Practices

- Store all sensitive credentials only in Databricks secret scopes, never in code or configuration files
- Use service accounts for production deployments rather than personal accounts
- Regularly rotate access tokens and database passwords
- Implement proper access controls and permissions on Databricks workspaces
- Review and audit secret scope access regularly
- Use network security groups to restrict database access

## Advanced Configuration

For advanced users, you can customize:
- Cluster configurations in the job YAML files
- Custom transformation logic in the notebook files
- Data quality rules and thresholds
- Monitoring and alerting configurations
- Custom dashboard layouts and metrics

When not using VS Code with Databricks extension, consult your development environment's documentation and/or the documentation for Databricks Connect for manually setting up your environment (https://docs.databricks.com/en/dev-tools/databricks-connect/python/index.html).

## Support and Documentation

- **Databricks Asset Bundles**: https://docs.databricks.com/dev-tools/bundles/
- **Databricks CLI**: https://docs.databricks.com/dev-tools/cli/
- **Delta Lake Documentation**: https://docs.delta.io/
- **Medallion Architecture**: https://www.databricks.com/glossary/medallion-architecture

For additional support, refer to the Databricks documentation or contact your system administrator.
