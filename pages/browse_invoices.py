import streamlit as st
from models import invoice as invoice_model
from models import transaction as transaction_model
from utils.helpers import check_invoice_activation, format_currency, format_number
from datetime import datetime, timedelta

def navigate_to(page_name):
    """Navigate to a specific page"""
    import streamlit as st
    st.session_state.current_page = page_name
    st.rerun()

def calculate_investment_metrics(original_amount, chunks_total, chunks_to_buy):
    """Calculate detailed investment metrics for a chunk purchase"""
    
    # Basic calculations
    investment_amount = chunks_to_buy * 100
    gross_return_per_chunk = original_amount / chunks_total
    gross_total_return = chunks_to_buy * gross_return_per_chunk
    gross_profit = gross_total_return - investment_amount
    
    # Platform fee calculations (10% of profit)
    platform_fee_total = gross_profit * 0.10
    net_profit = gross_profit - platform_fee_total
    net_total_return = investment_amount + net_profit
    
    # ROI calculations
    gross_roi = (gross_profit / investment_amount * 100) if investment_amount > 0 else 0
    net_roi = (net_profit / investment_amount * 100) if investment_amount > 0 else 0
    
    return {
        'investment_amount': investment_amount,
        'gross_return': gross_total_return,
        'gross_profit': gross_profit,
        'platform_fee': platform_fee_total,
        'net_profit': net_profit,
        'net_return': net_total_return,
        'gross_roi': gross_roi,
        'net_roi': net_roi,
        'return_per_chunk': gross_return_per_chunk,
        'net_return_per_chunk': gross_return_per_chunk - (platform_fee_total / chunks_to_buy) if chunks_to_buy > 0 else 0
    }

def render_investment_opportunity(invoice_data, conn):
    """Render a detailed investment opportunity card"""
    invoice_id, owner_id, debtor, amount, terms, sale_price, chunks_total, chunks_sold, status = invoice_data
    
    remaining_chunks = chunks_total - chunks_sold
    funding_progress = (chunks_sold / chunks_total * 100) if chunks_total > 0 else 0
    
    # Main container with styling
    with st.container():
        st.markdown(f"""
        <div style="border: 2px solid #e1e5e9; border-radius: 10px; padding: 20px; margin: 15px 0; background-color: #fafafa;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="color: #2c3e50; margin: 0;">🏢 {debtor}</h3>
                <span style="background-color: {'#28a745' if status == 'Active' else '#ffc107'}; color: white; padding: 5px 15px; border-radius: 15px; font-weight: bold;">
                    {status}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Two column layout for main info
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # Invoice Details Section
            st.markdown("### 📋 Invoice Details")
            
            detail_col1, detail_col2 = st.columns(2)
            with detail_col1:
                st.markdown(f"""
                **Original Invoice Amount:** {format_currency(amount)}  
                **Payment Terms:** {terms}  
                **Invoice ID:** #{invoice_id}
                """)
            
            with detail_col2:
                st.markdown(f"""
                **Seeking to Raise:** {format_currency(sale_price)}  
                **Total Chunks:** {format_number(chunks_total)} × ฿100  
                **Discount Offered:** {format_currency(amount - sale_price)}
                """)
            
            # Funding Progress
            st.markdown("### 📊 Funding Progress")
            progress_col1, progress_col2 = st.columns([3, 1])
            
            with progress_col1:
                st.progress(funding_progress / 100, text=f"{funding_progress:.1f}% funded")
            with progress_col2:
                st.metric("Remaining", f"{format_number(remaining_chunks)} chunks")
            
            st.markdown(f"**{format_number(chunks_sold)}/{format_number(chunks_total)}** chunks sold • **{format_number(remaining_chunks)} chunks available**")
        
        with col_right:
            # Investment Calculator
            st.markdown("### 💰 Investment Calculator")
            
            if status == 'Pending' and remaining_chunks > 0:
                # Chunk selector
                chunks_to_buy = st.number_input(
                    "Chunks to Purchase:",
                    min_value=1,
                    max_value=remaining_chunks,
                    value=min(5, remaining_chunks),
                    key=f"calc_{invoice_id}",
                    help="Each chunk costs ฿100"
                )
                
                # Calculate metrics
                metrics = calculate_investment_metrics(amount, chunks_total, chunks_to_buy)
                
                # Investment summary box
                st.markdown(f"""
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745;">
                    <h4 style="margin-top: 0; color: #155724;">💸 Your Investment</h4>
                    <p><strong>You Pay:</strong> {format_currency(metrics['investment_amount'])}</p>
                    <p><strong>You Get Back:</strong> {format_currency(metrics['net_return'])}</p>
                    <p><strong>Your Profit:</strong> {format_currency(metrics['net_profit'])} ({metrics['net_roi']:.1f}% ROI)</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Buy button
                if st.button(f"🛒 Buy {chunks_to_buy} Chunks", key=f"buy_{invoice_id}", use_container_width=True):
                    if st.session_state.selected_user:
                        transaction_model.purchase_chunks(
                            conn, invoice_id, st.session_state.selected_user['user_id'], chunks_to_buy
                        )
                        
                        # Check activation
                        activated = check_invoice_activation(conn, invoice_id)
                        
                        if activated:
                            st.success(f"🎉 Purchased {chunks_to_buy} chunks! Invoice is now FULLY FUNDED and ACTIVE!")
                        else:
                            st.success(f"✅ Purchased {chunks_to_buy} chunks!")
                        
                        st.rerun()
                    else:
                        st.error("Please select a user first!")
            
            elif status == 'Active':
                st.success("✅ **FULLY FUNDED**")
                st.info("This invoice is active and waiting for debtor payment.")
            
            else:
                st.info("No chunks available")
        
        # Detailed Financial Breakdown (Expandable)
        with st.expander("📈 Detailed Financial Breakdown", expanded=False):
            fin_col1, fin_col2 = st.columns(2)
            
            with fin_col1:
                st.markdown("#### 💹 Per Chunk Analysis")
                return_per_chunk = amount / chunks_total
                profit_per_chunk_gross = return_per_chunk - 100
                platform_fee_per_chunk = (profit_per_chunk_gross * 0.10)
                net_profit_per_chunk = profit_per_chunk_gross - platform_fee_per_chunk
                
                st.markdown(f"""
                **Cost per chunk:** ฿100.00  
                **Gross return per chunk:** {format_currency(return_per_chunk)}  
                **Gross profit per chunk:** {format_currency(profit_per_chunk_gross)}  
                **Platform fee per chunk:** -{format_currency(platform_fee_per_chunk)}  
                **Net profit per chunk:** {format_currency(net_profit_per_chunk)}
                """)
            
            with fin_col2:
                st.markdown("#### ⚖️ Risk & Timeline")
                
                # Calculate estimated timeline (assuming payment terms)
                if 'net' in terms.lower():
                    try:
                        days = int(''.join(filter(str.isdigit, terms)))
                        expected_date = datetime.now() + timedelta(days=days)
                        st.markdown(f"""
                        **Expected Payment:** ~{expected_date.strftime('%B %d, %Y')}  
                        **Timeline:** ~{days} days from activation  
                        **Risk Level:** {"🟢 Low" if days <= 30 else "🟡 Medium" if days <= 60 else "🔴 High"}
                        """)
                    except:
                        st.markdown(f"""
                        **Payment Terms:** {terms}  
                        **Timeline:** Variable  
                        **Risk Level:** 🟡 Assess carefully
                        """)
                else:
                    st.markdown(f"""
                    **Payment Terms:** {terms}  
                    **Timeline:** Review terms carefully  
                    **Risk Level:** 🟡 Assess carefully
                    """)
                
                # Platform fee explanation
                st.markdown("#### 🏦 Platform Fee")
                st.markdown("""
                • 10% of profit goes to platform  
                • Deducted automatically on payout  
                • Ensures platform sustainability  
                """)
        
        # All-or-Nothing Warning
        if status == 'Pending':
            st.warning(f"""
            ⚠️ **All-or-Nothing Funding:** This invoice only activates if ALL {format_number(chunks_total)} chunks are purchased. 
            If not fully funded, all purchases will be voided.
            """)
        
        st.markdown("---")

def app(conn):
    # Breadcrumb navigation
    st.markdown("🏠 [Home](#) > 🛒 **Browse Invoices**")
    if st.button("← Back to Home", key="back_to_home"):
        navigate_to("Home")
    st.markdown("---")
    
    st.title("🛒 Browse Investment Opportunities")
    st.markdown("**Find high-yield short-term investments backed by real invoices**")
    
    if not st.session_state.selected_user:
        st.error("🚫 Please select a user from the sidebar to view investment opportunities")
        return
    
    # Filter options
    st.markdown("### 🔍 Filter Options")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        show_status = st.selectbox("Status Filter:", ["All", "Pending Only", "Active Only"], index=1)
    
    with filter_col2:
        min_roi = st.slider("Minimum ROI %:", 0, 50, 0, step=5)
    
    with filter_col3:
        max_timeline = st.selectbox("Max Timeline:", ["Any", "≤30 days", "≤60 days", "≤90 days"])
    
    # Get invoices
    invoices = invoice_model.get_all_invoices(conn)
    
    if not invoices:
        st.info("🎯 No invoices available at the moment. Check back later for new investment opportunities!")
        return
    
    # Apply filters
    filtered_invoices = []
    for invoice in invoices:
        invoice_id, owner_id, debtor, amount, terms, sale_price, chunks_total, chunks_sold, status = invoice
        
        # Status filter
        if show_status == "Pending Only" and status != "Pending":
            continue
        elif show_status == "Active Only" and status != "Active":
            continue
        
        # ROI filter
        if chunks_total > 0:
            gross_profit_per_chunk = (amount / chunks_total) - 100
            platform_fee_per_chunk = gross_profit_per_chunk * 0.10
            net_profit_per_chunk = gross_profit_per_chunk - platform_fee_per_chunk
            roi = (net_profit_per_chunk / 100 * 100) if net_profit_per_chunk > 0 else 0
            
            if roi < min_roi:
                continue
        
        # Timeline filter (basic implementation)
        if max_timeline != "Any":
            # This is a simplified filter - in production you'd want more sophisticated date parsing
            if max_timeline == "≤30 days" and "60" in terms:
                continue
            elif max_timeline == "≤60 days" and "90" in terms:
                continue
        
        filtered_invoices.append(invoice)
    
    # Results summary
    st.markdown(f"### 📊 Found {len(filtered_invoices)} Investment Opportunities")
    
    if not filtered_invoices:
        st.info("No invoices match your current filters. Try adjusting the criteria above.")
        return
    
    # Sort by status (Pending first, then Active)
    filtered_invoices.sort(key=lambda x: (x[8] != 'Pending', x[0]))  # Sort by status, then by ID
    
    # Display opportunities
    for invoice in filtered_invoices:
        render_investment_opportunity(invoice, conn)
    
    # Footer with tips
    st.markdown("---")
    st.markdown("### 💡 Investment Tips")
    
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.markdown("""
        **✅ Good Investments:**
        • Established companies as debtors
        • Short payment terms (Net 30 or less)
        • Clear, specific payment terms
        • Reasonable discount (5-15%)
        """)
    
    with tip_col2:
        st.markdown("""
        **⚠️ Consider Carefully:**
        • Very high returns (might be risky)
        • Vague payment terms
        • Unknown debtor companies
        • Long payment terms (>60 days)
        """)
    
    st.info("💰 Remember: All returns shown are AFTER the 10% platform fee is deducted.")