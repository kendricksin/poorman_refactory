import streamlit as st
from models import invoice as invoice_model
from models import transaction as transaction_model
from utils.helpers import process_invoice_owner_payment, format_currency, get_user_summary, format_number

def navigate_to(page_name):
    """Navigate to a specific page"""
    import streamlit as st
    st.session_state.current_page = page_name
    st.rerun()

def show_platform_dashboard(conn):
    """Display platform owner earnings and statistics"""
    st.subheader("🏦 Platform Owner Dashboard")
    
    cursor = conn.cursor()
    
    # Platform earnings summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_fees,
            COALESCE(SUM(amount), 0) as total_earnings
        FROM cash_transfers 
        WHERE to_party LIKE '%PLATFORM OWNER%'
    """)
    fee_stats = cursor.fetchone()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 Total Platform Earnings", format_currency(fee_stats[1]))
    with col2:
        st.metric("📊 Number of Fee Collections", fee_stats[0])
    
    # Detailed earnings breakdown
    st.subheader("💸 Earnings Breakdown")
    
    cursor.execute("""
        SELECT 
            ct.invoice_id,
            ct.amount,
            ct.event_timestamp,
            ct.event_description,
            i.debtor_name,
            i.original_amount
        FROM cash_transfers ct
        JOIN invoices i ON ct.invoice_id = i.invoice_id
        WHERE ct.to_party LIKE '%PLATFORM OWNER%'
        ORDER BY ct.event_timestamp DESC
    """)
    
    earnings = cursor.fetchall()
    
    if earnings:
        total_shown = 0
        for earning in earnings:
            invoice_id, amount, timestamp, description, debtor, original = earning
            total_shown += amount
            
            st.markdown(f"""
            <div style='padding: 10px; border-left: 3px solid green; margin: 5px 0; background-color: #f9f9f9;'>
                <strong>💰 {format_currency(amount)}</strong> from Invoice #{invoice_id}<br>
                <em>{debtor}</em> (Original: {format_currency(original)})<br>
                <small>{timestamp} - {description}</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.info(f"Total shown: {format_currency(total_shown)}")
    else:
        st.info("No platform earnings yet. Earnings will appear when deals are completed!")
    
    # Close button
    if st.button("Close Platform Dashboard"):
        st.session_state.show_platform_dashboard = False
        st.rerun()

def app(conn):
    # Breadcrumb navigation
    st.markdown("🏠 [Home](#) > 📊 **Dashboard**")
    if st.button("← Back to Home", key="back_to_home"):
        navigate_to("Home")
    st.markdown("---")
    
    st.title("📊 Your Dashboard")
    
    if not st.session_state.selected_user:
        st.warning("Please select a user in the User Management tab first")
        
        # Show Platform Owner Dashboard option
        st.markdown("---")
        st.subheader("🏦 Platform Owner Dashboard")
        if st.button("View Platform Earnings"):
            st.session_state.show_platform_dashboard = True
            st.rerun()
        
        # Show platform dashboard if requested
        if hasattr(st.session_state, 'show_platform_dashboard') and st.session_state.show_platform_dashboard:
            show_platform_dashboard(conn)
        
        return
    
    user_id = st.session_state.selected_user["user_id"]
    username = st.session_state.selected_user["username"]
    
    st.subheader(f"Welcome back, {username}! 👋")
    
    # Admin section to fix existing data
    with st.expander("🔧 System Maintenance (Click if invoices seem stuck)"):
        st.write("If you have invoices that are fully funded but still show as 'Pending', click below to fix them:")
        
        if st.button("🔄 Fix Pending Invoices", help="This will check all pending invoices and activate those that are fully funded"):
            cursor = conn.cursor()
            
            # Get all pending invoices that are actually fully funded
            cursor.execute("""
                SELECT invoice_id, chunks_sold, chunks_total, desired_sale_price, owner_user_id, debtor_name
                FROM invoices 
                WHERE status = 'Pending' AND chunks_sold >= chunks_total
            """)
            
            invoices_to_fix = cursor.fetchall()
            
            if invoices_to_fix:
                for invoice_data in invoices_to_fix:
                    invoice_id, chunks_sold, chunks_total, sale_price, owner_id, debtor = invoice_data
                    
                    # Update invoice status to Active
                    cursor.execute("UPDATE invoices SET status = 'Active' WHERE invoice_id = ?", (invoice_id,))
                    
                    # Update all related transactions to Active status
                    cursor.execute("""
                        UPDATE transactions 
                        SET status = 'Active'
                        WHERE invoice_id = ? AND status = 'Pending Activation'
                    """, (invoice_id,))
                    
                    # Create cash transfer record
                    funding_amount = chunks_total * 100
                    cursor.execute("""
                        INSERT INTO cash_transfers (
                            invoice_id, event_description, amount, from_party, to_party
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        invoice_id, 
                        "Invoice Fully Funded - Cash Released to Owner (Auto-Fixed)", 
                        funding_amount, 
                        "Collective Buyers", 
                        f"Invoice Owner (User {owner_id})"
                    ))
                
                conn.commit()
                st.success(f"✅ Fixed {len(invoices_to_fix)} invoices! They are now Active.")
                st.rerun()
            else:
                st.info("No invoices need fixing. All fully-funded invoices are already Active.")
    
    
    # Get user summary
    summary = get_user_summary(conn, user_id)
    
    # Portfolio Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Invoices Created", format_number(summary['owned_invoices']))
    with col2:
        st.metric("💰 Total Invoice Value", format_currency(summary['owned_value']))
    with col3:
        st.metric("🎯 Investment Deals", format_number(summary['investments']))
    with col4:
        st.metric("💸 Total Invested", format_currency(summary['investment_value']))
    
    st.markdown("---")
    
    # Two-column layout
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("📄 Your Invoices")
        owned_invoices = invoice_model.get_invoices_by_owner(conn, user_id)
        
        if owned_invoices:
            for invoice in owned_invoices:
                invoice_id, _, debtor, amount, terms, sale_price, total_chunks, sold_chunks, status = invoice
                
                # Create expandable card for each invoice
                with st.expander(f"#{invoice_id} - {debtor} | {status}", expanded=(status == 'Active')):
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        st.write(f"**Original Amount:** {format_currency(amount)}")
                        st.write(f"**Sale Price:** {format_currency(sale_price)}")
                        st.write(f"**Payment Terms:** {terms}")
                        
                        # Progress bar
                        progress = (sold_chunks / total_chunks) if total_chunks > 0 else 0
                        st.progress(progress, text=f"{sold_chunks}/{total_chunks} chunks sold ({progress*100:.0f}%)")
                        
                        # Status indicator
                        status_colors = {
                            'Pending': '🟡',
                            'Active': '🟢', 
                            'Paid': '✅'
                        }
                        st.write(f"**Status:** {status_colors.get(status, '❓')} {status}")
                        
                        if status == 'Active':
                            st.info("💡 Invoice is fully funded! Waiting for debtor payment.")
                        elif status == 'Pending':
                            remaining = total_chunks - sold_chunks
                            st.info(f"⏳ Need {remaining} more chunks (฿{remaining * 100}) to activate")
                    
                    with col_b:
                        if status == 'Active':
                            st.write("**Mark as Paid**")
                            st.write("Click when debtor pays:")
                            if st.button("💰 Debtor Paid", key=f"pay_{invoice_id}"):
                                try:
                                    process_invoice_owner_payment(conn, invoice_id, user_id)
                                    st.success("✅ Payment processed! Buyers have been paid out.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        elif status == 'Paid':
                            st.success("✅ Completed")
                        else:
                            st.write("**Potential Profit:**")
                            profit = amount - sale_price
                            st.write(format_currency(profit))
        else:
            st.info("🎯 You haven't created any invoices yet.")
            if st.button("📝 Create Your First Invoice", use_container_width=True):
                navigate_to("Create Invoice")
    
    with col_right:
        st.subheader("💼 Your Investments")
        
        # Get user's investments
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.invoice_id,
                t.chunks_purchased,
                t.status as transaction_status,
                t.purchase_timestamp,
                i.debtor_name,
                i.original_amount,
                i.desired_sale_price,
                i.chunks_total,
                i.status as invoice_status
            FROM transactions t
            JOIN invoices i ON t.invoice_id = i.invoice_id
            WHERE t.buyer_user_id = ?
            ORDER BY t.purchase_timestamp DESC
        """, (user_id,))
        
        investments = cursor.fetchall()
        
        if investments:
            total_investment = 0
            potential_returns = 0
            
            for investment in investments:
                (inv_id, chunks, trans_status, timestamp, debtor, orig_amount, 
                 sale_price, total_chunks, inv_status) = investment
                
                investment_amount = chunks * 100
                total_investment += investment_amount
                
                # Calculate potential return AFTER 10% platform fee
                base_return_per_chunk = orig_amount / total_chunks
                total_profit = orig_amount - (total_chunks * 100)  # Total profit in the deal
                platform_fee_total = total_profit * 0.10  # 10% of total profit
                platform_fee_per_chunk = platform_fee_total / total_chunks
                net_return_per_chunk = base_return_per_chunk - platform_fee_per_chunk
                
                potential_return = chunks * net_return_per_chunk
                potential_returns += potential_return
                profit = potential_return - investment_amount
                
                with st.expander(f"#{inv_id} - {debtor} | {inv_status}", expanded=(inv_status == 'Active')):
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        st.write(f"**Investment:** {chunks} chunks = {format_currency(investment_amount)}")
                        st.write(f"**Expected Return:** {format_currency(potential_return)}")
                        st.write(f"**Expected Profit:** {format_currency(profit)}")
                        
                        roi = (profit / investment_amount * 100) if investment_amount > 0 else 0
                        st.write(f"**ROI:** {roi:.1f}%")
                        
                        st.write(f"**Purchase Date:** {timestamp}")
                    
                    with col_b:
                        status_info = {
                            'Pending Activation': ('⏳', 'Waiting for full funding'),
                            'Active': ('🟢', 'Invoice is active!'),
                            'Paid Out': ('✅', 'You\'ve been paid!'),
                            'Paid': ('✅', 'Completed')
                        }
                        
                        emoji, description = status_info.get(trans_status, ('❓', 'Unknown status'))
                        st.write(f"**Status:** {emoji}")
                        st.write(description)
            
            # Investment Summary
            st.markdown("---")
            st.subheader("💰 Investment Summary")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Total Invested", format_currency(total_investment))
            with col_b:
                st.metric("Potential Returns", format_currency(potential_returns))
            
            total_profit = potential_returns - total_investment
            overall_roi = (total_profit / total_investment * 100) if total_investment > 0 else 0
            
            st.write(f"**Expected Total Profit:** {format_currency(total_profit)}")
            st.write(f"**Overall ROI:** {overall_roi:.1f}%")
            
        else:
            st.info("🎯 You haven't made any investments yet.")
            if st.button("🛒 Browse Investment Opportunities", use_container_width=True):
                navigate_to("Browse Invoices")
    
    # Recent Activity Section
    st.markdown("---")
    st.subheader("📈 Recent Activity")
    
    # Get recent cash transfers involving this user
    cursor.execute("""
        SELECT 
            ct.event_description,
            ct.event_timestamp,
            ct.amount,
            ct.from_party,
            ct.to_party,
            i.debtor_name,
            ct.invoice_id
        FROM cash_transfers ct
        JOIN invoices i ON ct.invoice_id = i.invoice_id
        WHERE ct.from_party LIKE ? OR ct.to_party LIKE ?
        ORDER BY ct.event_timestamp DESC
        LIMIT 10
    """, (f"%User {user_id}%", f"%User {user_id}%"))
    
    recent_transfers = cursor.fetchall()
    
    if recent_transfers:
        for transfer in recent_transfers:
            event, timestamp, amount, from_party, to_party, debtor, inv_id = transfer
            
            # Determine if money was received or sent
            if f"User {user_id}" in to_party:
                direction = "received"
                color = "green"
                emoji = "💰"
            else:
                direction = "sent"
                color = "red"
                emoji = "💸"
            
            st.markdown(f"""
            <div style='padding: 10px; border-left: 3px solid {color}; margin: 5px 0; background-color: #f9f9f9;'>
                <strong>{emoji} {event}</strong><br>
                Invoice #{inv_id} - {debtor}<br>
                {direction.title()} {format_currency(amount)} on {timestamp}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent activity. Your financial transactions will appear here.")
    
    # Navigation footer
    st.markdown("---")
    st.markdown("### 🧭 Quick Links")
    
    nav_footer_col1, nav_footer_col2, nav_footer_col3 = st.columns(3)
    
    with nav_footer_col1:
        if st.button("💰 View All Cash Transfers", use_container_width=True):
            navigate_to("Cash Transfers")
    
    with nav_footer_col2:
        if st.button("🛒 Browse Opportunities", use_container_width=True):
            navigate_to("Browse Invoices")
    
    with nav_footer_col3:
        if st.button("📝 Create New Invoice", use_container_width=True):
            navigate_to("Create Invoice")