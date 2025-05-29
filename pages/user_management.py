import streamlit as st
from models import user as user_model

def app(conn):
    st.title("User Management")
    
    # Form to add new user
    st.subheader("Add New User")
    new_username = st.text_input("New Username")
    if st.button("Create User"):
        if new_username:
            user_id = user_model.create_user(conn, new_username)
            st.success(f"Created user: {new_username} (ID: {user_id})")
            st.rerun()
        else:
            st.warning("Please enter a username")
    
    st.markdown("---")
    
    # Display all users and selection buttons
    st.subheader("Select Active User")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY user_id DESC")
    users = cursor.fetchall()
    
    if not users:
        st.info("No users in the system yet")
        return
    
    for user in users:
        user_id, username = user
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"{username} (ID: {user_id})")
        
        with col2:
            if st.button(f"Select", key=f"select_{user_id}"):
                st.session_state.selected_user = {
                    "user_id": user_id,
                    "username": username
                }
                st.success(f"Selected user: {username}")
                st.rerun()