import requests
import json

class RowLevelPrivilegeManager:
    def __init__(self, groups_config, table_name, function_name, col_name, col_type, 
                 account_id, databricks_account_url, account_api_token, spark):
        self.groups_config = groups_config
        self.table_name = table_name
        self.function_name = function_name
        self.col_name = col_name
        self.col_type = col_type
        self.account_id = account_id
        self.databricks_account_url = databricks_account_url
        self.account_api_token = account_api_token
        self.spark = spark
        
        # Parse catalog/schema/table
        self.catalog, self.schema, self.table = table_name.split(".")
        
        # Set headers
        self.headers = {"Authorization": f"Bearer {account_api_token}", "Content-Type": "application/json"}
    
    def get_group_id(self, group_name):
        url = f"https://accounts.cloud.databricks.com/api/2.0/accounts/{self.account_id}/scim/v2/Groups"
        response = requests.get(url, headers=self.headers, params = {"filter": f"displayName eq {group_name}"} )
        resources = response.json().get("Resources", [])
        if resources:
            return resources[0]["id"]
        return None

    def create_group(self, group_name):
        url = f"https://accounts.cloud.databricks.com/api/2.0/accounts/{self.account_id}/scim/v2/Groups"
        payload = {"displayName": group_name}
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code == 201:
            return response.json()["id"]
        raise Exception(f"Failed to create group: {response.text}")

    def add_user_to_group(self, group_id, user_email):
        # Find user by email
        url = f"https://accounts.cloud.databricks.com/api/2.0/accounts/{self.account_id}/scim/v2/Users?filter=userName eq \"{user_email}\""
        user_resp = requests.get(url, headers=self.headers)
        users = user_resp.json().get("Resources", [])
        if not users:
            raise Exception(f"User {user_email} not found in account.")
        user_id = users[0]["id"]

        # Check & Add user to group
        group_url = f"https://accounts.cloud.databricks.com/api/2.0/accounts/{self.account_id}/scim/v2/Groups/{group_id}"

        group_resp = requests.get(group_url, headers=self.headers)
        group_members = group_resp.json().get("members", [])

        if any(member.get("value") == user_id for member in group_members):
            print(f" User `{user_email}` already exist.")
            return 

        payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "add",
                "path": "members",
                "value": [{"value": user_id}]
            }]
        }
        response = requests.patch(group_url, headers=self.headers, data=json.dumps(payload))
        print(f"User `{user_email}` added.")
        if response.status_code != 200:
            raise Exception(f"Failed to add user to group: {response.text}")
        
    def execute_creation(self, group_name, user_names):
        group_id = self.get_group_id(group_name)
        if not group_id:
            print(f"Group '{group_name}' not found. Creating...")
            group_id = self.create_group(group_name)
            print(f"{group_name} created successfully. ")
        else:
            print(f"Group '{group_name}' already exists.")

        # add users to group
        user_list = user_names.split(",")
        for user_email in user_list:
            print(f"Start Adding user '{user_email}' to group '{group_name}' ---> ",end="")
            self.add_user_to_group(group_id, user_email.strip())
        
        # The End #
        print(f"******Process done for Group - {group_name}. ********")

    def function_exists(self, function_name, catalog, schema):
        print("check if function exist or not -->")
        result = self.spark.sql(f""" SELECT routine_definition FROM system.information_schema.routines WHERE specific_catalog = '{catalog}' and specific_schema = '{schema}' and specific_name = '{function_name}' """)
        return result.first()

    def get_function_definition(self, function_name, catalog, schema):
        result = self.spark.sql(f""" SELECT routine_definition FROM system.information_schema.routines WHERE specific_catalog = '{catalog}' and specific_schema = '{schema}' and specific_name = '{function_name}' """)
        definition = result.first()['routine_definition']
        return definition

    def build_condition(self, groups_config, column):
        condition = ''
        for group_name, group_config in groups_config.items():
            col_values = group_config['column_values'].split(",")
            for col_val in col_values:
                condition += f"(is_account_group_member('{group_name}') AND {column} = '{col_val.strip()}')" + ' OR '
        return condition.strip(' OR ')

    def function_created(self, fq_function, condition, col_name, col_type):
        create_sql = f"""
        CREATE OR REPLACE FUNCTION {fq_function}({col_name} {col_type})
        RETURNS BOOLEAN
        RETURN ({condition});
        """
        print(create_sql)
        self.spark.sql(create_sql)
        print("Completed the process.")

    def prepare_complete_condition(self, existing_def, new_def):
        overall_cond = existing_def[1:-1]
        print(overall_cond)
        for i in new_def.split('OR'):
            if i.strip() in existing_def:
                continue
            else:
                overall_cond = overall_cond + ' OR '+ i.strip()
        print(overall_cond)
        return overall_cond

    def apply_row_filter(self, table_name, fq_function, col_name):
        alter_sql = f"""
        ALTER TABLE {table_name}
        SET ROW FILTER {fq_function}
        ON ({col_name});
        """
        print(alter_sql)
        self.spark.sql(alter_sql)
        print(f"Row filter applied to {table_name} using {fq_function}.")

    def create_groups_and_users(self):
        """Create groups and add users to respective groups"""
        for group_name, group_config in self.groups_config.items():
            user_names = group_config['users']
            self.execute_creation(group_name, user_names)

    def create_function_and_apply_filter(self):
        """Create/update function and apply row filter"""
        self.spark.sql(f"use catalog {self.catalog}")
        
        fq_function = f"{self.catalog}.{self.schema}.{self.function_name}"

        if self.function_exists(self.function_name, self.catalog, self.schema):
            print(f"Function {fq_function} exists. Dropping and recreating it.")
            # Drop existing function to avoid column name conflicts
            self.spark.sql(f"DROP FUNCTION IF EXISTS {fq_function}")
        
        print(f"Creating function {fq_function}.")
        condition = self.build_condition(self.groups_config, f"`{self.col_name}`")
        self.function_created(fq_function, condition, self.col_name, self.col_type)
        
        print("*********Applying filtering******")
        self.apply_row_filter(self.table_name, fq_function, self.col_name)

        print("****The End********")

    def execute_main(self):
        """Main execution method"""
        print("Starting Row Level Privilege Setup...")
        
        # Step 1: Create groups and add users
        print("=== Creating Groups and Adding Users ===")
        self.create_groups_and_users()
        
        # Step 2: Create function and apply row filter
        print("=== Creating Function and Applying Row Filter ===")
        self.create_function_and_apply_filter()
        
        print("Row Level Privilege Setup Completed Successfully!")