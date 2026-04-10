import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIG ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

# Standardizing columns for every transaction type
LOG_COLS = ["Date", "User", "Location", "Stall", "Product", "Extras", "Price", "Wallet Left", "Type"]

st.set_page_config(page_title="Unified Finance System", layout="wide")

# --- 2. DATA ENGINE ---
def load_data(file, default_cols):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file, dtype=str)
            for col in default_cols:
                if col not in df.columns: df[col] = "N/A"
            return df
        except:
            return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

user_df = load_data(USER_FILE, ["Username", "Password"])
log_df = load_data(LOG_FILE, LOG_COLS)

# --- 3. AUTHENTICATION ---
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

if not st.session_state.auth:
    t1, t2 = st.tabs(["🔒 Login", "📝 Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Enter"):
            if u == SUPER_USER and p == SUPER_PASS:
                st.session_state.auth, st.session_state.user = True, u
                st.rerun()
            elif not user_df.empty:
                match = user_df[(user_df["Username"] == u) & (user_df["Password"] == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user = True, u
                    st.rerun()
            st.error("Invalid Login Credentials")
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            pd.DataFrame([{"Username": nu, "Password": np}]).to_csv(USER_FILE, mode='a', index=False, header=not os.path.exists(USER_FILE))
            st.success("Registered successfully!")
    st.stop()

# --- 4. NAVIGATION ---
current_user = st.session_state.user
menu = ["🏠 Home", "🛒 Order Food", "💵 Top Up", "🤝 Lending", "📊 History"]
if current_user == SUPER_USER:
    menu.append("🛠️ SUPERADMIN SPACE")

choice = st.sidebar.radio("Navigation", menu)

# --- 5. SHARED DATA LOGIC ---
user_log = log_df[log_df["User"] == current_user]
try:
    balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0
except:
    balance = 0.0

# --- 6. FEATURE SPACES ---

if choice == "🏠 Home":
    st.title(f"Welcome, {current_user}!")
    st.metric("My Current Balance", f"${balance:,.2f}")

elif choice == "💵 Top Up":
    st.header("Wallet Top Up")
    st.write("Add funds to your digital wallet.")
    amount = st.number_input("Enter Amount ($)", min_value=0.0, step=1.0)
    
    if st.button("Confirm Deposit", type="primary"):
        if amount > 0:
            new_row = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "User": current_user,
                "Location": "N/A", "Stall": "Wallet", "Product": "Deposit", "Extras": "N/A",
                "Price": str(amount),
                "Wallet Left": str(balance + amount),
                "Type": "TopUp"
            }])
            new_row.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))
            st.success(f"Added ${amount:.2f} to your account!")
            st.rerun()

elif choice == "🤝 Lending":
    st.header("Money Lending")
    st.write("Track money you have lent to others.")
    friend_name = st.text_input("Friend's Name")
    lend_amount = st.number_input("Amount Lent ($)", min_value=0.0, step=0.10)
    
    if st.button("Record Loan"):
        if friend_name and lend_amount > 0:
            if balance >= lend_amount:
                new_row = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "User": current_user,
                    "Location": "Lending", "Stall": "N/A", 
                    "Product": f"Lent to {friend_name}", "Extras": "N/A",
                    "Price": str(lend_amount),
                    "Wallet Left": str(balance - lend_amount),
                    "Type": "Lend"
                }])
                new_row.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))
                st.warning(f"Recorded ${lend_amount:.2f} lent to {friend_name}.")
                st.rerun()
            else:
                st.error("Insufficient balance to lend this amount.")

elif choice == "🛒 Order Food":
    st.header("Canteen Ordering")
    menu_items = log_df[log_df["Type"] == "MenuSetup"]
    if not menu_items.empty:
        l_sel = st.selectbox("Location", menu_items["Location"].unique())
        s_sel = st.selectbox("Stall", menu_items[menu_items["Location"] == l_sel]["Stall"].unique())
        prods = menu_items[(menu_items["Location"] == l_sel) & (menu_items["Stall"] == s_sel)]
        p_sel = st.selectbox("Product", prods["Product"].unique())
        
        details = prods[prods["Product"] == p_sel].iloc[-1]
        price = float(details['Price'])
        st.info(f"**Includes:** {details['Extras']} | **Price:** ${price:.2f}")
        
        if st.button("Confirm Purchase"):
            if balance >= price:
                new_tx = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "User": current_user,
                    "Location": l_sel, "Stall": s_sel, "Product": p_sel, "Extras": details['Extras'],
                    "Price": str(price), "Wallet Left": str(balance - price), "Type": "Spend"
                }])
                new_tx.to_csv(LOG_FILE, mode='a', index=False)
                st.balloons(); st.rerun()
            else:
                st.error("Insufficient balance!")
    else:
        st.warning("Menu is empty. Admin must add items in Superadmin Space.")

elif choice == "📊 History":
    st.header("Transaction History")
    st.dataframe(user_log[user_log["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)

elif choice == "🛠️ SUPERADMIN SPACE":
    st.title("🛡️ Admin Dashboard")
    adm_t1, adm_t2, adm_t3 = st.tabs(["👤 Accounts", "📂 Global Logs", "🍱 Menu Setup"])
    
    with adm_t1:
        st.dataframe(user_df, use_container_width=True)
        
    with adm_t2:
        st.dataframe(log_df[log_df["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)
        
    with adm_t3:
        with st.form("admin_menu"):
            al = st.text_input("Location")
            as_ = st.text_input("Stall")
            ap = st.text_input("Product")
            ae = st.text_input("Extras")
            price = st.number_input("Price", min_value=0.0)
            if st.form_submit_button("Add to Menu"):
                new_m = pd.DataFrame([{
                    "Date": "MASTER", "User": "ADMIN", "Location": al, "Stall": as_, 
                    "Product": ap, "Extras": ae, "Price": str(price), 
                    "Wallet Left": "0", "Type": "MenuSetup"
                }])
                new_m.to_csv(LOG_FILE, mode='a', index=False); st.rerun()

with st.sidebar:
    st.divider()
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()
