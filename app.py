import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIG & SETUP ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

# Standard columns for the whole system
LOG_COLS = ["Date", "User", "Location", "Stall", "Product", "Extras", "Price", "Extra_Price", "Total", "Wallet_Left", "Type", "Note"]

st.set_page_config(page_title="Finance & Canteen System", layout="wide")

# --- 2. DATA ENGINE ---
def load_data(file, default_cols):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file, dtype=str)
            # Repair logic: adds missing columns if the CSV is old
            for col in default_cols:
                if col not in df.columns:
                    df[col] = "0" if "Price" in col or "Total" in col else "N/A"
            return df
        except:
            return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

user_df = load_data(USER_FILE, ["Username", "Password"])
log_
