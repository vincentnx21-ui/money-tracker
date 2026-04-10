import streamlit as st
import pandas as pd
from datetime import datetime
import os
import hashlib

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Finance & Canteen System", layout="wide")

FILES = {
    "users": "users.csv",
    "transactions": "transactions.csv",
    "menu": "menu.csv",
    "extras": "extras.csv",
    "lending": "lending.csv"
}

SUPER_USER = "admin"
SUPER_PASS = "admin123"

# ---------------- HELPERS ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file, on_bad_lines='skip')
            return df.reindex(columns=columns)
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# ---------------- LOAD DATA ----------------
users = load_data(FILES["users"], ["Username", "Password"])
transactions = load_data(FILES["transactions"], ["Date","User","Type","Amount","Details","Wallet"])
menu = load_data(FILES["menu"], ["Location","Stall","Product","Price"])
extras = load_data(FILES["extras"], ["Extra","Price"])
lending = load_data(FILES["lending"], ["Date","User","Person","Amount","Note","Repaid"])

# ---------------- SESSION ----------------
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None
    st.session_state.wallet = 0.0

# ---------------- LOGIN / REGISTER ----------------
if not st.session_state.auth:
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            hp = hash_password(p)

            valid = (
                (u == SUPER_USER and p == SUPER_PASS) or
                ((users["Username"] == u) & (users["Password"] == hp)).any()
            )

            if valid:
                st.session_state.auth = True
                st.session_state.user = u

                user_tx = transactions[transactions["User"] == u]
                if not user_tx.empty:
                    st.session_state.wallet = float(user_tx.iloc[-1]["Wallet"])

                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")

        if st.button("Register"):
            if nu in users["Username"].values:
                st.warning("User exists")
            elif nu and np:
                new = pd.DataFrame([[nu, hash_password(np)]], columns=["Username","Password"])
                users = pd.concat([users, new], ignore_index=True)
                save_data(users, FILES["users"])
                st.success("Registered!")
            else:
                st.warning("Fill all fields")

# ---------------- MAIN APP ----------------
else:
    st.title("💰 Finance & Canteen System")

    st.sidebar.write(f"👤 {st.session_state.user}")

    # Wallet display
    st.sidebar.metric("Wallet", f"${st.session_state.wallet:.2f}")

    menu_tab, topup_tab, lend_tab, history_tab = st.tabs(["🍽 Order", "💵 Top-up", "🤝 Lending", "📜 History"])

    # ---------------- ORDER ----------------
    with menu_tab:
        st.subheader("Order Food")

        if not menu.empty:
            location = st.selectbox("Location", menu["Location"].dropna().unique())

            stall = st.selectbox(
                "Stall",
                menu[menu["Location"] == location]["Stall"].dropna().unique()
            )

            products = menu[(menu["Location"] == location) & (menu["Stall"] == stall)]
            product = st.selectbox("Product", products["Product"])

            price = float(products[products["Product"] == product]["Price"].values[0])
        else:
            st.warning("No menu available")
            price = 0

        st.write(f"Base Price: ${price}")

        # Extras
        if not extras.empty:
            extra_selected = st.multiselect("Extras", extras["Extra"])
            extra_price = extras[extras["Extra"].isin(extra_selected)]["Price"].astype(float).sum()
        else:
            extra_selected = []
            extra_price = 0

        total = price + extra_price
        st.subheader(f"Total: ${total:.2f}")

        if st.button("Confirm Order"):
            st.session_state.wallet -= total

            new_tx = pd.DataFrame([[
                datetime.now(),
                st.session_state.user,
                "Expense",
                total,
                f"{product} + {', '.join(extra_selected)}",
                st.session_state.wallet
            ]], columns=transactions.columns)

            transactions = pd.concat([transactions, new_tx], ignore_index=True)
            save_data(transactions, FILES["transactions"])

            st.success("Order saved!")

    # ---------------- TOP-UP ----------------
    with topup_tab:
        amount = st.number_input("Top-up amount", min_value=0.0)

        if st.button("Add Money"):
            st.session_state.wallet += amount

            new_tx = pd.DataFrame([[
                datetime.now(),
                st.session_state.user,
                "Top-up",
                amount,
                "Top-up",
                st.session_state.wallet
            ]], columns=transactions.columns)

            transactions = pd.concat([transactions, new_tx], ignore_index=True)
            save_data(transactions, FILES["transactions"])

            st.success("Money added!")

    # ---------------- LENDING ----------------
    with lend_tab:
        person = st.text_input("Person Name")
        amount = st.number_input("Amount", min_value=0.0)
        note = st.text_input("Reminder")

        if st.button("Lend"):
            new_lend = pd.DataFrame([[
                datetime.now(),
                st.session_state.user,
                person,
                amount,
                note,
                "No"
            ]], columns=lending.columns)

            lending = pd.concat([lending, new_lend], ignore_index=True)
            save_data(lending, FILES["lending"])

            st.success("Lending recorded!")

        st.dataframe(lending[lending["User"] == st.session_state.user])

    # ---------------- HISTORY ----------------
    with history_tab:
        st.dataframe(transactions[transactions["User"] == st.session_state.user])

    # ---------------- ADMIN PANEL ----------------
    if st.session_state.user == SUPER_USER:
        st.sidebar.subheader("🛠 Admin Panel")

        if st.sidebar.checkbox("View Users"):
            st.dataframe(users)

        if st.sidebar.checkbox("View Transactions"):
            st.dataframe(transactions)

        if st.sidebar.checkbox("Edit Menu"):
            loc = st.text_input("Location")
            stall = st.text_input("Stall")
            prod = st.text_input("Product")
            price = st.number_input("Price", min_value=0.0)

            if st.button("Add Menu Item"):
                new = pd.DataFrame([[loc, stall, prod, price]], columns=menu.columns)
                menu = pd.concat([menu, new], ignore_index=True)
                save_data(menu, FILES["menu"])
                st.success("Added!")

        if st.sidebar.checkbox("Edit Extras"):
            ex = st.text_input("Extra")
            pr = st.number_input("Extra Price", min_value=0.0)

            if st.button("Add Extra"):
                new = pd.DataFrame([[ex, pr]], columns=extras.columns)
                extras = pd.concat([extras, new], ignore_index=True)
                save_data(extras, FILES["extras"])
                st.success("Added!")

    # Logout
    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.session_state.user = None
        st.rerun()
