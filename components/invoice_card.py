import streamlit as st

def render_invoice_card(invoice_id, debtor, amount, sale_price, chunks_total, chunks_sold, status):
    progress = (chunks_sold / chunks_total) * 100 if chunks_total > 0 else 0
    
    with st.container():
        st.markdown(f"""
        <div style="border:1px solid #ccc; border-radius:5px; padding:15px; margin:10px 0;">
            <h4>{debtor}</h4>
            <p>Original Amount: {amount} THB</p>
            <p>Sale Price: {sale_price} THB</p>
            <p>Status: {status}</p>
            <div style="background: #f0f0f0; border-radius: 5px; height: 20px;">
                <div style="width: {progress}%; background: #4CAF50; height: 100%; border-radius: 5px;"></div>
            </div>
            <p>{chunks_sold}/{chunks_total} chunks sold</p>
        </div>
        """, unsafe_allow_html=True)