import streamlit as st
import sqlite3
from pages import browse_invoices, home, create_invoice, dashboard, user_management, cash_transfers_page

def navigate_to(page_name):
    """Navigate to a specific page"""
    st.session_state.current_page = page_name
    st.rerun()

def get_current_page():
    """Get the current page from session state"""
    return st.session_state.get('current_page', 'Home')

def init_navigation():
    """Initialize navigation session state"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'

# Initialize database
import database.init_db

# Set page config
st.set_page_config(page_title="Invoice Refactoring MVP", layout="wide")

# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect("invoice.db", check_same_thread=False)

conn = get_connection()

# Ensure PLATFORM OWNER exists
def ensure_platform_owner():
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = 'PLATFORM OWNER'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username) VALUES ('PLATFORM OWNER')")
        conn.commit()

ensure_platform_owner()

# Session state initialization
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None

# Initialize navigation
init_navigation()

def create_sidebar_navigation():
    """Create sidebar navigation with current page highlighting"""
    st.sidebar.title("🏦 Navigation")
    
    current_page = get_current_page()
    
    # Navigation buttons
    nav_items = [
        ("Home", "🏠"),
        ("Create Invoice", "📝"),
        ("Browse Invoices", "🛒"),
        ("Dashboard", "📊"),
        ("User Management", "👤"),
        ("Cash Transfers", "💰")
    ]
    
    for page_name, emoji in nav_items:
        # Highlight current page
        if page_name == current_page:
            st.sidebar.markdown(f"**{emoji} {page_name}** ←")
        else:
            if st.sidebar.button(f"{emoji} {page_name}", key=f"nav_{page_name}"):
                navigate_to(page_name)

def sidebar_user_selection():
    """Handle user selection in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 Current User")
    
    # Get all users (excluding PLATFORM OWNER)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username 
        FROM users 
        WHERE username != 'PLATFORM OWNER'
        ORDER BY username
    """)
    users = cursor.fetchall()
    
    if not users:
        st.sidebar.warning("No users found. Create a user first!")
        return
    
    # Create user options
    user_options = {f"{username} (ID: {user_id})": {"user_id": user_id, "username": username} 
                   for user_id, username in users}
    
    # Current selection for selectbox
    current_key = None
    if st.session_state.selected_user:
        current_user = st.session_state.selected_user
        current_key = f"{current_user['username']} (ID: {current_user['user_id']})"
    
    # User selection dropdown
    selected_key = st.sidebar.selectbox(
        "Select Active User:",
        options=["None"] + list(user_options.keys()),
        index=0 if current_key is None else list(user_options.keys()).index(current_key) + 1 if current_key in user_options else 0,
        key="user_selector"
    )
    
    if selected_key != "None" and selected_key != current_key:
        st.session_state.selected_user = user_options[selected_key]
        st.rerun()
    elif selected_key == "None":
        st.session_state.selected_user = None
    
    # Show selected user info
    if st.session_state.selected_user:
        st.sidebar.success(f"✅ {st.session_state.selected_user['username']}")
    else:
        st.sidebar.info("No user selected")

# Main app
def main():
    # Create sidebar navigation
    create_sidebar_navigation()
    
    # Add user selection to sidebar
    sidebar_user_selection()
    
    # Quick stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Quick Stats")
    
    cursor = conn.cursor()
    
    # Total invoices
    cursor.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = cursor.fetchone()[0]
    
    # Active invoices
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE status = 'Active'")
    active_invoices = cursor.fetchone()[0]
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    st.sidebar.metric("Total Invoices", f"{total_invoices:,}")
    st.sidebar.metric("Active Invoices", f"{active_invoices:,}")
    st.sidebar.metric("Total Users", f"{total_users:,}")
    
    # Get current page and run it
    current_page = get_current_page()
    
    # Page routing
    if current_page == "Home":
        home.app(conn)
    elif current_page == "Create Invoice":
        create_invoice.app(conn)
    elif current_page == "Browse Invoices":
        browse_invoices.app(conn)
    elif current_page == "Dashboard":
        dashboard.app(conn)
    elif current_page == "User Management":
        user_management.app(conn)
    elif current_page == "Cash Transfers":
        cash_transfers_page.app(conn)
    else:
        # Default to home if unknown page
        st.session_state.current_page = "Home"
        st.rerun()

if __name__ == "__main__":
    main()