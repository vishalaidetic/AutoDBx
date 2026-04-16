#!/usr/bin/env python3
"""
Databricks Secrets Manager
Manages Databricks secret scopes and secrets using local environment variables.
"""

import os
import requests
from dotenv import load_dotenv
import json

class DatabricksSecretsManager:
    def __init__(self):
        """Initialize the Databricks Secrets Manager."""
        load_dotenv()
        
        self.databricks_instance = os.getenv('DATABRICKS_INSTANCE')
        self.token = os.getenv('DATABRICKS_TOKEN')
        
        if not self.databricks_instance or not self.token:
            raise ValueError("DATABRICKS_INSTANCE and DATABRICKS_TOKEN must be set in .env file")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Reserved environment variables that should not be synced as secrets
        self.reserved_vars = {
            'DATABRICKS_INSTANCE', 'DATABRICKS_TOKEN', 'SCOPE_NAME'
        }
    
    def create_scope(self, scope_name, initial_manage_principal="users"):
        """
        Create a new secret scope in Databricks.
        
        Args:
            scope_name (str): Name of the scope to create
            initial_manage_principal (str): Who can manage secrets (default: "users")
        
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.databricks_instance}/api/2.0/secrets/scopes/create"
        
        payload = {
            "scope": scope_name,
            "initial_manage_principal": initial_manage_principal
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                print(f"Scope '{scope_name}' created successfully.")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"Scope '{scope_name}' already exists.")
                return True
            else:
                print(f"Failed to create scope: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Error creating scope: {str(e)}")
            return False
    
    def create_secret(self, scope_name, key, value):
        """
        Create or update a single secret in the specified scope.
        
        Args:
            scope_name (str): Name of the scope
            key (str): Secret key name
            value (str): Secret value
        
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.databricks_instance}/api/2.0/secrets/put"
        
        payload = {
            "scope": scope_name,
            "key": key,
            "string_value": str(value)
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                print(f"Secret '{key}' synced successfully.")
                return True
            else:
                print(f"Failed to sync secret '{key}': {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Error syncing secret '{key}': {str(e)}")
            return False
    
    def get_env_variables_for_secrets(self):
        """
        Get environment variables from .env file only (not system variables).
        
        Returns:
            dict: Dictionary of environment variables to sync as {env_key: secret_key}
        """
        env_vars = {}
        
        # Read the .env file directly to get only those variables
        env_file_path = '.env'
        if not os.path.exists(env_file_path):
            print("Warning: .env file not found")
            return env_vars
        
        try:
            with open(env_file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Only include non-reserved variables with actual values
                        if key not in self.reserved_vars and value:
                            env_vars[key] = key.lower()
                    else:
                        print(f"Warning: Skipping malformed line {line_num} in .env file: {line}")
        
        except Exception as e:
            print(f"Error reading .env file: {str(e)}")
        
        return env_vars
    
    def create_secrets_from_env(self, scope_name):
        """
        Create/update secrets from all relevant environment variables.
        
        Args:
            scope_name (str): Name of the scope to store secrets in
        
        Returns:
            dict: Results of secret creation operations
        """
        env_vars = self.get_env_variables_for_secrets()
        results = {}
        
        if not env_vars:
            print("No environment variables found to sync as secrets.")
            return results
        
        print(f"\nSyncing {len(env_vars)} environment variables to scope '{scope_name}'...")
        print("-" * 60)
        
        for env_key, secret_key in env_vars.items():
            value = os.getenv(env_key)
            success = self.create_secret(scope_name, secret_key, value)
            results[secret_key] = success
        
        return results
    
    def list_secrets(self, scope_name):
        """List all secrets in a scope."""
        url = f"{self.databricks_instance}/api/2.0/secrets/list"
        params = {"scope": scope_name}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                secrets = response.json().get('secrets', [])
                print(f"\nSecrets in scope '{scope_name}': {len(secrets)} total")
                print("-" * 40)
                for secret in secrets:
                    print(f"  • {secret['key']}")
                return secrets
            else:
                print(f"Failed to list secrets: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Error listing secrets: {str(e)}")
            return []


def main():
    """Main function to run the secrets management."""
    try:
        manager = DatabricksSecretsManager()
        scope_name = os.getenv('SCOPE_NAME', 'AutoDbx')
        
        print("Databricks Secrets Manager")
        print("=" * 50)
        
        # Create the scope if it doesn't exist
        manager.create_scope(scope_name)
        
        # Sync all environment variables as secrets
        results = manager.create_secrets_from_env(scope_name)
        
        # Summary
        if results:
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            print(f"\nSummary: {successful}/{total} secrets synced successfully")
            
            if successful < total:
                failed = [key for key, success in results.items() if not success]
                print(f"Failed: {', '.join(failed)}")
        
        # List all secrets in the scope
        manager.list_secrets(scope_name)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())