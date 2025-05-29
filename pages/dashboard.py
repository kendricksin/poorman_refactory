# pages/dashboard.py

import streamlit as st
from models import invoice as invoice_model
from models import transaction as transaction_model
from utils.helpers import process_invoice_owner_payment, format_currency

def app(conn):
    st.title("Your Dashboard")
    
    if not st.session_state.selected_user:
        st.warning("Please select a user in the User Management tab first")
        return
    
    user_id = st.session_state.selected_user["user_id"]
    
    # Owned Invoices Section
    st.subheader("Your Invoices")
    owned_invoices = invoice_model.get_invoices_by_owner(conn, user_id)
    
    if owned_invoices:
        for invoice in owned_invoices:
            invoice_id, _, debtor, amount, _, sale_price, _, _, status = invoice
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{debtor}** - {format_currency(amount)} | Status: {status}")
            
            with col2:
                if status == 'Active':
                    if st.button("Mark as Paid", key=f"pay_{invoice_id}"):
                        process_invoice_owner_payment(conn, invoice_id, user_id)
                        st.success("Invoice marked as paid!")
                        st.experimental_rerun()
    else:
        st.info("You haven't created any invoices yet")