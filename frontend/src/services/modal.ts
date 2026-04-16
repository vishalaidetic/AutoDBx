export interface Catalog {
    name: string;
    owner: string;
    storage_root?: string;
    enable_auto_maintenance?: string;
    enable_predictive_optimization?: string;
    catalog_type: string;
    metastore_id: string;
    created_at: number;
    created_by: string;
    updated_at: number;
    updated_by: string;
    storage_location?: string;
    isolation_mode: string;
    accessible_in_current_workspace: boolean;
    effective_auto_maintenance_flag?: {
      value: string;
      inherited_from_type: string;
      inherited_from_name: string;
    };
    effective_predictive_optimization_flag?: {
      value: string;
      inherited_from_type: string;
      inherited_from_name: string;
    };
    browse_only: boolean;
    id: string;
    full_name: string;
    securable_type: string;
    securable_kind: string;
    resource_name: string;
    metastore_version: number;
    comment?: string;
    delta_sharing_valid_through_timestamp?: number;
    [key: string]: any;
  }



  // New Schema Interface
  export interface Schema {
    name: string;
    catalog_name: string;
    owner: string;
    comment?: string;
    enable_auto_maintenance?: string;
    enable_predictive_optimization?: string;
    metastore_id: string;
    full_name: string;
    created_at: number;
    created_by: string;
    updated_at: number;
    updated_by: string;
    catalog_type: string;
    effective_auto_maintenance_flag?: {
      value: string;
      inherited_from_type: string;
      inherited_from_name: string;
    };
    effective_predictive_optimization_flag?: {
      value: string;
      inherited_from_type: string;
      inherited_from_name: string;
    };
    schema_id: string;
    securable_type: string;
    securable_kind: string;
    browse_only: boolean;
    metastore_version: number;
    [key: string]: any;
  }

   // Table and Column interfaces for Databricks tables
   export interface DatabricksTableColumn {
    name: string;
    type_text?: string;
    type_name?: string;
    position?: number;
    type_precision?: number;
    type_scale?: number;
    type_json?: string;
    comment?: string;
    nullable?: boolean;
    column_masks?: Record<string, unknown>;
    // Allow extra fields for flexibility
    [key: string]: any;
  }

  export interface DatabricksTable {
    name: string;
    catalog_name: string;
    schema_name: string;
    table_type: string;
    columns?: DatabricksTableColumn[];
    view_definition?: string;
    owner?: string;
    comment?: string;
    properties?: Record<string, any>;
    securable_kind?: string;
    properties_pairs?: Record<string, unknown>;
    generation?: number;
    metastore_id?: string;
    full_name?: string;
    data_access_configuration_id?: string;
    created_at?: number;
    created_by?: string;
    updated_at?: number;
    updated_by?: string;
    table_id?: string;
    delta_runtime_properties_kvpairs?: Record<string, unknown>;
    securable_type?: string;
    browse_only?: boolean;
    metastore_version?: number;
    schema_id?: string;
    catalog_id?: string;
    row_filters?: Record<string, unknown>;
    // Some tables may have additional fields
    [key: string]: any;
  }


  // Make all fields optional and allow extra fields for flexibility
  export interface DatabricksTableDetailsColumn {
    name?: string;
    type_text?: string;
    type_name?: string;
    position?: number;
    type_precision?: number;
    type_scale?: number;
    type_json?: string;
    comment?: string;
    nullable?: boolean;
    column_masks?: Record<string, unknown>;
    // Allow extra fields for flexibility
    [key: string]: any;
  }
  
  export interface DatabricksTableDetails {
    name?: string;
    catalog_name?: string;
    schema_name?: string;
    table_type?: string;
    data_source_format?: string;
    columns?: DatabricksTableDetailsColumn[];
    storage_location?: string;
    owner?: string;
    properties?: Record<string, any>;
    securable_kind?: string;
    enable_auto_maintenance?: string;
    enable_predictive_optimization?: string;
    properties_pairs?: Record<string, unknown>;
    generation?: number;
    metastore_id?: string;
    full_name?: string;
    data_access_configuration_id?: string;
    created_at?: number;
    created_by?: string;
    updated_at?: number;
    updated_by?: string;
    table_id?: string;
    delta_runtime_properties_kvpairs?: Record<string, unknown>;
    securable_type?: string;
    effective_auto_maintenance_flag?: Record<string, unknown>;
    effective_predictive_optimization_flag?: Record<string, unknown>;
    browse_only?: boolean;
    encryption_details?: Record<string, unknown>;
    metastore_version?: number;
    schema_id?: string;
    catalog_id?: string;
    row_filters?: Record<string, unknown>;
    view_definition?: string;
    view_dependencies?: Record<string, unknown>;
    comment?: string;
    // Allow extra fields for flexibility
    [key: string]: any;
  }

// New interfaces for table data
export interface DatabricksTableDataResponse {
    columns: string[]; // Array of column names
    data: Record<string, any>[]; // Array of row objects, where keys are column names
  }