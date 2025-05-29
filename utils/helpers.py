def format_currency(amount):
    return f"฿{amount:.2f}"

def calculate_profit(original_amount, sale_price, chunks_sold):
    chunk_value = original_amount / sale_price * 100
    return format_currency(chunk_value - 100)

def check_invoice_activation(conn, invoice_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT chunks_sold, chunks_total, invoice_id 
        FROM invoices WHERE invoice_id = ?
    """, (invoice_id,))
    
    invoice = cursor.fetchone()
    
    if invoice and invoice[0] >= invoice[1]:
        cursor.execute("""
            UPDATE invoices 
            SET status = 'Active' 
            WHERE invoice_id = ?
        """, (invoice_id,))
        
        # Create cash transfer for funding
        cursor.execute("""
            INSERT INTO cash_transfers (
                invoice_id, event_description, amount, from_party, to_party
            ) VALUES (?, ?, ?, ?, ?)
        """, (invoice_id, "Invoice Fully Funded", invoice[1]*100, "Buyers", "Invoice Owner"))
        
        conn.commit()
        return True
    return False

def process_invoice_payment(conn, invoice_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT original_amount, chunks_total, invoice_id 
        FROM invoices WHERE invoice_id = ?
    """, (invoice_id,))
    
    invoice = cursor.fetchone()
    
    if invoice and invoice[2]:
        cursor.execute("UPDATE invoices SET status = 'Paid' WHERE invoice_id = ?", (invoice_id,))
        
        # Get all transactions for this invoice
        cursor.execute("""
            SELECT buyer_user_id, chunks_purchased 
            FROM transactions 
            WHERE invoice_id = ?
        """, (invoice_id,))
        
        transactions = cursor.fetchall()
        payout_per_chunk = invoice[0] / invoice[1]
        
        for buyer_id, chunks in transactions:
            amount = chunks * payout_per_chunk
            
            cursor.execute("""
                INSERT INTO cash_transfers (
                    invoice_id, event_description, amount, from_party, to_party
                ) VALUES (?, ?, ?, ?, ?)
            """, (invoice_id, f"Payout to Buyer {buyer_id}", amount, "Debtor", f"Buyer {buyer_id}"))
        
        conn.commit()
        return True
    return False