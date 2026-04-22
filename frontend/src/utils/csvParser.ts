export function parseCsv(text: string): { columns: string[]; rows: Record<string, string>[] } {
    const lines = text.split('\n').filter((line) => line.trim());
    if (lines.length === 0) return { columns: [], rows: [] };

    const parseRow = (line: string): string[] => {
        const result: string[] = [];
        let current = '';
        let inQuotes = false;
        for (let i = 0; i < line.length; i++) {
            const ch = line[i];
            if (ch === '"') {
                inQuotes = !inQuotes;
            } else if (ch === ',' && !inQuotes) {
                result.push(current.trim());
                current = '';
            } else {
                current += ch;
            }
        }
        result.push(current.trim());
        return result;
    };

    const columns = parseRow(lines[0]);
    const rows = lines.slice(1).map((line) => {
        const values = parseRow(line);
        const row: Record<string, string> = {};
        columns.forEach((col, i) => {
            row[col] = values[i] ?? '';
        });
        return row;
    });

    return { columns, rows };
}

export function generateSampleMigrationCsv(): string {
    return [
        'source_table,destination_table,schema,transformation_type,partition_column,load_frequency',
        'users,dim_users,dbo,full_load,user_id,daily',
        'orders,fact_orders,dbo,incremental,order_date,hourly',
        'products,dim_products,dbo,full_load,product_id,daily',
        'transactions,fact_transactions,dbo,incremental,created_at,hourly',
        'categories,dim_categories,dbo,full_load,category_id,weekly',
    ].join('\n');
}

export function generateSampleCredentialsCsv(): string {
    return [
        'parameter,value',
        'workspace_url,https://your-workspace.azuredatabricks.net',
        'token,dapi_your_token_here',
        'cluster_id,0123-456789-abcdef',
        'catalog,main',
        'schema,default',
    ].join('\n');
}
