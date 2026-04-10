import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. SETTINGS & CONFIG ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

# Column definitions to prevent KeyError
USER_COLS = ["Username", "Password"]
LOG_COLS = ["Date", "User", "Location", "Shop", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"]

st.set_page_config(page_title="Advanced Finance System", layout="wide")

# --- 2. DATA ENGINE (With Auto-Repair) ---
def load_data(file, default_cols):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file, dtype=str)
            # Check if all required columns exist; if not, fix the dataframe
            for col in default_cols:
                if col not in df.columns:
                    df[col] = "N/A"
            return df
        except:
            return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# Load data with safety nets
user_df = load_data(USER_FILE, USER_COLS)
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
        if st.button("Log In"):
            if u == SUPER_USER and p == SUPER_PASS:
                st.session_state.auth, st.session_state.user = True, u
                st.rerun()
            elif not user_df.empty:
                match = user_df[(user_df["Username"] == u) & (user_df["Password"] == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user = True, u
                    st.rerun()
                else: st.error("Wrong username or password.")
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Register Account"):
            if nu and np:
                new_user = pd.DataFrame([{"Username": nu, "Password": np}])
                new_user.to_csv(USER_FILE, mode='a', index=False, header=not os.path.exists(USER_FILE))
                st.success("Success! You can now log in.")
    st.stop()

# --- 4. NAVIGATION ---
current_user = st.session_state.user
menu = ["🏠 Home", "🛒 Order Food", "💵 Top Up", "🤝 Lending", "📊 My History"]

if current_user == SUPER_USER:
    menu.append("🛠️ SUPERADMIN SPACE")

with st.sidebar:
    st.title(f"👤 {current_user}")
    choice = st.radio("Go to:", menu)
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# Pre-calculate user data
user_log = log_df[log_df["User"] == current_user]
try:
    balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0
except:
    balance = 0.0

# --- 5. INTERFACE ---

if choice == "🛠️ SUPERADMIN SPACE":
    st.header("🛡️ Admin Command Center")
    t_acc, t_logs, t_menu = st.tabs(["User Registry", "Global Activity", "System Setup"])
    
    with t_acc:
        st.subheader("Decoded Account Data")
        st.dataframe(user_df, use_container_width=True) # Passwords visible here
        
    with t_logs:
        st.subheader("Full Transaction Log")
        st.dataframe(log_df[log_df["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)
        
    with t_menu:
        st.subheader("Global Menu Manager")
        c1, c2, c3 = st.columns(3)
        loc_in = c1.text_input("Location")
        item_in = c2.text_input("Item Name")
        price_in = c3.number_input("Price", min_value=0.0)
        if st.button("Add to Global System"):
            new_item = pd.DataFrame([{
                "Date": "MASTER", "User": "ADMIN", "Location": loc_in, "Shop": "N/A",
                "Item": item_in, "Quantity": "1", "Total Cost": str(price_in), 
                "Wallet Left": "0", "Type": "MenuSetup"
            }])
            new_item.to_csv(LOG_FILE, mode='a', index=False); st.success("Added!"); st.rerun()

elif choice == "🏠 Home":
    st.title(f"Hello, {current_user}")
    st.metric("Your Balance", f"${balance:,.2f}")

elif choice == "🛒 Order Food":
    st.header("Order")
    menu_items = log_df[log_df["Type"] == "MenuSetup"]
    if not menu_items.empty:
        l_list = menu_items["Location"].unique()
        l_sel = st.selectbox("Where are you?", l_list)
        p_list = menu_items[menu_items["Location"] == l_sel]["Item"].unique()
        p_sel = st.selectbox("What do you want?", p_list)
        u_price = float(menu_items[menu_items["Item"] == p_sel].iloc[-1]["Total Cost"])
        st.write(f"Price: ${u_price:.2f}")
        if st.button("Buy Now"):
            new_tx = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"), "User": current_user,
                "Location": l_sel, "Shop": "N/A", "Item": p_sel, "Quantity": "1",
                "Total Cost": str(u_price), "Wallet Left": str(balance - u_price), "Type": "Spend"
            }])
            new_tx.to_csv(LOG_FILE, mode='a', index=False); st.balloons(); st.rerun()
    else:
        st.warning("Admin has not added any food items yet.")

elif choice == "📊 My History":
    st.header("My Transactions")
    st.dataframe(user_log[user_log["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)
