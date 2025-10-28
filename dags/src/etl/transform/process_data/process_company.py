import os
import pandas as pd

def process_company_data(overview_df, profile_df):
    # Xử lý dữ liệu: Loại bỏ các cột không cần thiết từ profile_df
    profile_df = profile_df.drop(columns=['history_dev', 'company_promise', 'key_developments',
                                          'business_risk', 'company_profile', 
                                          'business_strategies'], errors='ignore')
    
    # Xử lý dữ liệu: Loại bỏ các cột không cần thiết từ overview_df
    overview_df = overview_df.drop(columns=['exchange', 'no_shareholders', 'foreign_percent',
                                            'outstanding_share', 'issue_share', 'established_year',
                                            'no_employees', 'delta_in_week', 'delta_in_month',
                                            'delta_in_year', 'website', 'industry_id', 
                                            'industry_id_v2'], errors='ignore')
    
    # Gộp hai DataFrame theo cột 'symbol'
    company_summary = pd.merge(profile_df, overview_df, on='symbol', how='inner')
    
    return company_summary