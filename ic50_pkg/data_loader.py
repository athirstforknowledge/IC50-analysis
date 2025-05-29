import pandas as pd
import numpy as np
import os

def load_and_process_data(data_input):
    """
    Loads raw data from a file path OR a pandas DataFrame, 
    performs background subtraction, normalization, and handles replicates.

    Parameters:
    ----------
    data_input : str or pandas.DataFrame
        Either the path to the CSV/Excel file or a DataFrame.

    Returns:
    -------
    pandas.DataFrame or None
        A DataFrame containing processed data, or None if an error occurs.
    """
    try:
        # --- Read Data based on input type ---
        if isinstance(data_input, str): # It's a file path
            file_path = data_input
            file_name = os.path.basename(file_path)
            _, file_extension = os.path.splitext(file_path)

            if file_extension.lower() == '.csv':
                df = pd.read_csv(file_path)
                print(f"Reading data from CSV: {file_name}")
            elif file_extension.lower() == '.xlsx':
                df = pd.read_excel(file_path, engine='openpyxl', sheet_name=0)
                print(f"Reading data from Excel: {file_name}")
            else:
                print(f"Error: Unsupported file type: {file_extension}.")
                return None
        elif isinstance(data_input, pd.DataFrame): # It's a DataFrame
            df = data_input.copy() # Use a copy to avoid modifying original
            print("Processing data from uploaded DataFrame.")
        else:
            print("Error: Invalid input. Must be file path or DataFrame.")
            return None

        # --- Data Validation (with Case-Insensitive Column Handling) ---
        required_cols_lower = ['type', 'value']
        original_cols = df.columns.tolist()
        df.columns = [str(col).strip() for col in df.columns]
        df_cols_lower = [col.lower() for col in df.columns]

        if not all(req_col in df_cols_lower for req_col in required_cols_lower):
            print(f"Error: Input must have 'Type' & 'Value' columns. Found: {original_cols}")
            return None
            
        rename_map = {}
        for original, lower in zip(df.columns, df_cols_lower):
            if lower == 'type': rename_map[original] = 'Type'
            if lower == 'value': rename_map[original] = 'Value'
            if lower == 'concentration': rename_map[original] = 'Concentration'
            if lower == 'samplename': rename_map[original] = 'SampleName'
        df = df.rename(columns=rename_map)

        # --- Process Data ---
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df = df.dropna(subset=['Value']) 
        
        bg_wells = df[df['Type'].str.lower() == 'background']['Value']
        avg_bg = bg_wells.mean() if not bg_wells.empty else 0.0
        print(f"Average Background: {avg_bg:.4f}")

        control_wells = df[df['Type'].str.lower() == 'control_100']['Value']
        if control_wells.empty: print("Error: No 'Control_100' found."); return None
        avg_control = (control_wells - avg_bg).mean()
        print(f"Average 100% Control (BG Subtracted): {avg_control:.4f}")
        if avg_control <= 0: print("Error: Control value <= 0."); return None

        sample_df = df[df['Type'].str.lower() == 'sample'].copy()
        if sample_df.empty: print("Error: No 'Sample' data found."); return None
        if not all(col in sample_df.columns for col in ['Concentration', 'SampleName']):
            print("Error: 'Sample' rows need 'Concentration' & 'SampleName'."); return None
            
        sample_df['Concentration'] = pd.to_numeric(sample_df['Concentration'], errors='coerce')
        sample_df = sample_df.dropna(subset=['Concentration', 'SampleName'])
        sample_df['Value_BG_Sub'] = sample_df['Value'] - avg_bg
        sample_df['Normalized_Response'] = (sample_df['Value_BG_Sub'] / avg_control) * 100
        
        processed_data = sample_df.groupby(['SampleName', 'Concentration']).agg(
            Normalized_Response_Mean=('Normalized_Response', 'mean'),
            Normalized_Response_Std=('Normalized_Response', 'std'),
            N_Replicates=('Normalized_Response', 'size')
        ).reset_index()
        processed_data['Normalized_Response_Std'] = processed_data['Normalized_Response_Std'].fillna(0)

        print("\n--- Aggregated Data (Mean & Std Dev) ---")
        print(processed_data)
        return processed_data

    except Exception as e: 
        print(f"An unexpected error occurred during data processing: {e}")
        traceback.print_exc() # Print full traceback for debugging
        return None

# --- Example Usage (No change needed) ---
if __name__ == "__main__":
    # ... (This part remains the same) ...
    pass