def get_cash_transfers_by_invoice(conn, invoice_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM cash_transfers 
        WHERE invoice_id = ?
        ORDER BY event_timestamp
    """, (invoice_id,))
    return cursor.fetchall()