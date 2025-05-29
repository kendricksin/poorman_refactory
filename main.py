import streamlit as st
import sqlite3
import os

# Set page config FIRST - before any other Streamlit commands
st.set_page_config(page_title="Poor Mans Refactoring", initial_sidebar_state="collapsed", layout="wide")

# Now import pages and other modules
from pages import browse_invoices, home, create_invoice, dashboard, user_management, cash_transfers_page
from database.init_db import init_db

# Initialize database if not exists (without displaying messages during initial load)
DB_PATH = "invoice.db"
database_just_initialized = False

if not os.path.exists(DB_PATH):
    init_db()
    database_just_initialized = True

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

def create_top_navigation():
    """Create persistent top navigation bar"""
    current_page = get_current_page()
    
    # Add custom CSS for better navigation styling
    st.markdown("""
    <style>
    .nav-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    }
    .nav-title {
        font-size: 1.5em;
        font-weight: bold;
        margin: 0;
        color: white;
    }
    .current-page-indicator {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin: 2px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stSelectbox > div > div {
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation container with styling
    st.markdown('<div class="nav-header">', unsafe_allow_html=True)
    
    # Top row with logo and user selection
    header_col1, header_col2, header_col3 = st.columns([2, 3, 2])
    
    with header_col1:
        st.markdown('<h2 class="nav-title">🏦 Invoice Refactoring</h2>', unsafe_allow_html=True)
    
    with header_col2:
        # User selection in the center
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username 
            FROM users 
            WHERE username != 'PLATFORM OWNER'
            ORDER BY username
        """)
        users = cursor.fetchall()
        
        if users:
            user_options = {f"{username} (ID: {user_id})": {"user_id": user_id, "username": username} 
                           for user_id, username in users}
            
            current_key = None
            if st.session_state.selected_user:
                current_user = st.session_state.selected_user
                current_key = f"{current_user['username']} (ID: {current_user['user_id']})"
            
            selected_key = st.selectbox(
                "👤 Active User:",
                options=["None"] + list(user_options.keys()),
                index=0 if current_key is None else list(user_options.keys()).index(current_key) + 1 if current_key in user_options else 0,
                key="top_user_selector"
            )
            
            if selected_key != "None" and selected_key != current_key:
                st.session_state.selected_user = user_options[selected_key]
                st.rerun()
            elif selected_key == "None":
                st.session_state.selected_user = None
    
    with header_col3:
        # Quick stats
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE status = 'Active'")
        active_count = cursor.fetchone()[0]
        st.metric("🟢 Active Deals", f"{active_count:,}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation buttons row
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns(6)
    
    nav_items = [
        ("Home", "🏠", nav_col1),
        ("Create Invoice", "📝", nav_col2),
        ("Browse Invoices", "🛒", nav_col3),
        ("Dashboard", "📊", nav_col4),
        ("User Management", "👤", nav_col5),
        ("Cash Transfers", "💰", nav_col6)
    ]
    
    for page_name, emoji, col in nav_items:
        with col:
            # Different styling for current page
            if page_name == current_page:
                st.markdown(f"""
                <div class="current-page-indicator">
                    {emoji} {page_name}
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(f"{emoji} {page_name}", key=f"nav_{page_name}", use_container_width=True):
                    navigate_to(page_name)
    
    st.markdown("---")

def create_user_status_bar():
    """Create a status bar showing current user and quick info"""
    if st.session_state.selected_user:
        # Get user summary
        user_id = st.session_state.selected_user["user_id"]
        username = st.session_state.selected_user["username"]
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE owner_user_id = ?", (user_id,))
        owned_invoices = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE buyer_user_id = ?", (user_id,))
        investments = cursor.fetchone()[0]
        
        st.success(f"✅ **Acting as: {username}** | 📋 {owned_invoices} invoices created | 💰 {investments} investments made")
    else:
        st.info("ℹ️ No user selected - select a user from the dropdown above to access full features")

# Main app
def main():
    # Show database initialization message only if it just happened
    global database_just_initialized
    if database_just_initialized:
        st.success("✅ Database initialized successfully!")
        database_just_initialized = False
    
    # Create persistent top navigation
    create_top_navigation()
    
    # User status bar
    create_user_status_bar()
    
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