import streamlit as st
from models import invoice as invoice_model
from utils.helpers import check_invoice_activation

def app(conn):
    st.title("Create New Invoice")
    
    if not st.session_state.user:
        st.warning("Please log in first")
        return
    
    with st.form("invoice_form"):
        debtor = st.text_input("Debtor Name")
        original_amount = st.number_input("Original Amount (THB)", min_value=100.0)
        terms = st.text_input("Payment Terms (e.g., Net 30)")
        sale_price = st.number_input("Desired Sale Price (THB)", min_value=100.0)
        submit = st.form_submit_button("Create Invoice")
        
        if submit:
            owner_id = st.session_state.user["user_id"]
            invoice_id = invoice_model.create_invoice(
                conn, owner_id, debtor, original_amount, terms, sale_price
            )
            
            st.success(f"Invoice created successfully! ID: {invoice_id}")
            st.balloons()
            
            # Check if activation needed
            check_invoice_activation(conn, invoice_id)