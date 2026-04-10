# ---------------- LENDING ----------------
with lend_tab:
    person = st.text_input("Person Name")
    amount = st.number_input("Amount", min_value=0.0)
    note = st.text_input("Reminder")

    if st.button("Lend"):
        if amount > 0:
            # 💸 Deduct from wallet
            st.session_state.wallet -= amount

            # 🧾 Save to lending table
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

            # 🧾 ALSO save as transaction
            new_tx = pd.DataFrame([[
                datetime.now(),
                st.session_state.user,
                "Lend",
                amount,
                f"Lent to {person}",
                st.session_state.wallet
            ]], columns=transactions.columns)

            transactions = pd.concat([transactions, new_tx], ignore_index=True)
            save_data(transactions, FILES["transactions"])

            st.success(f"Lent ${amount:.2f} to {person}")
        else:
            st.warning("Enter a valid amount")

    # Show user's lending records
    st.subheader("Your Lending Records")
    st.dataframe(lending[lending["User"] == st.session_state.user])
