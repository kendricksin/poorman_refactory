def create_invoice(conn, owner_id, debtor, original_amount, terms, sale_price):
    chunks_total = int(sale_price // 100)
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoices (
            owner_user_id, debtor_name, original_amount, 
            payment_terms, desired_sale_price, chunks_total
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (owner_id, debtor, original_amount, terms, sale_price, chunks_total))
    
    conn.commit()
    return cursor.lastrowid

def get_all_invoices(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM invoices 
        WHERE status IN ('Pending', 'Active')
        ORDER BY invoice_id DESC
    """)
    return cursor.fetchall()

def purchase_chunks(conn, invoice_id, buyer_id, chunks):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE invoices 
        SET chunks_sold = chunks_sold + ?
        WHERE invoice_id = ?
    """, (chunks, invoice_id))
    
    cursor.execute("""
        INSERT INTO transactions (
            invoice_id, buyer_user_id, chunks_purchased
        ) VALUES (?, ?, ?)
    """, (invoice_id, buyer_id, chunks))
    
    conn.commit()

def get_invoices_by_owner(conn, owner_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM invoices 
        WHERE owner_user_id = ?
        ORDER BY invoice_id DESC
    """, (owner_id,))
    return cursor.fetchall()