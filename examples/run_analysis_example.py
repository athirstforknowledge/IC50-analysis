import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# --- Add Project Root to Python Path ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# --- Import Our Modules ---
from ic50_pkg.data_loader import load_and_process_data
from ic50_pkg.analyzer import calculate_ic50

def run_full_analysis(data_file_path):
    """
    Loads data from a CSV or Excel file, processes it, calculates IC50 & stats
    for each sample found, and plots the results.
    """
    print(f"--- Starting Full Analysis for: {os.path.basename(data_file_path)} ---")

    # 1. Load and Process Data
    processed_df = load_and_process_data(data_file_path)

    if processed_df is None:
        print("\n--- Analysis Halted: Data loading or processing failed. ---")
        return None

    # 2. Identify Unique Samples
    unique_samples = processed_df['SampleName'].unique()
    print(f"\nFound {len(unique_samples)} sample(s): {', '.join(unique_samples)}")

    results = {}

    # 3. Loop Through Each Sample
    for sample_name in unique_samples:
        print(f"\n=======================================")
        print(f"--- Analyzing Sample: {sample_name} ---")
        print(f"=======================================")

        sample_data = processed_df[processed_df['SampleName'] == sample_name].copy()
        sample_data = sample_data.sort_values(by='Concentration')

        concentrations = sample_data['Concentration'].values
        responses = sample_data['Normalized_Response_Mean'].values
        stds = sample_data['Normalized_Response_Std'].values

        if len(concentrations) < 4:
            print(f"Warning: Skipping {sample_name}. Not enough data points.")
            results[sample_name] = {'IC50': None, 'Params': None, 'Stats': None, 'Error': 'Not enough data'}
            continue

        # --- THIS IS THE CALL, NOW ON A SINGLE LINE ---
        ic50_value, fitted_params, stats = calculate_ic50(concentrations, responses, response_stds=stds, plot_curve=True)

        if pd.isna(ic50_value):
            print(f">>> FAILED to calculate IC50 for {sample_name}.")
            results[sample_name] = {'IC50': None, 'Params': None, 'Stats': None, 'Error': 'Fit failed'}
        else:
            print(f">>> SUCCESS! Calculated IC50 for {sample_name}: {ic50_value:.3e}")
            results[sample_name] = {'IC50': ic50_value, 'Params': fitted_params, 'Stats': stats, 'Error': None}

        plt.show()

    # 4. Print Summary
    print("\n=======================================")
    print("--- Analysis Summary ---")
    print("=======================================")
    for sample, result in results.items():
        if result['IC50'] is not None and result['Stats'] is not None:
            stats_info = result['Stats']
            ci_lower, ci_upper = stats_info['IC50_CI_95']
            if not (pd.isna(ci_lower) or pd.isna(ci_upper)):
                print(f"  {sample}: IC50 = {result['IC50']:.3e} "
                      f"(95% CI: {ci_lower:.3e} - {ci_upper:.3e}), "
                      f"R² = {stats_info['R_squared']:.4f}")
            else:
                print(f"  {sample}: IC50 = {result['IC50']:.3e} "
                      f"(95% CI: N/A), "
                      f"R² = {stats_info['R_squared']:.4f}")
        else:
            error_msg = result.get('Error', 'Unknown Error')
            print(f"  {sample}: IC50 = Calculation Failed ({error_msg})")
    print("=======================================")

    return results

# --- Main execution block ---
if __name__ == "__main__":
    csv_example = 'example_data.csv'
    xlsx_example = 'example_data.xlsx'

    script_dir = os.path.dirname(__file__)
    csv_path = os.path.join(script_dir, csv_example)
    xlsx_path = os.path.join(script_dir, xlsx_example)

    data_path_to_use = xlsx_path if os.path.exists(xlsx_path) else csv_path

    if not os.path.exists(data_path_to_use):
        print(f"Error: Example data file not found at {csv_path} or {xlsx_path}")
    else:
        run_full_analysis(data_path_to_use)