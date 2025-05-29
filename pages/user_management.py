import streamlit as st
from models import user as user_model

def navigate_to(page_name):
    """Navigate to a specific page"""
    st.session_state.current_page = page_name
    st.rerun()

def app(conn):
    # Breadcrumb navigation
    st.markdown("🏠 [Home](#) > 👤 **User Management**")
    if st.button("← Back to Home", key="back_to_home"):
        navigate_to("Home")
    st.markdown("---")
    
    st.title("👤 User Management")
    st.markdown("**Create and manage user accounts for the platform**")
    
    # Form to add new user
    st.subheader("➕ Add New User")
    
    with st.form("create_user_form"):
        new_username = st.text_input(
            "Username", 
            placeholder="Enter a unique username",
            help="This will be used to identify the user throughout the platform"
        )
        
        submit = st.form_submit_button("🚀 Create User", use_container_width=True)
        
        if submit:
            if new_username:
                if new_username == "PLATFORM OWNER":
                    st.error("❌ Cannot create user with reserved name 'PLATFORM OWNER'")
                else:
                    try:
                        user_id = user_model.create_user(conn, new_username)
                        st.success(f"✅ Created user: **{new_username}** (ID: {user_id})")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error(f"❌ Username '{new_username}' already exists. Please choose a different name.")
                        else:
                            st.error(f"❌ Error creating user: {str(e)}")
            else:
                st.warning("⚠️ Please enter a username")
    
    st.markdown("---")
    
    # Display all users and selection
    st.subheader("👥 All Users")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username 
        FROM users 
        WHERE username != 'PLATFORM OWNER'
        ORDER BY user_id DESC
    """)
    users = cursor.fetchall()
    
    if not users:
        st.info("📝 No users in the system yet. Create your first user above!")
        return
    
    # Show current selection
    if st.session_state.selected_user:
        st.success(f"🎯 **Currently selected:** {st.session_state.selected_user['username']} (ID: {st.session_state.selected_user['user_id']})")
    else:
        st.info("ℹ️ No user currently selected")
    
    # User list with selection buttons
    st.markdown("**Click to select a user:**")
    
    for user in users:
        user_id, username = user
        
        # Create a container for each user
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                # Check if this is the currently selected user
                if (st.session_state.selected_user and 
                    st.session_state.selected_user['user_id'] == user_id):
                    st.markdown(f"**✅ {username}** (ID: {user_id}) *← Selected*")
                else:
                    st.markdown(f"**{username}** (ID: {user_id})")
            
            with col2:
                # Get user stats
                cursor.execute("SELECT COUNT(*) FROM invoices WHERE owner_user_id = ?", (user_id,))
                owned_invoices = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE buyer_user_id = ?", (user_id,))
                investments = cursor.fetchone()[0]
                
                st.markdown(f"📋 {owned_invoices} invoices • 💰 {investments} investments")
            
            with col3:
                if st.button("Select", key=f"select_{user_id}"):
                    st.session_state.selected_user = {
                        "user_id": user_id,
                        "username": username
                    }
                    st.success(f"Selected: {username}")
                    st.rerun()
        
        st.markdown("---")
    
    # Quick actions after user selection
    if st.session_state.selected_user:
        st.subheader("🚀 Quick Actions")
        st.markdown(f"What would you like to do as **{st.session_state.selected_user['username']}**?")
        
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("📝 Create Invoice", use_container_width=True):
                navigate_to("Create Invoice")
        
        with action_col2:
            if st.button("🛒 Browse Deals", use_container_width=True):
                navigate_to("Browse Invoices")
        
        with action_col3:
            if st.button("📊 My Dashboard", use_container_width=True):
                navigate_to("Dashboard")
    
    # Platform stats
    st.markdown("---")
    st.subheader("📊 Platform Statistics")
    
    # Get platform stats
    cursor.execute("SELECT COUNT(*) FROM users WHERE username != 'PLATFORM OWNER'")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.metric("👥 Total Users", f"{total_users:,}")
    
    with stat_col2:
        st.metric("📋 Total Invoices", f"{total_invoices:,}")
    
    with stat_col3:
        st.metric("💰 Total Transactions", f"{total_transactions:,}")
    
    if total_users == 0:
        st.info("🌟 Create your first user to get started with the platform!")