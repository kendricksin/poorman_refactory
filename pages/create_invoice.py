import streamlit as st
from models import invoice as invoice_model
from utils.helpers import check_invoice_activation

def navigate_to(page_name):
    """Navigate to a specific page"""
    st.session_state.current_page = page_name
    st.rerun()

def app(conn):
    # Breadcrumb navigation
    st.markdown("🏠 [Home](#) > 📝 **Create Invoice**")
    if st.button("← Back to Home", key="back_to_home"):
        navigate_to("Home")
    st.markdown("---")
    
    st.title("📝 Create New Invoice")
    st.markdown("**Turn your outstanding invoice into immediate cash flow**")
    
    if not st.session_state.selected_user:
        st.warning("Please select a user from the sidebar first")
        
        # Quick navigation to user management
        if st.button("👤 Go to User Management"):
            navigate_to("User Management")
        return
        
    # Show current user
    st.success(f"Creating invoice as: **{st.session_state.selected_user['username']}**")
    
    # Initialize session state for form success
    if 'invoice_created' not in st.session_state:
        st.session_state.invoice_created = False
    if 'created_invoice_id' not in st.session_state:
        st.session_state.created_invoice_id = None
    if 'created_invoice_details' not in st.session_state:
        st.session_state.created_invoice_details = None
    
    with st.form("invoice_form"):
        st.markdown("### 📋 Invoice Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            debtor = st.text_input(
                "Debtor/Client Name*", 
                placeholder="e.g., ABC Company Ltd.",
                help="The company or person who owes you money"
            )
            original_amount = st.number_input(
                "Original Invoice Amount (THB)*", 
                min_value=100.0,
                step=100.0,
                help="The full amount your client owes you"
            )
        
        with col2:
            terms = st.text_input(
                "Payment Terms*", 
                placeholder="e.g., Net 30, Due March 15th",
                help="When is the debtor supposed to pay?"
            )
            sale_price = st.number_input(
                "Desired Sale Price (THB)*", 
                min_value=100.0,
                step=100.0,
                help="How much immediate cash do you want? (Should be less than original amount)"
            )
        
        # Show calculations
        if original_amount > 0 and sale_price > 0:
            st.markdown("### 💰 Deal Preview")
            
            if sale_price >= original_amount:
                st.error("⚠️ Sale price must be less than original amount to offer investors a profit!")
            else:
                chunks_total = int(sale_price // 100)
                discount = original_amount - sale_price
                investor_profit = discount
                discount_percentage = (discount / original_amount) * 100
                
                preview_col1, preview_col2, preview_col3 = st.columns(3)
                
                with preview_col1:
                    st.metric("💸 You Get (Immediate)", f"฿{sale_price:,.2f}")
                
                with preview_col2:
                    st.metric("🎯 Total Chunks", f"{chunks_total} × ฿100")
                
                with preview_col3:
                    st.metric("💰 Investor Profit Pool", f"฿{investor_profit:,.2f}")
                
                st.info(f"📊 You're offering a {discount_percentage:.1f}% discount ({discount:,.0f} THB profit) to get immediate cash")
                
                # Platform fee note
                platform_fee = investor_profit * 0.10
                st.warning(f"🏦 Platform will earn ฿{platform_fee:,.2f} (10% of investor profits) when deal completes")
        
        submit = st.form_submit_button("🚀 Create Invoice", use_container_width=True)
        
        if submit:
            # Validation
            if not debtor or not terms:
                st.error("Please fill in all required fields (marked with *)")
            elif sale_price >= original_amount:
                st.error("Sale price must be less than original amount to attract investors!")
            elif sale_price < 100:
                st.error("Sale price must be at least ฿100 to create chunks")
            else:
                # Create the invoice
                owner_id = st.session_state.selected_user["user_id"]
                invoice_id = invoice_model.create_invoice(
                    conn, owner_id, debtor, original_amount, terms, sale_price
                )
                
                # Store success details in session state
                st.session_state.invoice_created = True
                st.session_state.created_invoice_id = invoice_id
                st.session_state.created_invoice_details = {
                    'debtor': debtor,
                    'original_amount': original_amount,
                    'sale_price': sale_price,
                    'chunks_total': int(sale_price // 100)
                }
                
                # Check if activation needed (shouldn't happen immediately, but good to check)
                check_invoice_activation(conn, invoice_id)
                
                st.rerun()  # Rerun to show success message outside form
    
    # Show success message and navigation OUTSIDE the form
    if st.session_state.invoice_created and st.session_state.created_invoice_id:
        invoice_id = st.session_state.created_invoice_id
        details = st.session_state.created_invoice_details
        
        st.success(f"🎉 Invoice created successfully! ID: #{invoice_id}")
        st.balloons()
        
        # Show next steps
        st.markdown("### 🎯 What's Next?")
        st.info(f"""
        Your invoice has been created and is now available for investors to purchase.
        
        **Invoice #{invoice_id}** needs **{details['chunks_total']} investors** to buy ฿100 chunks each.
        Once all chunks are sold, your invoice will activate and you'll receive ฿{details['sale_price']:,.2f} immediately!
        """)
        
        # Navigation options OUTSIDE the form
        st.markdown("### 🧭 Where to go next?")
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
        
        with nav_col1:
            if st.button("🛒 Browse All Invoices", use_container_width=True, key="nav_browse"):
                st.session_state.invoice_created = False  # Reset success state
                navigate_to("Browse Invoices")
        
        with nav_col2:
            if st.button("📊 My Dashboard", use_container_width=True, key="nav_dashboard"):
                st.session_state.invoice_created = False  # Reset success state
                navigate_to("Dashboard")
        
        with nav_col3:
            if st.button("📝 Create Another", use_container_width=True, key="nav_create_another"):
                # Reset form state
                st.session_state.invoice_created = False
                st.session_state.created_invoice_id = None
                st.session_state.created_invoice_details = None
                st.rerun()
        
        with nav_col4:
            if st.button("🏠 Go Home", use_container_width=True, key="nav_home"):
                st.session_state.invoice_created = False  # Reset success state
                navigate_to("Home")
    
    # Help section
    st.markdown("---")
    with st.expander("❓ Need Help? Invoice Creation Guide"):
        st.markdown("""
        ### 📚 How to Create a Good Invoice Listing
        
        **1. Choose the Right Debtor**
        - List established companies that are likely to pay
        - Avoid unknown or risky clients
        
        **2. Set Realistic Sale Price**
        - Offer 5-15% discount for quick funding
        - Too small discount = no investor interest
        - Too large discount = you lose too much
        
        **3. Clear Payment Terms**
        - Be specific: "Net 30" or "Due March 15th"
        - Shorter terms = more attractive to investors
        
        **4. Example Good Invoice**
        - Debtor: "XYZ Corporation Ltd."
        - Original: ฿50,000
        - Sale Price: ฿45,000 (10% discount)
        - Terms: "Net 30 days"
        - Result: 450 chunks × ฿100, ฿5,000 investor profit
        """)
    
    # Quick stats for motivation
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE status IN ('Active', 'Paid')")
    successful_deals = cursor.fetchone()[0]
    
    if successful_deals > 0:
        st.success(f"💪 {successful_deals} deals have been successfully funded on this platform!")