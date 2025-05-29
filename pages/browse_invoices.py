import streamlit as st
from models import invoice as invoice_model
from models import transaction as transaction_model
from components.invoice_card import render_invoice_card

def app(conn):
    st.title("Browse Available Invoices")
    
    invoices = invoice_model.get_all_invoices(conn)

    if not st.session_state.selected_user:
        st.warning("Please select a user in the User Management tab first")
        return
    
    if not invoices:
        st.info("No available invoices at the moment.")
        return
    
    for invoice in invoices:
        invoice_id, owner_id, debtor, amount, terms, sale_price, chunks_total, chunks_sold, status = invoice
        
        with st.container():
            render_invoice_card(
                invoice_id=invoice_id,
                debtor=debtor,
                amount=amount,
                sale_price=sale_price,
                chunks_total=chunks_total,
                chunks_sold=chunks_sold,
                status=status
            )
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                remaining = chunks_total - chunks_sold
                st.write(f"**Chunks Remaining:** {remaining}")
                
            with col2:
                remaining = chunks_total - chunks_sold
                if status == 'Pending' and remaining > 0:
                    chunks_to_buy = st.number_input(
                        "Chunks to Buy", 
                        min_value=1, 
                        max_value=remaining,
                        key=f"buy_{invoice_id}"
                    )
                    
                    if st.button(f"Buy {chunks_to_buy} Chunks", key=f"btn_{invoice_id}"):
                        transaction_model.purchase_chunks(
                            conn, invoice_id, st.session_state.selected_user['user_id'], chunks_to_buy
                        )
                        st.success(f"Purchased {chunks_to_buy} chunks!")
                        st.experimental_rerun()
                else:
                    st.info("Fully Funded")