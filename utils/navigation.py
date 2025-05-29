# utils/navigation.py

import streamlit as st

def navigate_to(page_name):
    """Navigate to a specific page"""
    st.session_state.current_page = page_name
    st.rerun()

def get_current_page():
    """Get the current page from session state"""
    return st.session_state.get('current_page', 'Home')

def create_nav_button(label, page_name, emoji="", use_container_width=False, key=None):
    """Create a navigation button that switches pages"""
    button_label = f"{emoji} {label}" if emoji else label
    
    if st.button(button_label, use_container_width=use_container_width, key=key):
        navigate_to(page_name)

def create_nav_link(label, page_name, emoji="", help_text=""):
    """Create a navigation link that switches pages"""
    link_label = f"{emoji} {label}" if emoji else label
    
    if st.button(link_label, help=help_text, use_container_width=True):
        navigate_to(page_name)

def init_navigation():
    """Initialize navigation session state"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'

def create_breadcrumb_nav(current_page):
    """Create breadcrumb navigation"""
    breadcrumbs = {
        'Home': ['🏠 Home'],
        'Create Invoice': ['🏠 Home', '📝 Create Invoice'],
        'Browse Invoices': ['🏠 Home', '🛒 Browse Invoices'],
        'Dashboard': ['🏠 Home', '📊 Dashboard'],
        'User Management': ['🏠 Home', '👤 User Management'],
        'Cash Transfers': ['🏠 Home', '💰 Cash Transfers']
    }
    
    if current_page in breadcrumbs:
        breadcrumb_items = breadcrumbs[current_page]
        
        # Create clickable breadcrumbs
        cols = st.columns(len(breadcrumb_items))
        
        for i, (col, item) in enumerate(zip(cols, breadcrumb_items)):
            with col:
                if i == len(breadcrumb_items) - 1:  # Current page
                    st.markdown(f"**{item}**")
                else:  # Clickable previous pages
                    page_name = item.split(' ', 1)[1] if ' ' in item else item
                    if st.button(item, key=f"breadcrumb_{i}"):
                        navigate_to(page_name)
        
        st.markdown("---")

def create_quick_actions():
    """Create quick action buttons for common tasks"""
    st.markdown("### ⚡ Quick Actions")
    
    if not st.session_state.selected_user:
        st.info("👆 Select a user to see quick actions")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_nav_button("Create Invoice", "Create Invoice", "📝", use_container_width=True)
    
    with col2:
        create_nav_button("Browse Deals", "Browse Invoices", "🛒", use_container_width=True)
    
    with col3:
        create_nav_button("My Dashboard", "Dashboard", "📊", use_container_width=True)