import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import t
import warnings
import traceback

# --- Models (No change) ---
def sigmoid_model_4pl(x, E_min, E_max, EC50, Hill_slope):
    epsilon = 1e-12; x = np.asarray(x, dtype=float)
    return E_min + (E_max - E_min) / (1 + np.power((x + epsilon) / (EC50 + epsilon), Hill_slope))

def sigmoid_model_3pl_min0(x, E_max, EC50, Hill_slope):
    epsilon = 1e-12; x = np.asarray(x, dtype=float)
    return 0 + (E_max - 0) / (1 + np.power((x + epsilon) / (EC50 + epsilon), Hill_slope))

# --- Calculate IC50 (No change in signature, already uses **plot_kwargs) ---
def calculate_ic50(concentrations, responses, response_stds=None, 
                   model_type='4PL', initial_guesses=None, plot_curve=True, **plot_kwargs):
    # ... (The entire existing logic of this function remains the same as the last version) ...
    # ... (Input validation, sorting, model selection, fitting, stats calculation) ...
    if len(concentrations) != len(responses): raise ValueError("Len mismatch")
    concentrations_arr = np.array(concentrations, dtype=float)
    responses_arr = np.array(responses, dtype=float)
    valid_indices = concentrations_arr > 0
    if not np.any(valid_indices): return np.nan, None, None, None
    concentrations_valid = concentrations_arr[valid_indices]; responses_valid = responses_arr[valid_indices]
    if response_stds is not None: response_stds_valid = np.array(response_stds, dtype=float)[valid_indices]
    else: response_stds_valid = None
    if len(concentrations_valid) < (4 if model_type == '4PL' else 3): print(f"Warn: Few points")

    sorted_indices = np.argsort(concentrations_valid)
    concentrations_sorted = concentrations_valid[sorted_indices]; responses_sorted = responses_valid[sorted_indices]
    if response_stds_valid is not None: response_stds_sorted = response_stds_valid[sorted_indices]
    else: response_stds_sorted = None
    
    E_min_guess = np.min(responses_sorted); E_max_guess = np.max(responses_sorted)
    EC50_guess = np.median(concentrations_sorted)
    is_inhibition = responses_sorted[0] > responses_sorted[-1] if len(responses_sorted) > 1 else True
    Hill_slope_guess = -1.0 if is_inhibition else 1.0

    if model_type == '4PL':
        model_func = sigmoid_model_4pl; p0 = [E_min_guess, E_max_guess, EC50_guess, Hill_slope_guess]
        if is_inhibition: bounds = ([0, E_min_guess, 0, -100], [E_max_guess, 110, np.inf, -0.01])
        else: bounds = ([E_min_guess, 0, 0, 0.01], [110, E_max_guess, np.inf, 100]) 
        n_params = 4; ec50_index = 2
    elif model_type == '3PL_min0':
        model_func = sigmoid_model_3pl_min0; p0 = [E_max_guess, EC50_guess, Hill_slope_guess]
        if is_inhibition: bounds = ([0, 0, -100], [110, np.inf, -0.01])
        else: bounds = ([0, 0, 0.01], [110, np.inf, 100])
        n_params = 3; ec50_index = 1
    else: raise ValueError(f"Unknown model: {model_type}")
    if initial_guesses is not None: p0 = initial_guesses

    fig_to_return = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            params, covariance = curve_fit(model_func, concentrations_sorted, responses_sorted, p0=p0, bounds=bounds, maxfev=10000, method='trf')
        
        if model_type == '4PL':
            E_min_fit, E_max_fit, EC50_fit, Hill_slope_fit = params
            fitted_params = {"E_min": E_min_fit, "E_max": E_max_fit, "EC50": EC50_fit, "Hill_slope": Hill_slope_fit}
            params_for_plot = params
        else: # 3PL_min0
            E_max_fit, EC50_fit, Hill_slope_fit = params; E_min_fit = 0.0
            fitted_params = {"E_min": E_min_fit, "E_max": E_max_fit, "EC50": EC50_fit, "Hill_slope": Hill_slope_fit}
            params_for_plot = [E_min_fit, E_max_fit, EC50_fit, Hill_slope_fit]
        ic50_value = EC50_fit
        
        residuals = responses_sorted - model_func(concentrations_sorted, *params)
        ss_res = np.sum(residuals**2); ss_tot = np.sum((responses_sorted - np.mean(responses_sorted))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1.0
        n_points = len(concentrations_sorted); dof = max(1, n_points - n_params)
        ic50_ci_95 = (np.nan, np.nan); ic50_std_err = np.nan
        try:
            std_errors = np.sqrt(np.diag(covariance)); ic50_std_err = std_errors[ec50_index]
            t_value = t.ppf(1 - 0.05 / 2, df=dof); ci_margin = t_value * ic50_std_err
            ic50_ci_95 = (ic50_value - ci_margin, ic50_value + ci_margin)
        except Exception as ci_err: print(f"Warn: CI/StdErr: {ci_err}")
        stats = {"R_squared": r_squared, "IC50_CI_95": ic50_ci_95, "IC50_StdErr": ic50_std_err}
        
        if plot_curve:
            fig_to_return = plot_dose_response(concentrations_sorted, responses_sorted, response_stds_sorted,
                                               params_for_plot, ic50_value, r_squared, model_type, 
                                               **plot_kwargs) # Pass kwargs
        return ic50_value, fitted_params, stats, fig_to_return
    except Exception as e:
        print(f"Fit Fail ({model_type}): {e}"); traceback.print_exc()
        if plot_curve:
             fig_to_return = plot_dose_response(concentrations_sorted, responses_sorted, response_stds_sorted, 
                                None, np.nan, None, model_type, fit_failed=True, **plot_kwargs)
        return np.nan, None, None, fig_to_return

# --- 3. Plotting Function (Updated for more style options) ---
def plot_dose_response(concentrations, responses, response_stds, fitted_params_4pl, 
                       ic50_value, r_squared, model_type, fit_failed=False, 
                       plot_title=None, x_label=None, y_label=None,
                       data_color='red', curve_color='blue', # <-- NEW style args
                       marker_style='o', curve_style='-'):  # <-- NEW style args
    """Generates a plot with optional custom labels and styles."""
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot(1, 1, 1)
    
    ax.errorbar(concentrations, responses, yerr=response_stds,
                 fmt=marker_style,  # <-- Use custom marker
                 color=data_color,  # <-- Use custom data color
                 label='Experimental Data (Mean ± SD)', 
                 capsize=4, linestyle='None', zorder=2)

    default_title = f'Dose-Response Curve ({model_type})'
    default_x = 'Concentration (log scale)'
    default_y = 'Normalized Response (%)'

    if not fit_failed and fitted_params_4pl is not None:
        min_c_val = np.min(concentrations[concentrations > 0]) if np.any(concentrations > 0) else 1e-3
        max_c_val = np.max(concentrations) if np.any(concentrations > 0) else 1e3
        x_curve = np.logspace(np.log10(min_c_val) - 1, np.log10(max_c_val) + 1, 200)
        y_curve = sigmoid_model_4pl(x_curve, *fitted_params_4pl) 
        curve_label = f'{model_type} Fit (IC50 = {ic50_value:.2e}, R² = {r_squared:.3f})'
        ax.plot(x_curve, y_curve, label=curve_label, 
                color=curve_color,   # <-- Use custom curve color
                linestyle=curve_style, # <-- Use custom curve style
                zorder=1)
        ax.axvline(ic50_value, color='gray', linestyle='--')
        ax.set_title(plot_title if plot_title else default_title)
    else:
        ax.set_title(plot_title if plot_title else f'Dose-Response Data (Fit Failed - {model_type})')

    ax.set_xscale('log')
    ax.set_xlabel(x_label if x_label else default_x)
    ax.set_ylabel(y_label if y_label else default_y)
    ax.legend(fontsize='small')
    ax.grid(True, which="both", ls="-", alpha=0.5); plt.tight_layout()
    return fig

# --- 4. Example Usage (No change) ---
if __name__ == "__main__":
    pass