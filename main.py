import streamlit as st
import sqlite3
from pages import home, create_invoice, browse_invoices, dashboard

# Initialize database
import database.init_db

# Set page config
st.set_page_config(page_title="Invoice Refactoring MVP", layout="wide")

# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect("invoice.db", check_same_thread=False)

conn = get_connection()

# Navigation
PAGES = {
    "Home": home,
    "Create Invoice": create_invoice,
    "Browse Invoices": browse_invoices,
    "Dashboard": dashboard
}

# Session state initialization
if "user" not in st.session_state:
    st.session_state.user = None

def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    
    if st.session_state.user:
        st.sidebar.success(f"Logged in as {st.session_state.user['username']}")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()
    
    page = PAGES[selection]
    page.app(conn)

if __name__ == "__main__":
    main()