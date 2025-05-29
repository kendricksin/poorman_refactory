import streamlit as st
import sqlite3
from pages import browse_invoices, home, create_invoice, dashboard, user_management, cash_transfers_page

# Initialize database
import database.init_db

# Set page config
st.set_page_config(page_title="Invoice Refactoring MVP", layout="wide")

# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect("invoice.db", check_same_thread=False)

conn = get_connection()

# Session state initialization
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None

# Navigation
PAGES = {
    "Home": home,
    "Create Invoice": create_invoice,
    "Browse Invoices": browse_invoices,
    "Dashboard": dashboard,
    "User Management": user_management,
    "Cash Transfers": cash_transfers_page
}

# Main app
def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    
    # Show selected user info
    if st.session_state.selected_user:
        st.sidebar.info(f"Current User: {st.session_state.selected_user['username']} (ID: {st.session_state.selected_user['user_id']})")
    
    page = PAGES[selection]
    page.app(conn)

if __name__ == "__main__":
    main()