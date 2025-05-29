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
    """Render a detailed investment opportunity card with slider interface"""
    invoice_id, owner_id, debtor, amount, terms, sale_price, chunks_total, chunks_sold, status = invoice_data
    
    remaining_chunks = chunks_total - chunks_sold
    funding_progress = (chunks_sold / chunks_total * 100) if chunks_total > 0 else 0
    
    # Main container with enhanced styling
    with st.container():
        st.markdown(f"""
        <div style="border: 2px solid #e1e5e9; border-radius: 15px; padding: 25px; margin: 20px 0; background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin: 0; font-size: 1.5em;">🏢 {debtor}</h2>
                <span style="background: {'linear-gradient(45deg, #28a745, #20c997)' if status == 'Active' else 'linear-gradient(45deg, #ffc107, #fd7e14)'}; color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 0.9em;">
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
                **💰 Original Invoice:** {format_currency(amount)}  
                **📅 Payment Terms:** {terms}  
                **🆔 Invoice ID:** #{invoice_id}
                """)
            
            with detail_col2:
                st.markdown(f"""
                **🎯 Target Amount:** {format_currency(sale_price)}  
                **📦 Total Chunks:** {format_number(chunks_total)} × ฿100  
                **💸 Your Discount:** {format_currency(amount - sale_price)}
                """)
            
            # Funding Progress with enhanced visualization
            st.markdown("### 📊 Funding Progress")
            progress_col1, progress_col2, progress_col3 = st.columns([2, 1, 1])
            
            with progress_col1:
                st.progress(funding_progress / 100, text=f"{funding_progress:.1f}% funded")
            with progress_col2:
                st.metric("✅ Sold", f"{format_number(chunks_sold)}")
            with progress_col3:
                st.metric("🎯 Remaining", f"{format_number(remaining_chunks)}")
        
        with col_right:
            # Enhanced Investment Calculator with Slider
            st.markdown("### 💰 Investment Calculator")
            
            if status == 'Pending' and remaining_chunks > 0:
                # Chunk selector with SLIDER
                st.markdown("**Select Number of Chunks:**")
                chunks_to_buy = st.slider(
                    "",
                    min_value=1,
                    max_value=remaining_chunks,
                    value=min(5, remaining_chunks),
                    key=f"slider_{invoice_id}",
                    help=f"Each chunk costs ฿100. {remaining_chunks} chunks available."
                )
                
                # Real-time investment amount display
                investment_amount = chunks_to_buy * 100
                st.markdown(f"**💸 Investment Amount: {format_currency(investment_amount)}**")
                
                # Calculate metrics
                metrics = calculate_investment_metrics(amount, chunks_total, chunks_to_buy)
                
                # Enhanced Investment summary box
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #28a745; margin: 15px 0;">
                    <h4 style="margin-top: 0; color: #155724; text-align: center;">💎 Your Investment</h4>
                    <div style="text-align: center;">
                        <p style="font-size: 1.1em; margin: 8px 0;"><strong>💰 You Pay:</strong> <span style="color: #dc3545;">{format_currency(metrics['investment_amount'])}</span></p>
                        <p style="font-size: 1.1em; margin: 8px 0;"><strong>💵 You Get Back:</strong> <span style="color: #28a745;">{format_currency(metrics['net_return'])}</span></p>
                        <p style="font-size: 1.2em; margin: 8px 0; font-weight: bold;"><strong>🚀 Your Profit:</strong> <span style="color: #007bff;">{format_currency(metrics['net_profit'])} ({metrics['net_roi']:.1f}% ROI)</span></p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced Buy button
                if st.button(f"🛒 Buy {chunks_to_buy} Chunk{'s' if chunks_to_buy > 1 else ''} for {format_currency(investment_amount)}", 
                           key=f"buy_{invoice_id}", 
                           use_container_width=True,
                           type="primary"):
                    if st.session_state.selected_user:
                        transaction_model.purchase_chunks(
                            conn, invoice_id, st.session_state.selected_user['user_id'], chunks_to_buy
                        )
                        
                        # Check activation
                        activated = check_invoice_activation(conn, invoice_id)
                        
                        if activated:
                            st.success(f"🎉 Purchased {chunks_to_buy} chunks! Invoice is now FULLY FUNDED and ACTIVE!")
                            st.balloons()
                        else:
                            st.success(f"✅ Successfully purchased {chunks_to_buy} chunks!")
                        
                        st.rerun()
                    else:
                        st.error("Please select a user first!")
            
            elif status == 'Active':
                st.markdown("""
                <div style="background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%); padding: 20px; border-radius: 12px; text-align: center;">
                    <h3 style="color: #0c5460; margin: 0;">✅ FULLY FUNDED</h3>
                    <p style="margin: 10px 0; color: #0c5460;">This invoice is active and waiting for debtor payment.</p>
                </div>
                """, unsafe_allow_html=True)
            
            else:
                st.info("No chunks available")
        
        # Detailed Financial Breakdown (Expandable)
        with st.expander("📈 Detailed Financial Breakdown & Risk Analysis", expanded=False):
            fin_col1, fin_col2 = st.columns(2)
            
            with fin_col1:
                st.markdown("#### 💹 Per Chunk Analysis")
                return_per_chunk = amount / chunks_total
                profit_per_chunk_gross = return_per_chunk - 100
                platform_fee_per_chunk = (profit_per_chunk_gross * 0.10)
                net_profit_per_chunk = profit_per_chunk_gross - platform_fee_per_chunk
                
                st.markdown(f"""
                **💸 Cost per chunk:** ฿100.00  
                **💰 Gross return per chunk:** {format_currency(return_per_chunk)}  
                **📈 Gross profit per chunk:** {format_currency(profit_per_chunk_gross)}  
                **🏦 Platform fee per chunk:** -{format_currency(platform_fee_per_chunk)}  
                **✨ Net profit per chunk:** {format_currency(net_profit_per_chunk)}
                """)
            
            with fin_col2:
                st.markdown("#### ⚖️ Risk & Timeline Analysis")
                
                # Calculate estimated timeline (assuming payment terms)
                if 'net' in terms.lower():
                    try:
                        days = int(''.join(filter(str.isdigit, terms)))
                        expected_date = datetime.now() + timedelta(days=days)
                        risk_level = "🟢 Low Risk" if days <= 30 else "🟡 Medium Risk" if days <= 60 else "🔴 High Risk"
                        st.markdown(f"""
                        **📅 Expected Payment:** ~{expected_date.strftime('%B %d, %Y')}  
                        **⏰ Timeline:** ~{days} days from activation  
                        **⚖️ Risk Level:** {risk_level}
                        """)
                    except:
                        st.markdown(f"""
                        **📋 Payment Terms:** {terms}  
                        **⏰ Timeline:** Variable - Review carefully  
                        **⚖️ Risk Level:** 🟡 Medium - Assess terms
                        """)
                else:
                    st.markdown(f"""
                    **📋 Payment Terms:** {terms}  
                    **⏰ Timeline:** Review terms carefully  
                    **⚖️ Risk Level:** 🟡 Medium - Assess carefully
                    """)
                
                # Enhanced Platform fee explanation
                st.markdown("#### 🏦 Platform Fee Structure")
                st.markdown("""
                • **10%** of **profit only** goes to platform  
                • Deducted automatically on payout  
                • No fees on your original investment  
                • Ensures platform sustainability  
                """)
        
        # All-or-Nothing Warning with enhanced styling
        if status == 'Pending':
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107; margin: 15px 0;">
                <h4 style="color: #856404; margin: 0;">⚠️ All-or-Nothing Funding</h4>
                <p style="color: #856404; margin: 10px 0;">This invoice only activates if <strong>ALL {format_number(chunks_total)} chunks</strong> are purchased. 
                If not fully funded, all purchases will be voided and money returned.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")

def app(conn):
    st.title("🛒 Browse Investment Opportunities")
    st.markdown("**Find high-yield short-term investments backed by real invoices**")
    
    if not st.session_state.selected_user:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545; margin: 20px 0; text-align: center;">
            <h3 style="color: #721c24; margin: 0;">🚫 User Selection Required</h3>
            <p style="color: #721c24; margin: 10px 0;">Select a user from the dropdown at the top of the page to view and purchase investment opportunities</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Enhanced Filter Section
    st.markdown("### 🔍 Investment Filters")
    
    with st.container():
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        with filter_col1:
            show_status = st.selectbox("📊 Status Filter:", ["All", "Pending Only", "Active Only"], index=1)
        
        with filter_col2:
            min_roi = st.slider("📈 Minimum ROI %:", 0, 50, 0, step=5)
        
        with filter_col3:
            max_investment = st.selectbox("💰 Max Investment:", ["Any Amount", "≤ ฿1,000", "≤ ฿5,000", "≤ ฿10,000"])
        
        with filter_col4:
            max_timeline = st.selectbox("⏰ Max Timeline:", ["Any", "≤30 days", "≤60 days", "≤90 days"])
    
    # Get invoices
    invoices = invoice_model.get_all_invoices(conn)
    
    if not invoices:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%); padding: 30px; border-radius: 15px; text-align: center; margin: 30px 0;">
            <h2 style="color: #0c5460; margin: 0;">🎯 No Investment Opportunities Available</h2>
            <p style="color: #0c5460; margin: 15px 0; font-size: 1.1em;">Check back later for new investment opportunities, or create your own invoice to get started!</p>
        </div>
        """, unsafe_allow_html=True)
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
        
        # Investment amount filter
        remaining_chunks = chunks_total - chunks_sold
        min_investment_needed = remaining_chunks * 100
        
        if max_investment == "≤ ฿1,000" and min_investment_needed > 1000:
            continue
        elif max_investment == "≤ ฿5,000" and min_investment_needed > 5000:
            continue
        elif max_investment == "≤ ฿10,000" and min_investment_needed > 10000:
            continue
        
        filtered_invoices.append(invoice)
    
    # Enhanced Results Summary
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #e2e3e5 0%, #f8f9fa 100%); padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
        <h3 style="color: #495057; margin: 0;">📊 Found {len(filtered_invoices)} Investment Opportunities</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not filtered_invoices:
        st.info("No invoices match your current filters. Try adjusting the criteria above.")
        return
    
    # Sort by status (Pending first, then Active)
    filtered_invoices.sort(key=lambda x: (x[8] != 'Pending', x[0]))  # Sort by status, then by ID
    
    # Display opportunities
    for invoice in filtered_invoices:
        render_investment_opportunity(invoice, conn)
    
    # Enhanced Footer with tips
    st.markdown("---")
    st.markdown("### 💡 Smart Investment Tips")
    
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
            <h4 style="color: #155724; margin: 0;">✅ Good Investment Indicators</h4>
            <ul style="color: #155724; margin: 10px 0;">
                <li>Established companies as debtors</li>
                <li>Short payment terms (Net 30 or less)</li>
                <li>Clear, specific payment terms</li>
                <li>Reasonable discount (5-15%)</li>
                <li>Good ROI without being too high</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with tip_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107;">
            <h4 style="color: #856404; margin: 0;">⚠️ Consider Carefully</h4>
            <ul style="color: #856404; margin: 10px 0;">
                <li>Very high returns (might indicate risk)</li>
                <li>Vague or unclear payment terms</li>
                <li>Unknown debtor companies</li>
                <li>Long payment terms (>60 days)</li>
                <li>Unusually large discounts (>20%)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #cce5ff 0%, #b3d9ff 100%); padding: 15px; border-radius: 10px; text-align: center; margin: 20px 0;">
        <p style="color: #004085; margin: 0; font-weight: bold;">💰 Remember: All returns shown are AFTER the 10% platform fee is deducted from profits.</p>
    </div>
    """, unsafe_allow_html=True)