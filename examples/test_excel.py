import pandas as pd
from soda.scan import Scan
import os

# Read the Excel file
df_orig = pd.read_excel("data.xlsx")  # You'll need to provide the correct path to your Excel file

# Add the dataframe to scan
scan = Scan()
scan.set_scan_definition_name("excel_validation")
scan.add_pandas_dataframe(dataset_name="excel_data", pandas_df=df_orig)



# Load checks from external YAML file with explicit path handling
yaml_path = os.path.join(os.path.dirname(__file__), "checks_sg.yml")
if not os.path.exists(yaml_path):
    raise FileNotFoundError(f"YAML file not found at: {yaml_path}")

scan.add_sodacl_yaml_file(yaml_path)

scan.execute()

# Generate and print the report
from test02 import generate_scan_report
print(generate_scan_report(scan)) 
