def get_cash_transfers_by_invoice(conn, invoice_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM cash_transfers 
        WHERE invoice_id = ?
        ORDER BY event_timestamp
    """, (invoice_id,))
    return cursor.fetchall()

def get_all_cash_transfers(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ct.*, i.debtor_name, i.original_amount
        FROM cash_transfers ct
        JOIN invoices i ON ct.invoice_id = i.invoice_id
        ORDER BY ct.event_timestamp DESC
    """)
    return cursor.fetchall()