# https://github.com/sodadata/soda-core/blob/main/examples/pandas_dask_example.py


import dask.datasets
import pandas as pd
from soda.scan import Scan
import os
from datetime import datetime


def generate_scan_report(scan):
    """Generate a formatted report from scan results."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = []
    report.append("=" * 80)
    report.append(f"SODA DATA QUALITY SCAN REPORT")
    report.append(f"Generated at: {now}")
    report.append("=" * 80)
    
    # Overall scan summary
    report.append("\nSCAN SUMMARY")
    report.append("-" * 80)
    report.append(f"Total Checks Run: {len(scan._checks)}")
    
    # Count check outcomes
    passed = sum(1 for c in scan._checks if getattr(c, 'outcome', None) == 'PASS')
    failed = sum(1 for c in scan._checks if getattr(c, 'outcome', None) == 'FAIL')
    warned = sum(1 for c in scan._checks if getattr(c, 'outcome', None) == 'WARN')
    errored = sum(1 for c in scan._checks if getattr(c, 'outcome', None) == 'ERROR')
    
    report.append(f"Passed Checks:    {passed}")
    report.append(f"Failed Checks:    {failed}")
    report.append(f"Warning Checks:   {warned}")
    report.append(f"Error Checks:     {errored}")
    
    # Detailed results by dataset
    report.append("\nDETAILED RESULTS")
    report.append("-" * 80)
    
    # Group checks by dataset
    checks_by_dataset = {}
    for check in scan._checks:
        # Try to get dataset name from various possible attributes
        dataset = None
        if hasattr(check, 'dataset_name'):
            dataset = check.dataset_name
        elif hasattr(check, 'table_name'):
            dataset = check.table_name
        else:
            dataset = "Global"
            
        if dataset not in checks_by_dataset:
            checks_by_dataset[dataset] = []
        checks_by_dataset[dataset].append(check)
    
    # Print results for each dataset
    for dataset, checks in checks_by_dataset.items():
        report.append(f"\nDataset: {dataset}")
        report.append("-" * 40)
        
        for check in checks:
            outcome = getattr(check, 'outcome', 'UNKNOWN')
            outcome_symbol = {
                'PASS': '✓',
                'FAIL': '✗',
                'WARN': '⚠',
                'ERROR': '!'
            }.get(outcome, '?')
            
            # Try to get check name or description from various possible attributes
            check_name = None
            if hasattr(check, 'name'):
                check_name = check.name
            elif hasattr(check, 'check_name'):
                check_name = check.check_name
            elif hasattr(check, 'check_cfg'):
                check_name = str(check.check_cfg)
            else:
                check_name = str(check)
            
            report.append(f"{outcome_symbol} [{outcome}] {check_name}")
            
            # Add diagnostics if available
            if outcome in ['FAIL', 'ERROR']:
                diagnostics = []
                if hasattr(check, 'diagnostics'):
                    diagnostics.append(str(check.diagnostics))
                if hasattr(check, 'error'):
                    diagnostics.append(str(check.error))
                if diagnostics:
                    report.append(f"  └─ Diagnostics: {' | '.join(diagnostics)}")
    
    # Final summary
    report.append("\n" + "=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


# Create soda scan object
scan = Scan()
scan.set_scan_definition_name("test")
scan.set_data_source_name("dask")

# Load timeseries data from dask datasets
df_timeseries = dask.datasets.timeseries().reset_index()
df_timeseries["email"] = "a@soda.io"

# Create an artificial pandas dataframe
df_employee = pd.DataFrame({"email": ["a@soda.io", "b@soda.io", "c@soda.io"]})

# Add dask dataframe to scan and assign a dataset name to refer from checks yaml
scan.add_dask_dataframe(dataset_name="timeseries", dask_df=df_timeseries)

# Add pandas dataframe to scan and assign a dataset name to refer from checks yaml
scan.add_pandas_dataframe(dataset_name="employee", pandas_df=df_employee)

# Load checks from external YAML file with explicit path handling
yaml_path = os.path.join(os.path.dirname(__file__), "checks.yml")
if not os.path.exists(yaml_path):
    raise FileNotFoundError(f"YAML file not found at: {yaml_path}")

scan.add_sodacl_yaml_file(yaml_path)

# Execute scan and generate report
scan.execute()
print(generate_scan_report(scan))

