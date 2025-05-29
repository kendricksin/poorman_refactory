# pages/cash_transfers_page.py

import streamlit as st

def app(conn):
    st.title("All Cash Transfer History")
    st.markdown("This page shows all financial transactions across all invoices and users.")

    cursor = conn.cursor()
    
    # Get all unique invoices with transfer data
    cursor.execute("""
        SELECT DISTINCT i.invoice_id, i.debtor_name, i.original_amount
        FROM invoices i
        JOIN cash_transfers ct ON i.invoice_id = ct.invoice_id
        ORDER BY i.invoice_id DESC
    """)
    invoices = cursor.fetchall()

    if not invoices:
        st.info("No cash transfers recorded yet.")
        return

    for invoice in invoices:
        invoice_id, debtor_name, original_amount = invoice
        
        with st.expander(f"Invoice #{invoice_id} - {debtor_name} | Amount: ฿{original_amount}"):
            cursor.execute("""
                SELECT event_description, event_timestamp, amount, from_party, to_party
                FROM cash_transfers
                WHERE invoice_id = ?
                ORDER BY event_timestamp ASC
            """, (invoice_id,))
            transfers = cursor.fetchall()

            if transfers:
                for transfer in transfers:
                    event_desc, timestamp, amount, from_party, to_party = transfer
                    st.write(f"**{timestamp}** | {event_desc}")
                    st.markdown(f"💰 ฿{amount:.2f} | From: {from_party} → To: {to_party}")
                    st.divider()
            else:
                st.write("No transfers recorded for this invoice.")