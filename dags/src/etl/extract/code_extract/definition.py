import pandas as pd
from vnstock.explorer.vci import Finance
import os

def collect_definition_data():
    data = Finance(symbol='PLX', period='quarter')._get_ratio_dict()

    output_dir = r"D:\project_persional\chabot_stock\data\raw\definition"
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, "definition_ratio.csv")
    data.to_csv(file_path, index=False, encoding='utf-8-sig')

# Chạy chương trình
print(collect_definition_data())