import streamlit as st

def app(conn):
    st.title("Welcome to Invoice Refactoring MVP")
    
    st.markdown("""
    ### How It Works
    1. **Create Invoices**: Submit your outstanding invoices for immediate cash
    2. **Buy Chunks**: Invest in high-yield invoice chunks from ฿100
    3. **Get Paid**: Collect returns when debtors settle the original invoice
    
    #### Key Benefits
    - No complex authentication required
    - Transparent transaction tracking
    - Simple cash flow visualization
    """)