import pandas as pd

# --- Step 1: Load Excel file ---
file_path = "./R.xlsx"  # Change this to your filename
excel = pd.ExcelFile(file_path)

# --- Step 2: Define sheet groups ---
old_sheets = ['2022', '2023', '2024']
new_sheet = '2025'

# --- Step 3: Function to clean and normalize columns ---
def clean_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    
    # Rename variations for consistency
    rename_map = {
        'team award': 'team name',
        'month of recognition': 'month',
    }
    df.rename(columns=rename_map, inplace=True)
    
    # Make sure all expected columns exist (fill missing)
    for col in ['s.no', 'employee name', 'team name', 'month',
                'award title', 'nominated by', 'coupon amount', 'distribution']:
        if col not in df.columns:
            df[col] = None
    return df

# --- Step 4: Combine OLD data (2022–2024) ---
old_list = []
for sheet in old_sheets:
    if sheet in excel.sheet_names:
        data = pd.read_excel(file_path, sheet_name=sheet)
        data = clean_columns(data)
        data['source_year'] = sheet
        old_list.append(data)

old_data = pd.concat(old_list, ignore_index=True)

# --- Step 5: Process NEW data (2025) ---
new_data = pd.read_excel(file_path, sheet_name=new_sheet)
new_data = clean_columns(new_data)
new_data['source_year'] = new_sheet

# Filter only “Kudos Corner”
new_data_kudos = new_data[new_data['award title'].str.strip().str.lower() == 'kudos corner']

# --- Step 6: Save outputs ---
old_data.to_excel("Old_Data.xlsx", index=False)
new_data_kudos.to_excel("New_Data_KudosCorner.xlsx", index=False)

print("✅ Split complete!")
print(" - Old_Data.xlsx (2022–2024)")
print(" - New_Data_KudosCorner.xlsx (2025 Kudos Corner only)")
