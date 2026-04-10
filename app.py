import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIG ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

# Required Columns
LOG_COLS = ["Date", "User", "Location", "Stall", "Product", "Extras", "Price", "Wallet Left", "Type"]

st.set_page_config(page_title="Pro Finance System", layout="wide")

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
            st.error("Invalid Login")
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            pd.DataFrame([{"Username": nu, "Password": np}]).to_csv(USER_FILE, mode='a', index=False, header=not os.path.exists(USER_FILE))
            st.success("Registered!")
    st.stop()

# --- 4. NAVIGATION ---
current_user = st.session_state.user
menu = ["🏠 Home", "🛒 Order Food", "💵 Top Up", "🤝 Lending", "📊 History"]
if current_user == SUPER_USER:
    menu.append("🛠️ SUPERADMIN SPACE")

choice = st.sidebar.radio("Navigation", menu)
if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.rerun()

# User Data
user_log = log_df[log_df["User"] == current_user]
try:
    balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0
except:
    balance = 0.0

# --- 5. SPACES ---

if choice == "🛠️ SUPERADMIN SPACE":
    st.title("🛡️ Admin Command Center")
    t_acc, t_logs, t_setup = st.tabs(["👤 Accounts", "📋 Global Logs", "🍱 Menu Manager"])
    
    with t_acc:
        st.subheader("Decoded Passwords")
        st.dataframe(user_df, use_container_width=True)
        
    with t_logs:
        st.subheader("System Activity")
        st.dataframe(log_df[log_df["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)
        
    with t_setup:
        st.subheader("➕ Add New Menu Item")
        with st.form("menu_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                loc_in = st.text_input("Location (e.g., Canteen A)")
                stall_in = st.text_input("Stall Name (e.g., Chicken Rice)")
            with col2:
                prod_in = st.text_input("Product Name (e.g., Roasted Chicken)")
                extra_in = st.text_input("Extras (e.g., Extra Rice, Egg)")
            
            price_in = st.number_input("Price ($)", min_value=0.0, step=0.10)
            
            if st.form_submit_button("Inject into Global System"):
                if loc_in and prod_in:
                    new_item = pd.DataFrame([{
                        "Date": "MASTER", "User": "ADMIN", "Location": loc_in, 
                        "Stall": stall_in, "Product": prod_in, "Extras": extra_in, 
                        "Price": str(price_in), "Wallet Left": "0", "Type": "MenuSetup"
                    }])
                    new_item.to_csv(LOG_FILE, mode='a', index=False)
                    st.success(f"Added {prod_in} to the menu!")
                    st.rerun()

elif choice == "🛒 Order Food":
    st.header("Place Your Order")
    menu_data = log_df[log_df["Type"] == "MenuSetup"]
    
    if not menu_data.empty:
        l_sel = st.selectbox("Location", menu_data["Location"].unique())
        stalls = menu_data[menu_data["Location"] == l_sel]["Stall"].unique()
        s_sel = st.selectbox("Stall", stalls)
        
        prods = menu_data[(menu_data["Location"] == l_sel) & (menu_data["Stall"] == s_sel)]
        p_sel = st.selectbox("Product", prods["Product"].unique())
        
        details = prods[prods["Product"] == p_sel].iloc[-1]
        st.info(f"**Extras included:** {details['Extras']} | **Price:** ${float(details['Price']):.2f}")
        
        if st.button("Confirm Purchase", type="primary"):
            cost = float(details['Price'])
            new_tx = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"), "User": current_user,
                "Location": l_sel, "Stall": s_sel, "Product": p_sel, "Extras": details['Extras'],
                "Price": str(cost), "Wallet Left": str(balance - cost), "Type": "Spend"
            }])
            new_tx.to_csv(LOG_FILE, mode='a', index=False)
            st.balloons(); st.rerun()
    else:
        st.warning("No menu items available. Admin needs to add them in 'Superadmin Space'.")

elif choice == "🏠 Home":
    st.title(f"Hello, {current_user}")
    st.metric("My Balance", f"${balance:,.2f}")

elif choice == "📊 History":
    st.header("My Activity")
    st.dataframe(user_log[user_log["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)
