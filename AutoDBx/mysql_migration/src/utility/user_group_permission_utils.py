import requests
import json

class UserGroupPermissionManager:
    def __init__(self, user_names, group_name, table_name, permissions, flag,
                 account_id, databricks_account_url, account_api_token, spark):
        self.user_names = user_names
        self.group_name = group_name
        self.table_name = table_name
        self.permissions = permissions
        self.flag = flag
        self.account_id = account_id
        self.databricks_account_url = databricks_account_url
        self.account_api_token = account_api_token
        self.spark = spark
        
        # Set headers
        self.headers = {"Authorization": f"Bearer {account_api_token}", "Content-Type": "application/json"}
        
        # Validate required parameters
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate required parameters"""
        if not self.user_names:
            raise ValueError("Missing user_names parameter")
        if not self.group_name:
            raise ValueError("Missing group_name parameter")
    
    def get_group_id(self, group_name):
        """Get group ID by group name"""
        url = f"https://accounts.cloud.databricks.com/api/2.0/accounts/{self.account_id}/scim/v2/Groups"
        response = requests.get(url, headers=self.headers, params = {"filter": f"displayName eq {group_name}"} )
        resources = response.json().get("Resources", [])
        if resources:
            return resources[0]["id"]
        return None

    def create_group(self, group_name):
        """Create a new group"""
        url = f"https://accounts.cloud.databricks.com/api/2.0/accounts/{self.account_id}/scim/v2/Groups"
        payload = {"displayName": group_name}
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code == 201:
            return response.json()["id"]
        raise Exception(f"Failed to create group: {response.text}")

    def add_user_to_group(self, group_id, user_email):
        """Add user to group"""
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

    def grant_permission(self, table_name, principal, permission):
        """Grant permission on table to principal (user or group)"""
        query = f"GRANT {permission} ON TABLE {table_name} TO `{principal}`;"
        self.spark.sql(query)
        print(f"Permission granted to `{principal}`. ")

    def create_group_and_add_users(self):
        """Create group if it doesn't exist and add users to it"""
        group_id = self.get_group_id(self.group_name)
        if not group_id:
            print(f"Group '{self.group_name}' not found. Creating...")
            group_id = self.create_group(self.group_name)
            print(f"{self.group_name} created successfully. ")
        else:
            print(f"Group '{self.group_name}' already exists.")

        # Add users to group
        user_list = self.user_names.split(",")
        for user_email in user_list:
            print(f"Start Adding user '{user_email}' to group '{self.group_name}' ---> ", end="")
            self.add_user_to_group(group_id, user_email.strip())
        
        return user_list

    def grant_table_permissions(self, user_list):
        """Grant permissions on table based on flag"""
        if self.permissions == '' and self.table_name == '' and self.flag == '':
            print("No permission need to grant")
            return

        # Grant permission to table
        if self.flag.lower() == 'group':
            self.grant_permission(self.table_name, self.group_name, self.permissions)
        else:
            for user_email in user_list:
                self.grant_permission(self.table_name, user_email.strip(), self.permissions)

    def execute_main(self):
        """Main execution method"""
        print("Starting User Group Permission Setup...")
        
        # Step 1: Create group and add users
        print("=== Creating Group and Adding Users ===")
        user_list = self.create_group_and_add_users()
        
        # Step 2: Grant table permissions
        print("=== Granting Table Permissions ===")
        self.grant_table_permissions(user_list)
        
        print("******The End ********")
        print("User Group Permission Setup Completed Successfully!")