from flask import Flask, render_template, jsonify, request
import dask.datasets
import pandas as pd
from soda.scan import Scan
import os
from datetime import datetime
import json

app = Flask(__name__)

def run_soda_scan():
    """Run the Soda scan and return the results"""
    # Create soda scan object
    scan = Scan()
    scan.set_scan_definition_name("test")
    scan.set_data_source_name("dask")

    # Load timeseries data from dask datasets
    df_timeseries = dask.datasets.timeseries().reset_index()
    df_timeseries["email"] = "a@soda.io"

    # Create an artificial pandas dataframe
    df_employee = pd.DataFrame({"email": ["a@soda.io", "b@soda.io", "c@soda.io"]})

    # Add dataframes to scan
    scan.add_dask_dataframe(dataset_name="timeseries", dask_df=df_timeseries)
    scan.add_pandas_dataframe(dataset_name="employee", pandas_df=df_employee)

    # Load checks from YAML file
    yaml_path = os.path.join(os.path.dirname(__file__), "checks.yml")
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"YAML file not found at: {yaml_path}")

    scan.add_sodacl_yaml_file(yaml_path)
    scan.execute()
    
    return process_scan_results(scan)

def process_scan_results(scan):
    """Process scan results into a format suitable for web display"""
    results = {
        'summary': {
            'total': len(scan._checks),
            'passed': sum(1 for c in scan._checks if getattr(c, 'outcome', None) == 'PASS'),
            'failed': sum(1 for c in scan._checks if getattr(c, 'outcome', None) == 'FAIL'),
            'warned': sum(1 for c in scan._checks if getattr(c, 'outcome', None) == 'WARN'),
            'errored': sum(1 for c in scan._checks if getattr(c, 'outcome', None) == 'ERROR')
        },
        'checks': []
    }
    
    for check in scan._checks:
        check_info = {
            'dataset': getattr(check, 'dataset_name', getattr(check, 'table_name', 'Global')),
            'outcome': getattr(check, 'outcome', 'UNKNOWN'),
            'name': (getattr(check, 'name', None) or 
                    getattr(check, 'check_name', None) or 
                    str(getattr(check, 'check_cfg', str(check)))),
            'diagnostics': []
        }
        
        if check_info['outcome'] in ['FAIL', 'ERROR']:
            if hasattr(check, 'diagnostics'):
                check_info['diagnostics'].append(str(check.diagnostics))
            if hasattr(check, 'error'):
                check_info['diagnostics'].append(str(check.error))
        
        results['checks'].append(check_info)
    
    return results

@app.route('/')
def index():
    """Main page showing scan results"""
    try:
        results = run_soda_scan()
        return render_template('index.html', results=results)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/run-scan', methods=['POST'])
def api_run_scan():
    """API endpoint to run a new scan"""
    try:
        results = run_soda_scan()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 


    