from pathlib import Path
import joblib
import pandas as pd
from padelpy import padeldescriptor
import streamlit as st


root = Path(__file__).parent
models = root / "models"
static = root / "static"
sample_data = root / "sample_data"


@st.cache_resource
def load_model():
    path = models / "rf_reg.joblib"
    if not path.exists():
        st.error(f"rf_reg.joblib not found")
        return None
    return joblib.load(path)


@st.cache_resource
def load_variance_selector():
    path = models / "variance_selector.joblib"
    if not path.exists():
        st.error(f"variance_selector.joblib not found")
        return None
    return joblib.load(path)


@st.cache_resource
def load_scaler():
    path = models / "target_scaler.joblib"
    if not path.exists():
        st.error(f"target_scaler.joblib not found")
        return None
    return joblib.load(path)


model = load_model()
variance_selector = load_variance_selector()
scaler = load_scaler()


def detect_columns(df: pd.DataFrame):
    if df.shape[1] != 2:
        st.error(f"Expected 2 columns, but found {df.shape[1]}.")
        return None

    col1, col2 = df.columns
    col1_is_chembl = df[col1].astype(str).str.startswith("CHEMBL").sum()
    col2_is_chembl = df[col2].astype(str).str.startswith("CHEMBL").sum()

    chembl_col = col1 if col1_is_chembl >= col2_is_chembl else col2
    smiles_col = col2 if chembl_col == col1 else col1
    return chembl_col, smiles_col


def prepare_padel_input(df, output_file="molecules.smi"):
    detected = detect_columns(df)
    if detected is None:
        return None

    chembl_col, smiles_col = detected
    df_smiles = df[[smiles_col, chembl_col]]
    df_smiles.to_csv(output_file, sep="\t", index=False, header=False)
    return output_file


def generate_fingerprints(input_smi="molecules.smi", output_csv="fingerprints.csv"):
    padeldescriptor(
        mol_dir=input_smi,
        d_file=output_csv,
        fingerprints=True,
        retainorder=True,
    )
    return output_csv


def apply_variance_threshold(df_fps: pd.DataFrame):
    if variance_selector is None:
        st.error("Variance selector is missing.")
        return None

    if "Name" in df_fps.columns:
        df_fps = df_fps.drop(columns=["Name"])

    df_fps = df_fps.apply(pd.to_numeric, errors="coerce")

    st.write(f"Input feature shape before selection: {df_fps.shape}")
    try:
        reduced = variance_selector.transform(df_fps)
        st.write(f"Feature shape after selection: {reduced.shape}")
        return reduced
    except Exception as e:
        st.error(f"Error during feature selection: {e}")
        return None


def undo_scaling_and_convert(predictions):
    """Convert scaled IC50 predictions back to original nM values."""
    if scaler is None:
        return predictions

    import numpy as np  # local import just in case

    try:
        predictions = np.array(predictions).reshape(-1, 1)
        unscaled = scaler.inverse_transform(predictions).flatten()
        ic50_nM = 10 ** (-unscaled) * 1e9
        return ic50_nM
    except Exception as e:
        st.error(f"Scaling error: {e}")
        return predictions


def predict_ic50(df_fps: pd.DataFrame):
    """Predict IC50 values and convert back to nanomolar (nM)."""
    if model is None:
        st.error("No trained model found. Model file missing.")
        return None

    reduced = apply_variance_threshold(df_fps)
    if reduced is None:
        return None

    if model.n_features_in_ != reduced.shape[1]:
        st.error(
            f"Model expects {model.n_features_in_} features, "
            f"but received {reduced.shape[1]}."
        )
        return None

    try:
        preds = model.predict(reduced)
        ic50_nM = undo_scaling_and_convert(preds)
        return pd.DataFrame({"Predicted IC50 (nM)": ic50_nM})
    except Exception as e:
        st.error(f"Error during prediction: {e}")
        return None



st.title("CGRP Receptor Antagonist IC50 Predictor")

gif_path = static / "inhib_CGRP.gif"
if gif_path.exists():
    st.image(str(gif_path), use_container_width=True)
st.caption(
    "Figure 1. Molecular visualization of Olcegepant and Telcagepant binding "
    "the CGRP receptor, generated using PyMOL (v2.5.5, Schrödinger, LLC)."
)

st.subheader("Submit a molecule for CGRP receptor inhibition analysis.")
st.write("Upload a CSV or TXT file with **two columns**: ChEMBL ID and SMILES.")

sample_csv_path = sample_data / "example_input.csv"
sample_txt_path = sample_data  / "example_input.txt"

st.write("You can start with these example files (no header row):")
cols = st.columns(2)
with cols[0]:
    if sample_csv_path.exists():
        with open(sample_csv_path, "rb") as f:
            cols[0].download_button(
                "Download Sample CSV",
                f.read(),
                file_name="example_input.csv",
                mime="text/csv",
            )
with cols[1]:
    if sample_txt_path.exists():
        with open(sample_txt_path, "rb") as f:
            cols[1].download_button(
                "Download Sample TXT",
                f.read(),
                file_name="example_input.txt",
                mime="text/plain",
            )

st.write("__________________")


file_type = st.radio("Choose file type:", ["CSV", "TXT"])
uploaded_file = st.file_uploader(
    f"Upload a {file_type} file (2 columns, no header)", type=["csv", "txt"]
)

if uploaded_file:
    try:
        if file_type == "CSV":
            df = pd.read_csv(uploaded_file, header=None)
        else:  # TXT file
            df = pd.read_csv(uploaded_file, sep="\t", header=None)

        if df.shape[1] != 2:
            st.error(f"Expected 2 columns, but found {df.shape[1]}.")
            st.stop()

        st.write("**Uploaded Data Sample**")
        st.write(df.head(10))

        smi_file = prepare_padel_input(df)
        if smi_file is None:
            st.stop()

        fps_file = generate_fingerprints(smi_file)
        df_fps = pd.read_csv(fps_file)

        preds_df = predict_ic50(df_fps)
        if preds_df is None:
            st.stop()

        st.write("**Predictions**")
        st.write(preds_df.head(10))

        csv_bytes = preds_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Prediction Results",
            csv_bytes,
            file_name="predictions.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error reading or processing file: {e}")

st.markdown("**[GitHub](https://github.com/danigeiger)**")
