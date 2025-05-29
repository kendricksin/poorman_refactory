import streamlit as st
from models import invoice as invoice_model
from models import transaction as transaction_model

def app(conn):
    st.title("Your Dashboard")
    
    if not st.session_state.user:
        st.warning("Please log in first")
        return
    
    user_id = st.session_state.user['user_id']
    
    # Owned Invoices Tab
    st.subheader("Your Invoices")
    owned_invoices = invoice_model.get_invoices_by_owner(conn, user_id)
    
    if owned_invoices:
        for invoice in owned_invoices:
            invoice_id, _, debtor, amount, _, sale_price, _, _, status = invoice
            st.write(f"**{debtor}** - {format_currency(amount)} | Status: {status}")
    else:
        st.info("You haven't created any invoices yet")
    
    # Investments Tab
    st.subheader("Your Investments")
    investments = transaction_model.get_user_transactions(conn, user_id)
    
    if investments:
        for trans in investments:
            _, invoice_id, _, chunks, status, _ = trans
            st.write(f"Invoice #{invoice_id} - {chunks} chunks | Status: {status}")
    else:
        st.info("You haven't invested in any invoices yet")