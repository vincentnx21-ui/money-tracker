import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIG & SETUP ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

# Expanded columns to handle "Extras Price" and "Reminders"
LOG_COLS = ["Date", "User", "Location", "Stall", "Product", "Extras", "Price", "Extra_Price", "Total", "Wallet_Left", "Type", "Note"]

st.set_page_config(page_title="Finance & Canteen System", layout="wide")

# --- 2. DATA ENGINE ---
def load_data(file, default_cols):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file, dtype=str)
            # FORCE MISSING COLUMNS: This prevents the KeyError!
            for col in default_cols:
                if col not in df.columns:
                    df[col] = "0" if "Price" in col else "N/A"
            return df
        except:
            return pd.DataFrame(columns=default_cols)
    # If file doesn't exist, create an empty one with correct headers
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
        if st.button("Login"):
            if (u == SUPER_USER and p == SUPER_PASS) or (not user_df.empty and not user_df[(user_df["Username"] == u) & (user_df["Password"] == p)].empty):
                st.session_state.auth, st.session_state.user = True, u
                st.rerun()
            else: st.error("Access Denied")
    with t2:
        nu, np = st.text_input("New Username"), st.text_input("New Password", type="password")
        if st.button("Register"):
            pd.DataFrame([{"Username": nu, "Password": np}]).to_csv(USER_FILE, mode='a', index=False, header=not os.path.exists(USER_FILE))
            st.success("Account created!")
    st.stop()

# --- 4. NAVIGATION & SHARED HEADER ---
current_user = st.session_state.user
menu = ["🏠 Home", "🛒 Order Food", "💵 Top Up", "🤝 Lending", "📊 History"]
if current_user == SUPER_USER: menu.append("🛠️ SUPERADMIN SPACE")

with st.sidebar:
    st.title(f"👤 {current_user}")
    choice = st.radio("Go to:", menu)
    if st.button("Log Out"):
        st.session_state.auth = False
        st.rerun()

# Pre-calculate User Balance
user_log = log_df[log_df["User"] == current_user]
try: balance = float(user_log["Wallet_Left"].iloc[-1]) if not user_log.empty else 0.0
except: balance = 0.0

# --- UNIVERSAL TOP BAR (Shown on every tab) ---
st.metric(label="Your Wallet Balance", value=f"${balance:,.2f}")
st.divider()

# --- 5. FEATURE SPACES ---

if choice == "🏠 Home":
    st.subheader(f"Welcome back, {current_user}!")
    st.info("Select an option from the sidebar to manage your canteen orders or personal finances.")

elif choice == "🛒 Order Food":
    st.subheader("Canteen Menu")
    menu_data = log_df[log_df["Type"] == "MenuSetup"]
    if not menu_data.empty:
        col1, col2 = st.columns(2)
        with col1:
            l_sel = st.selectbox("Pick Location", menu_data["Location"].unique())
            s_sel = st.selectbox("Pick Stall", menu_data[menu_data["Location"] == l_sel]["Stall"].unique())
            prods = menu_data[(menu_data["Location"] == l_sel) & (menu_data["Stall"] == s_sel)]
            p_sel = st.selectbox("Pick Product", prods["Product"].unique())

        details = prods[prods["Product"] == p_sel].iloc[-1]
        
        # FIX: Safe conversion for Base Price and Extra Price
        base_p = float(details['Price']) if 'Price' in details else 0.0
        
        try:
            # Use .get() to avoid the crash if the column is missing
            extra_p = float(details.get('Extra_Price', 0))
        except:
            extra_p = 0.0
            
        grand_total = base_p + extra_p
        
        with col2:
            st.write(f"**Base Price:** ${base_p:.2f}")
            st.write(f"**Extra ({details['Extras']}):** ${extra_p:.2f}")
            st.markdown(f"### Grand Total: ${grand_total:.2f}")
            
            if st.button("🛒 Confirm & Pay", use_container_width=True):
                if balance >= grand_total:
                    new_row = pd.DataFrame([{
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "User": current_user,
                        "Location": l_sel, "Stall": s_sel, "Product": p_sel, "Extras": details['Extras'],
                        "Price": str(base_p), "Extra_Price": str(extra_p), "Total": str(grand_total),
                        "Wallet_Left": str(balance - grand_total), "Type": "Spend", "Note": "Food Order"
                    }])
                    new_row.to_csv(LOG_FILE, mode='a', index=False); st.balloons(); st.rerun()
                else: st.error("Insufficient Funds!")
    else: st.warning("Admin has not set the menu yet.")

elif choice == "💵 Top Up":
    st.subheader("Add Money")
    amt = st.number_input("Amount ($)", min_value=0.0, step=1.0)
    if st.button("Add Funds"):
        new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "User": current_user, "Location": "N/A", "Stall": "Wallet", "Product": "Deposit", "Extras": "N/A", "Price": str(amt), "Extra_Price": "0", "Total": str(amt), "Wallet_Left": str(balance + amt), "Type": "TopUp", "Note": "N/A"}])
        new_row.to_csv(LOG_FILE, mode='a', index=False); st.rerun()

elif choice == "🤝 Lending":
    st.subheader("Lending Tracker")
    f_name = st.text_input("Borrower Name")
    l_amt = st.number_input("Amount to Lend", min_value=0.0)
    l_note = st.text_input("Set a Reminder (e.g., Pay back by Friday)")
    if st.button("Record Loan"):
        if balance >= l_amt:
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "User": current_user, "Location": "N/A", "Stall": "Lending", "Product": f"Lent to {f_name}", "Extras": "N/A", "Price": str(l_amt), "Extra_Price": "0", "Total": str(l_amt), "Wallet_Left": str(balance - l_amt), "Type": "Lend", "Note": l_note}])
            new_row.to_csv(LOG_FILE, mode='a', index=False); st.rerun()
        else: st.error("Not enough money!")

elif choice == "📊 History":
    st.subheader("Your Transaction History")
    st.dataframe(user_log[user_log["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)
    st.divider()
        st.subheader("🗑️ Delete Transaction")
        # Let the user pick a transaction by its index
        if not user_log.empty:
            target = st.selectbox("Select entry to remove:", user_log.index, 
                                 format_func=lambda x: f"{user_log.loc[x, 'Date']} - {user_log.loc[x, 'Product']}")
            
            if st.button("Delete Selected"):
                # Drop the row and update the CSV
                new_df = log_df.drop(target)
                new_df.to_csv(LOG_FILE, index=False)
                st.success("Deleted! Refreshing...")
                st.rerun()

# --- ADMIN FEATURES ---
elif choice == "🛠️ SUPERADMIN SPACE":
    t1, t2, t3 = st.tabs(["👥 Registered Users", "📈 Global Activity", "🍱 Set Canteen Menu"])
st.write("---")
        st.subheader("🗑️ Remove Menu Item")
        m_items = log_df[log_df["Type"] == "MenuSetup"]
        if not m_items.empty:
            m_target = st.selectbox("Select food to remove:", m_items.index,
                                   format_func=lambda x: f"{m_items.loc[x, 'Stall']} - {m_items.loc[x, 'Product']}")
            if st.button("Delete Item from Canteen"):
                new_log = log_df.drop(m_target)
                new_log.to_csv(LOG_FILE, index=False)
                st.rerun()
    
    with t1:
        st.write("### User Database (Plain Text Passwords)")
        st.dataframe(user_df, use_container_width=True)
        
    with t2:
        st.write("### All User Activities")
        st.dataframe(log_df[log_df["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)
        
    with t3:
        st.write("### Update Menu Settings")
        with st.form("menu_form"):
            c1, c2 = st.columns(2)
            loc = c1.text_input("Location")
            stl = c1.text_input("Stall Name")
            prd = c2.text_input("Product Name")
            ext = c2.text_input("Extras Description")
            b_p = st.number_input("Base Price", min_value=0.0)
            e_p = st.number_input("Extras Price", min_value=0.0)
            if st.form_submit_button("Add to System"):
                pd.DataFrame([{"Date": "MASTER", "User": "ADMIN", "Location": loc, "Stall": stl, "Product": prd, "Extras": ext, "Price": str(b_p), "Extra_Price": str(e_p), "Total": "0", "Wallet_Left": "0", "Type": "MenuSetup", "Note": "N/A"}]).to_csv(LOG_FILE, mode='a', index=False); st.rerun()
