import streamlit as st
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import traceback
import io 

# --- Add Project Root & Import ---
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
try:
    from ic50_pkg.data_loader import load_and_process_data
    from ic50_pkg.analyzer import calculate_ic50
except ImportError as e:
    st.error(f"FATAL ERROR: Could not import core modules: {e}. ", icon="🚨")
    st.stop()

# --- Initialize Session State Variables ---
def init_session_state():
    defaults = {
        "df_raw": None, "uploaded_file_name": None,
        "model_choice_display": '4PL (4-Parameter)', 
        "-PLOT_TITLE-": "", "-X_LABEL-": "", "-Y_LABEL-": "",
        "-DATA_COLOR-": "#FF0000", "-CURVE_COLOR-": "#0000FF",
        "-MARKER_STYLE-": 'Circle', "-CURVE_STYLE-": 'Solid',
        "analysis_done": False, "all_results_list": None, "processed_df_cache": None
    }
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value
init_session_state()

# --- Helper Function for Example Data (CORRECTED INDENTATION) ---
@st.cache_data 
def get_example_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    example_path = os.path.join(script_dir, 'examples', 'example_data.xlsx')
    if os.path.exists(example_path):
        with open(example_path, "rb") as file:
            return file.read() # <-- Correctly indented
    st.warning(f"Example file not found: {example_path}")
    return None

# --- Page Config ---
st.set_page_config(page_title="PyIC50 Analyzer", page_icon="🧪", layout="wide")

# --- Sidebar Content ---
st.sidebar.header("About PyIC50 Analyzer ℹ️")
st.sidebar.info(
    "This tool performs 4-parameter logistic regression (4PL) or "
    "3-parameter logistic regression (3PL, Min=0) to calculate "
    "IC50/EC50 values and key statistics (R², 95% CI) from dose-response "
    "experimental data. It accepts both CSV and Excel (.xlsx) files."
)
st.sidebar.header("Instructions & Data Format 📋")
with st.sidebar.expander("Data Format Guide"):
    st.markdown(
        """
        Your data file (CSV or Excel) **must** contain these columns 
        (case-insensitive headers are okay):

        1.  **`Type`**: Must be one of:
            * `Background`: Blank wells.
            * `Control_100`: 100% activity / 0% inhibition control.
            * `Sample`: Your experimental wells.
        2.  **`Value`**: The raw absorbance/fluorescence reading.
        3.  **`Concentration`**: The concentration for `Sample` types (leave blank/0 for others).
        4.  **`SampleName`**: The name of the substance for `Sample` types.
        """
    )
    st.table(pd.DataFrame({
        'Type': ['Background', 'Control_100', 'Sample', 'Sample'],
        'Value': [0.15, 1.30, 1.20, 0.95],
        'Concentration': ['', '', 1, 10],
        'SampleName': ['', '', 'CompoundX', 'CompoundX']
    }))
example_bytes = get_example_data()
if example_bytes: st.sidebar.download_button("Download Example (.xlsx)", example_bytes, "example_data.xlsx")
st.sidebar.header("Model Selection Guide 🧠")
with st.sidebar.expander("4PL vs. 3PL - Which to Choose?"):
    st.markdown("""
        * **4-Parameter Logistic (4PL):** Use when data determines both plateaus.
        * **3-Parameter Logistic (3PL - Min=0):** Use when response should go to 0.
    """)
st.sidebar.header("Interpreting Your Results 📈")
with st.sidebar.expander("Tips on R², CI, Hill Slope etc."):
    st.markdown("""
        * **IC50/EC50:** Concentration for 50% maximal response.
        * **R-squared (R²):** Closer to 1 is better fit (>0.95 good).
        * **95% Confidence Interval (CI):** Range for true IC50. Narrow is better.
        * **Hill Slope:** Steepness of curve (around -1 or +1 typical).
    """)
st.sidebar.header("Credit & Contact 🧑‍🔬")
st.sidebar.markdown("Designed by **Tshepo Aphane**. [aphanetshepo@outlook.com](mailto:aphanetshepo@outlook.com)")
st.sidebar.caption(f"App running in Pretoria, SA.")


# --- Main App Layout ---
st.title("🧪 PyIC50/EC50 Analysis Tool") 
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Upload Data File")
    uploaded_file = st.file_uploader("CSV or XLSX", type=['csv', 'xlsx'], label_visibility="collapsed", key="file_uploader_key")
with col2:
    st.subheader("2. Select Analysis Model")
    st.session_state.model_choice_display = st.radio(
        "Model:", ('4PL (4-Parameter)', '3PL (3-Parameter, Min=0)'), horizontal=True, label_visibility="collapsed", 
        index=0 if st.session_state.model_choice_display == '4PL (4-Parameter)' else 1, key="model_radio"
    )
model_code = '4PL' if st.session_state.model_choice_display == '4PL (4-Parameter)' else '3PL_min0'
st.caption(f"Using **{model_code}** model.")

st.subheader("3. Plotting Options (Optional)")
with st.expander("Customize Plot Appearance"):
    plot_opt_col1, plot_opt_col2 = st.columns(2)
    with plot_opt_col1:
        st.session_state["-PLOT_TITLE-"] = st.text_input("Plot Title:", value=st.session_state["-PLOT_TITLE-"])
        st.session_state["-X_LABEL-"] = st.text_input("X-Axis Label:", value=st.session_state["-X_LABEL-"])
        st.session_state["-Y_LABEL-"] = st.text_input("Y-Axis Label:", value=st.session_state["-Y_LABEL-"])
    with plot_opt_col2:
        st.session_state["-DATA_COLOR-"] = st.color_picker("Data Color:", value=st.session_state["-DATA_COLOR-"])
        st.session_state["-CURVE_COLOR-"] = st.color_picker("Curve Color:", value=st.session_state["-CURVE_COLOR-"])
        marker_options = {'Circle': 'o', 'Square': 's', 'Triangle Up': '^', 'Diamond': 'D', 'X': 'x', 'Plus': '+'}
        st.session_state["-MARKER_STYLE-"] = st.selectbox("Marker:", options=list(marker_options.keys()), index=list(marker_options.keys()).index(st.session_state["-MARKER_STYLE-"]))
        curve_style_options = {'Solid': '-', 'Dashed': '--', 'Dash-Dot': '-.', 'Dotted': ':'}
        st.session_state["-CURVE_STYLE-"] = st.selectbox("Curve Style:", options=list(curve_style_options.keys()), index=list(curve_style_options.keys()).index(st.session_state["-CURVE_STYLE-"]))

# --- File processing logic ---
if uploaded_file is not None:
    try:
        uploaded_file.seek(0) 
        if uploaded_file.name.endswith('.csv'):
            df_from_file = pd.read_csv(uploaded_file)
        else:
            df_from_file = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.session_state.df_raw = df_from_file
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.analysis_done = False 
        st.session_state.all_results_list = None
        st.session_state.processed_df_cache = None
        st.success(f"✅ Successfully read: **{st.session_state.uploaded_file_name}**")

    except Exception as e:
        st.error(f"Error reading uploaded file: {e}")
        st.exception(e) 
        st.session_state.df_raw = None 
        st.session_state.uploaded_file_name = None 

# --- Show Preview and Run Button IF df_raw is successfully populated ---
if st.session_state.df_raw is not None:
    st.subheader("4. Preview Uploaded Data"); st.dataframe(st.session_state.df_raw.head())
    st.divider(); st.subheader("5. Run the Analysis")
    
    if st.button(f"🚀 Calculate IC50 ({model_code})!", type="primary", use_container_width=True):
        st.session_state.analysis_done = False
        st.session_state.all_results_list = []
        st.session_state.processed_df_cache = None
        plot_options_kwargs = {
            'plot_title': st.session_state["-PLOT_TITLE-"] or None, 
            'x_label': st.session_state["-X_LABEL-"] or None,
            'y_label': st.session_state["-Y_LABEL-"] or None, 
            'data_color': st.session_state["-DATA_COLOR-"], 
            'curve_color': st.session_state["-CURVE_COLOR-"], 
            'marker_style': marker_options[st.session_state["-MARKER_STYLE-"]], 
            'curve_style': curve_style_options[st.session_state["-CURVE_STYLE-"]]
        }
        with st.spinner("⏳ Processing & Fitting..."):
            st.session_state.processed_df_cache = load_and_process_data(st.session_state.df_raw)
        
        if st.session_state.processed_df_cache is None: 
            st.error("❌ Data processing failed.", icon="🚨")
        else:
            st.markdown("#### Processed Summary:"); st.dataframe(st.session_state.processed_df_cache)
            st.divider(); st.markdown("#### Analysis Results:")
            unique_samples = st.session_state.processed_df_cache['SampleName'].unique()
            result_cols = st.columns(len(unique_samples))
            
            for i, sample_name in enumerate(unique_samples):
                with result_cols[i % len(result_cols)]:
                    st.subheader(f"{sample_name}")
                    sample_data = st.session_state.processed_df_cache[st.session_state.processed_df_cache['SampleName'] == sample_name].copy().sort_values(by='Concentration')
                    concentrations = sample_data['Concentration'].values
                    responses = sample_data['Normalized_Response_Mean'].values
                    stds = sample_data['Normalized_Response_Std'].values
                    
                    if len(concentrations) < (4 if model_code == '4PL' else 3): 
                        st.warning(f"Skip: Few points."); continue
                    
                    ic50_value, fitted_params, stats, fig = calculate_ic50(
                        concentrations, responses, response_stds=stds, model_type=model_code, plot_curve=True, **plot_options_kwargs
                    )
                    result_entry = {'SampleName': sample_name, 'Model': model_code}
                    if pd.isna(ic50_value): 
                        st.error(f"Fit FAILED.")
                        result_entry.update({'IC50': 'FAILED'})
                    else:
                        st.metric(f"IC50 ({model_code})", f"{ic50_value:.3e}")
                        st.write(f"**R²:** {stats['R_squared']:.4f}")
                        ci_l, ci_u = stats['IC50_CI_95']
                        st.write(f"**95% CI:** ({ci_l:.3e}, {ci_u:.3e})")
                        with st.expander("Params"): st.json(fitted_params)
                        result_entry.update({'IC50': ic50_value, **stats, **fitted_params})
                    
                    if fig: 
                        st.pyplot(fig)
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
                        st.download_button("Download Plot", buf, f"{sample_name}_{model_code}_plot.png", "image/png", key=f"dl_plot_{sample_name}_{i}")
                        plt.close(fig)
                    st.session_state.all_results_list.append(result_entry)
            st.session_state.analysis_done = True
            st.balloons()

if st.session_state.analysis_done and st.session_state.all_results_list:
    st.divider(); st.subheader("6. Download Full Results Table")
    results_df = pd.DataFrame(st.session_state.all_results_list)
    desired_cols = ['SampleName', 'Model', 'IC50', 'R_Squared', 'CI_Lower', 'CI_Upper', 'E_min', 'E_max', 'Hill_slope']
    final_cols = [c for c in desired_cols if c in results_df.columns]
    results_df_display = results_df[final_cols]
    st.dataframe(results_df_display) 
    csv_data = results_df_display.to_csv(index=False).encode('utf-8')
    st.download_button("Download Results (CSV)", csv_data, f"{st.session_state.uploaded_file_name}_results.csv" if st.session_state.uploaded_file_name else "analysis_results.csv", "text/csv", use_container_width=True)
elif 'df_raw' not in st.session_state or st.session_state.df_raw is None :
    st.info("⬆️ Upload a file, select model, set options, and run!")