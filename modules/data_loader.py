# modules/data_loader.py
import pandas as pd
import streamlit as st
from config import REQUIRED_COLUMNS

@st.cache_data
def load_data(source):
    """Loads data from CSV or XLSX, returns DataFrame and metadata."""
    try:
        if isinstance(source, str):
            if source.endswith('.csv'):
                df = pd.read_csv(source)
            else:
                df = pd.read_excel(source)
            file_name = source
        else: # UploadedFile
            if source.name.endswith('.csv'):
                df = pd.read_csv(source)
            else:
                df = pd.read_excel(source)
            file_name = source.name

        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        metadata = {
            "file_name": file_name,
            "record_count": len(df),
            "columns": df.columns.tolist()
        }
        return df, metadata

    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None, None

def preprocess(df):
    """Basic preprocessing: column names, date parsing, and ensuring timezone-naive datetimes."""
    if df is None:
        return pd.DataFrame() # return empty dataframe

    # Standardize column names (e.g., lowercase, replace spaces)
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    # Ensure date, hour, weekday columns exist and are timezone-naive
    if "call_ts" in df.columns:
        df["call_ts"] = pd.to_datetime(df["call_ts"], errors='coerce')
        
        # If timezone aware, convert to naive by removing tz info
        if pd.api.types.is_datetime64_any_dtype(df["call_ts"]) and df["call_ts"].dt.tz is not None:
            df["call_ts"] = df["call_ts"].dt.tz_localize(None)

        df["date"] = df["call_ts"].dt.date
        df["hour"] = df["call_ts"].dt.hour
        df["weekday"] = df["call_ts"].dt.day_name()
    
    return df