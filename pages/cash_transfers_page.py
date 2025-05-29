import streamlit as st

def navigate_to(page_name):
    """Navigate to a specific page"""
    st.session_state.current_page = page_name
    st.rerun()

def app(conn):
    # Breadcrumb navigation
    st.markdown("🏠 [Home](#) > 💰 **Cash Transfers**")
    if st.button("← Back to Home", key="back_to_home"):
        navigate_to("Home")
    st.markdown("---")
    
    st.title("💰 All Cash Transfer History")
    st.markdown("**Complete financial transaction history across all invoices and users**")
    
    cursor = conn.cursor()
    
    # Summary statistics
    st.subheader("📊 Transfer Summary")
    
    # Get summary stats
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM cash_transfers")
    total_transfers, total_amount = cursor.fetchone()
    
    cursor.execute("""
        SELECT COUNT(DISTINCT invoice_id) 
        FROM cash_transfers
    """)
    invoices_with_transfers = cursor.fetchone()[0]
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("💸 Total Transfers", f"{total_transfers:,}")
    
    with summary_col2:
        st.metric("💰 Total Amount", f"฿{total_amount:,.2f}")
    
    with summary_col3:
        st.metric("📋 Invoices Involved", f"{invoices_with_transfers:,}")
    
    st.markdown("---")
    
    # Filter options
    st.subheader("🔍 Filter Transfers")
    
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # Invoice filter
        cursor.execute("""
            SELECT DISTINCT i.invoice_id, i.debtor_name
            FROM invoices i
            JOIN cash_transfers ct ON i.invoice_id = ct.invoice_id
            ORDER BY i.invoice_id DESC
        """)
        invoice_options = cursor.fetchall()
        
        selected_invoice = st.selectbox(
            "Filter by Invoice:",
            options=["All Invoices"] + [f"#{inv_id} - {debtor}" for inv_id, debtor in invoice_options]
        )
    
    with filter_col2:
        # Event type filter
        cursor.execute("SELECT DISTINCT event_description FROM cash_transfers ORDER BY event_description")
        event_types = [row[0] for row in cursor.fetchall()]
        
        selected_event = st.selectbox(
            "Filter by Event Type:",
            options=["All Events"] + event_types
        )
    
    # Get filtered data
    if selected_invoice == "All Invoices":
        invoice_filter = None
    else:
        invoice_filter = int(selected_invoice.split('#')[1].split(' -')[0])
    
    # Build query based on filters
    query = """
        SELECT DISTINCT i.invoice_id, i.debtor_name, i.original_amount
        FROM invoices i
        JOIN cash_transfers ct ON i.invoice_id = ct.invoice_id
    """
    params = []
    
    if invoice_filter:
        query += " WHERE i.invoice_id = ?"
        params.append(invoice_filter)
    
    query += " ORDER BY i.invoice_id DESC"
    
    cursor.execute(query, params)
    invoices = cursor.fetchall()
    
    if not invoices:
        st.info("No cash transfers recorded yet.")
        
        # Quick navigation for new users
        st.markdown("### 🚀 Get Started")
        quick_col1, quick_col2 = st.columns(2)
        
        with quick_col1:
            if st.button("📝 Create Your First Invoice", use_container_width=True):
                navigate_to("Create Invoice")
        
        with quick_col2:
            if st.button("🛒 Browse Investment Opportunities", use_container_width=True):
                navigate_to("Browse Invoices")
        
        return
    
    # Results summary
    st.subheader(f"📋 Transfer History ({len(invoices)} invoices)")
    
    # Display transfers by invoice
    for invoice in invoices:
        invoice_id, debtor_name, original_amount = invoice
        
        # Get transfers for this invoice
        transfer_query = """
            SELECT event_description, event_timestamp, amount, from_party, to_party
            FROM cash_transfers
            WHERE invoice_id = ?
        """
        transfer_params = [invoice_id]
        
        if selected_event != "All Events":
            transfer_query += " AND event_description = ?"
            transfer_params.append(selected_event)
        
        transfer_query += " ORDER BY event_timestamp ASC"
        
        cursor.execute(transfer_query, transfer_params)
        transfers = cursor.fetchall()
        
        if not transfers:
            continue
        
        # Calculate total for this invoice
        total_in = sum(amount for _, _, amount, from_party, to_party in transfers if "User" not in from_party or from_party == "Debtor")
        total_out = sum(amount for _, _, amount, from_party, to_party in transfers if "User" in to_party)
        
        with st.expander(
            f"#{invoice_id} - {debtor_name} | ฿{original_amount:,.2f} | {len(transfers)} transfers", 
            expanded=(len(invoices) <= 3)  # Auto-expand if few invoices
        ):
            # Transfer timeline
            for i, transfer in enumerate(transfers):
                event_desc, timestamp, amount, from_party, to_party = transfer
                
                # Determine transfer direction and color
                if "PLATFORM OWNER" in to_party:
                    color = "#ff9500"  # Orange for platform fees
                    icon = "🏦"
                elif "Buyer" in to_party:
                    color = "#28a745"  # Green for payouts
                    icon = "💰"
                elif "Invoice Owner" in to_party and "Funded" in event_desc:
                    color = "#007bff"  # Blue for funding
                    icon = "💸"
                else:
                    color = "#6c757d"  # Gray for other
                    icon = "📄"
                
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 12px; margin: 8px 0; background-color: #f8f9fa; border-radius: 0 8px 8px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{icon} {event_desc}</strong><br>
                            <small style="color: #6c757d;">{timestamp}</small>
                        </div>
                        <div style="text-align: right;">
                            <strong style="font-size: 1.1em;">฿{amount:,.2f}</strong><br>
                            <small>{from_party} → {to_party}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Invoice summary
            st.markdown("---")
            summary_detail_col1, summary_detail_col2 = st.columns(2)
            
            with summary_detail_col1:
                st.markdown(f"**Total Money In:** ฿{total_in:,.2f}")
            
            with summary_detail_col2:
                st.markdown(f"**Total Money Out:** ฿{total_out:,.2f}")
    
    # Footer with navigation
    st.markdown("---")
    st.subheader("🧭 Quick Navigation")
    
    footer_col1, footer_col2, footer_col3, footer_col4 = st.columns(4)
    
    with footer_col1:
        if st.button("🏠 Home", use_container_width=True):
            navigate_to("Home")
    
    with footer_col2:
        if st.button("📊 Dashboard", use_container_width=True):
            navigate_to("Dashboard")
    
    with footer_col3:
        if st.button("🛒 Browse Deals", use_container_width=True):
            navigate_to("Browse Invoices")
    
    with footer_col4:
        if st.button("📝 Create Invoice", use_container_width=True):
            navigate_to("Create Invoice")