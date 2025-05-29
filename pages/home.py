import streamlit as st
from utils.helpers import format_currency, format_number

def navigate_to(page_name):
    """Navigate to a specific page"""
    import streamlit as st
    st.session_state.current_page = page_name
    st.rerun()

def create_quick_actions():
    """Create quick action buttons for common tasks"""
    import streamlit as st
    
    if not st.session_state.selected_user:
        st.info("👆 Select a user from sidebar to see quick actions")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Create Invoice", use_container_width=True):
            navigate_to("Create Invoice")
    
    with col2:
        if st.button("🛒 Browse Deals", use_container_width=True):
            navigate_to("Browse Invoices")
    
    with col3:
        if st.button("📊 My Dashboard", use_container_width=True):
            navigate_to("Dashboard")

def app(conn):
    # Add breadcrumb (just for Home page, it's simple)
    st.markdown("🏠 **Home**")
    st.markdown("---")
    
    st.title("🏦 Invoice Refactoring MVP")
    st.markdown("**Turn your outstanding invoices into immediate cash flow**")
    
    # Get real-time platform statistics
    cursor = conn.cursor()
    
    # Platform Overview Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Total Invoices
    cursor.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = cursor.fetchone()[0]
    
    # Active Deals (fully funded)
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE status = 'Active'")
    active_deals = cursor.fetchone()[0]
    
    # Total Value Processed
    cursor.execute("SELECT COALESCE(SUM(original_amount), 0) FROM invoices")
    total_value = cursor.fetchone()[0]
    
    # Available Investment Opportunities
    cursor.execute("""
        SELECT COALESCE(SUM((chunks_total - chunks_sold) * 100), 0) 
        FROM invoices 
        WHERE status = 'Pending'
    """)
    available_investment = cursor.fetchone()[0]
    
    # Platform earnings
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM cash_transfers 
        WHERE to_party LIKE '%PLATFORM OWNER%'
    """)
    platform_earnings = cursor.fetchone()[0]
    
    with col1:
        st.metric("📋 Total Invoices", format_number(total_invoices))
    with col2:
        st.metric("✅ Active Deals", format_number(active_deals))
    with col3:
        st.metric("💰 Total Value", format_currency(total_value))
    with col4:
        st.metric("🎯 Available Investment", format_currency(available_investment))
    with col5:
        st.metric("🏦 Platform Earnings", format_currency(platform_earnings))
    
    st.markdown("---")
    
    # Two column layout for content
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("🚀 How It Works")
        st.markdown("""
        #### For Invoice Owners (Get Cash Now)
        1. **Submit Invoice** - Upload your outstanding invoice details
        2. **Set Sale Price** - Choose how much immediate cash you need
        3. **Auto-Chunking** - We split it into ฿100 investment chunks
        4. **Get Funded** - Receive cash when all chunks are bought
        
        #### For Investors (Earn Returns)
        1. **Browse Opportunities** - View available invoice chunks
        2. **Invest ฿100+** - Buy one or more chunks per invoice
        3. **Earn Profit** - Get paid more when the debtor pays the original invoice
        4. **Track Returns** - Monitor your investments and payouts
        
        *Note: Platform takes 10% of profits to maintain the service*
        
        #### Key Benefits
        - ✅ **No Credit Checks** - Based on invoice quality, not personal credit
        - ✅ **Quick Funding** - Get cash as soon as all chunks are sold
        - ✅ **Transparent** - Full transaction history for every deal
        - ✅ **All-or-Nothing** - Deals only activate when fully funded
        """)
    
    with col_right:
        st.subheader("📈 Recent Activity")
        
        # Recent Invoices
        cursor.execute("""
            SELECT debtor_name, original_amount, status, chunks_sold, chunks_total
            FROM invoices 
            ORDER BY invoice_id DESC 
            LIMIT 5
        """)
        recent_invoices = cursor.fetchall()
        
        if recent_invoices:
            for invoice in recent_invoices:
                debtor, amount, status, sold, total = invoice
                progress = (sold / total * 100) if total > 0 else 0
                
                status_emoji = {
                    'Pending': '⏳',
                    'Active': '✅', 
                    'Paid': '💰'
                }.get(status, '❓')
                
                st.markdown(f"""
                **{status_emoji} {debtor}**  
                {format_currency(amount)} | {progress:.0f}% funded
                """)
        else:
            st.info("No invoices yet - be the first!")
        
        st.markdown("---")
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        create_quick_actions()
    
    # Platform Statistics Section
    st.markdown("---")
    st.subheader("📊 Platform Statistics")
    
    tab1, tab2 = st.tabs(["💼 Invoice Status", "💰 Financial Overview"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Invoice status breakdown
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM invoices 
                GROUP BY status
            """)
            status_data = cursor.fetchall()
            
            if status_data:
                st.write("**Invoice Status Breakdown:**")
                for status, count in status_data:
                    st.write(f"- {status}: {count}")
            else:
                st.info("No invoices created yet")
        
        with col2:
            # Funding progress
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN chunks_sold >= chunks_total THEN 1 ELSE 0 END) as fully_funded
                FROM invoices 
                WHERE status != 'Paid'
            """)
            funding_stats = cursor.fetchone()
            
            if funding_stats and funding_stats[0] > 0:
                total, funded = funding_stats
                funding_rate = (funded / total * 100) if total > 0 else 0
                st.write("**Funding Success Rate:**")
                st.write(f"- {funded}/{total} invoices fully funded")
                st.write(f"- {funding_rate:.1f}% success rate")
            else:
                st.info("No funding data yet")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Money flow
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(amount), 0) as total_transferred
                FROM cash_transfers
            """)
            total_transferred = cursor.fetchone()[0]
            
            st.metric("💸 Total Money Flow", format_currency(total_transferred))
        
        with col2:
            # Average deal size
            cursor.execute("""
                SELECT 
                    COALESCE(AVG(original_amount), 0) as avg_invoice,
                    COALESCE(AVG(desired_sale_price), 0) as avg_sale_price
                FROM invoices
            """)
            avg_data = cursor.fetchone()
            
            if avg_data:
                avg_invoice, avg_sale = avg_data
                st.metric("📊 Avg Invoice Size", format_currency(avg_invoice))
                if avg_invoice > 0:
                    discount_rate = ((avg_invoice - avg_sale) / avg_invoice * 100)
                    st.write(f"*Avg discount: {discount_rate:.1f}%*")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <small>Invoice Refactoring MVP - Connecting invoice owners with investors for mutual benefit</small>
    </div>
    """, unsafe_allow_html=True)