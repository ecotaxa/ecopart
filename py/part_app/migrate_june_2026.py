import sys
import os
import requests

# Ensure the parent directory is in the path so we can import part_app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import g
from part_app.app import part_app
from part_app.db_utils import GetAll, ExecSQL
from part_app.urls import BACKEND_API_HOST, BACKEND_API_PORT

def main():
    """
    Connect to the DB, collect values of EcoTaxa project IDs and sample IDs,
    and call /migrated_ids on Ecotaxa host.
    Update the corresponding fields in DB with the migrated IDs.
    """
    with part_app.app_context():
        # Initialize g.db as expected by db_utils
        g.db = None
        
        print("Migrating part_samples.sampleid to BIGINT...")
        alter_sql = "ALTER TABLE part_samples ALTER COLUMN sampleid TYPE BIGINT"
        print(f"Executing: {alter_sql}")
        ExecSQL(alter_sql)
        
        print("Collecting EcoTaxa Project IDs...")
        # projid in part_projects corresponds to the EcoTaxa project ID
        sql_projects = "SELECT projid, ptitle FROM part_projects WHERE projid IS NOT NULL"
        print(f"Executing: {sql_projects}")
        projects = GetAll(sql_projects)
        project_ids = [str(prj['projid']) for prj in projects]
        print(f"Collected {len(project_ids)} Project IDs.")

        print("\nCollecting EcoTaxa Sample IDs...")
        # sampleid in part_samples corresponds to the EcoTaxa sample ID
        sql_samples = "SELECT sampleid, profileid FROM part_samples WHERE sampleid IS NOT NULL"
        print(f"Executing: {sql_samples}")
        samples = GetAll(sql_samples)
        sample_ids = [str(smp['sampleid']) for smp in samples]
        print(f"Collected {len(sample_ids)} Sample IDs.")

        if not project_ids and not sample_ids:
            print("\nNo IDs collected. Skipping API call.")
            return

        # Prepare API call
        base_url = f"{BACKEND_API_HOST}:{BACKEND_API_PORT[0]}/api"
        endpoint = f"{base_url}/migrated_ids"
        
        # Split IDs into chunks to avoid "Request URI too long" or other size limits
        chunk_size = 500
        
        def chunked_migrate(id_list, param_name):
            migrated_results = {}
            for i in range(0, len(id_list), chunk_size):
                chunk = id_list[i:i + chunk_size]
                params = {param_name: ','.join(chunk)}
                print(f"Calling {endpoint} for {len(chunk)} {param_name}...")
                try:
                    response = requests.get(endpoint, params=params)
                    response.raise_for_status()
                    data = response.json()
                    migrated_results.update(data.get(param_name, {}))
                except Exception as e:
                    print(f"Error calling EcoTaxa API for {param_name} chunk: {e}")
            return migrated_results

        print("\nMigrating Project IDs...")
        migrated_projects = chunked_migrate(project_ids, 'projects')
        print(f"Total migrated projects received: {len(migrated_projects)}")

        if migrated_projects:
            print("Updating part_projects...")
            count = 0
            for old_id, new_id in migrated_projects.items():
                if str(old_id) != str(new_id):
                    sql = "UPDATE part_projects SET projid=%s WHERE projid=%s"
                    params = (new_id, old_id)
                    print(f"  Executing: {sql} % {params}")
                    rowcount = ExecSQL(sql, params)
                    count += rowcount
            print(f"Updated {count} rows in part_projects.")

        print("\nMigrating Sample IDs...")
        migrated_samples = chunked_migrate(sample_ids, 'samples')
        print(f"Total migrated samples received: {len(migrated_samples)}")

        if migrated_samples:
            print("Updating part_samples...")
            count = 0
            for old_id, new_id in migrated_samples.items():
                if str(old_id) != str(new_id):
                    sql = "UPDATE part_samples SET sampleid=%s WHERE sampleid=%s"
                    params = (new_id, old_id)
                    print(f"  Executing: {sql} % {params}")
                    rowcount = ExecSQL(sql, params)
                    count += rowcount
            print(f"Updated {count} rows in part_samples.")

        # Optional: summary output
        if migrated_projects:
            print("\nMigrated Projects mapping (first 5):")
            for k in list(migrated_projects.keys())[:5]:
                print(f"  {k} -> {migrated_projects[k]}")
        
        if migrated_samples:
            print("\nMigrated Samples mapping (first 5):")
            for k in list(migrated_samples.keys())[:5]:
                print(f"  {k} -> {migrated_samples[k]}")

if __name__ == "__main__":
    main()
