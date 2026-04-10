import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIG ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"

SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

LOG_COLS = [
    "Date", "User", "Location", "Stall", "Product",
    "Extras", "Price", "Extra_Price", "Total",
    "Wallet_Left", "Type", "Note"
]

st.set_page_config(page_title="Finance & Canteen System", layout="wide")

# --- DATA FUNCTIONS ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            return df
        except Exception as e:
            st.error(f"Error loading {file}: {e}")
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Load data
user_df = load_data(USER_FILE, ["Username", "Password"])
log_df = load_data(LOG_FILE, LOG_COLS)

# --- SESSION STATE ---
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None
    st.session_state.wallet = 0.0

# --- AUTH SYSTEM ---
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["🔒 Login", "📝 Register"])

    # LOGIN
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            valid_user = (
                (username == SUPER_USER and password == SUPER_PASS) or
                ((user_df["Username"] == username) & (user_df["Password"] == password)).any()
            )

            if valid_user:
                st.session_state.auth = True
                st.session_state.user = username
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    # REGISTER
    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Register"):
            if new_user in user_df["Username"].values:
                st.warning("User already exists")
            elif new_user and new_pass:
                new_row = pd.DataFrame([[new_user, new_pass]], columns=["Username", "Password"])
                user_df = pd.concat([user_df, new_row], ignore_index=True)
                save_data(user_df, USER_FILE)
                st.success("Account created! Go login.")
            else:
                st.warning("Fill all fields")

# --- MAIN APP ---
else:
    st.title("💰 Finance & Canteen System")

    st.sidebar.write(f"👤 Logged in as: {st.session_state.user}")

    # Wallet input
    st.sidebar.subheader("💵 Wallet")
    st.session_state.wallet = st.sidebar.number_input(
        "Enter current wallet",
        min_value=0.0,
        value=float(st.session_state.wallet)
    )

    # --- INPUT FORM ---
    st.subheader("🧾 Add Transaction")

    col1, col2 = st.columns(2)

    with col1:
        location = st.text_input("Location")
        stall = st.text_input("Stall")
        product = st.text_input("Product")

    with col2:
        extras = st.text_input("Extras")
        price = st.number_input("Price", min_value=0.0)
        extra_price = st.number_input("Extra Price", min_value=0.0)

    trans_type = st.selectbox("Type", ["Expense", "Top-up"])
    note = st.text_input("Note")

    if st.button("Add Transaction"):
        total = price + extra_price

        if trans_type == "Expense":
            st.session_state.wallet -= total
        else:
            st.session_state.wallet += total

        new_entry = pd.DataFrame([[
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            st.session_state.user,
            location,
            stall,
            product,
            extras,
            price,
            extra_price,
            total,
            st.session_state.wallet,
            trans_type,
            note
        ]], columns=LOG_COLS)

        log_df = pd.concat([log_df, new_entry], ignore_index=True)
        save_data(log_df, LOG_FILE)

        st.success("Transaction added!")

    # --- DISPLAY DATA ---
    st.subheader("📊 Transactions")
    st.dataframe(log_df.tail(20), use_container_width=True)

    # --- SUMMARY ---
    st.subheader("📈 Summary")

    total_spent = log_df[log_df["Type"] == "Expense"]["Total"].astype(float).sum()
    total_topup = log_df[log_df["Type"] == "Top-up"]["Total"].astype(float).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💸 Total Spent", f"${total_spent:.2f}")
    col2.metric("💰 Total Top-up", f"${total_topup:.2f}")
    col3.metric("🏦 Wallet", f"${st.session_state.wallet:.2f}")

    # --- LOGOUT ---
    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.session_state.user = None
        st.rerun()
