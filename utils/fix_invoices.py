# utils/fix_existing_data.py

def fix_all_pending_invoices(conn):
    """
    Check all pending invoices and activate those that should be active.
    This fixes invoices created before the activation logic was implemented.
    """
    cursor = conn.cursor()
    
    # Get all pending invoices that are actually fully funded
    cursor.execute("""
        SELECT invoice_id, chunks_sold, chunks_total, desired_sale_price, owner_user_id
        FROM invoices 
        WHERE status = 'Pending' AND chunks_sold >= chunks_total
    """)
    
    invoices_to_fix = cursor.fetchall()
    fixed_count = 0
    
    for invoice_data in invoices_to_fix:
        invoice_id, chunks_sold, chunks_total, sale_price, owner_id = invoice_data
        
        print(f"Fixing Invoice #{invoice_id}: {chunks_sold}/{chunks_total} chunks")
        
        # Update invoice status to Active
        cursor.execute("""
            UPDATE invoices 
            SET status = 'Active' 
            WHERE invoice_id = ?
        """, (invoice_id,))
        
        # Update all related transactions to Active status
        cursor.execute("""
            UPDATE transactions 
            SET status = 'Active'
            WHERE invoice_id = ? AND status = 'Pending Activation'
        """, (invoice_id,))
        
        # Create cash transfer record for the funding event
        funding_amount = chunks_total * 100
        cursor.execute("""
            INSERT INTO cash_transfers (
                invoice_id, event_description, amount, from_party, to_party
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            invoice_id, 
            "Invoice Fully Funded - Cash Released to Owner (Auto-Fixed)", 
            funding_amount, 
            "Collective Buyers", 
            f"Invoice Owner (User {owner_id})"
        ))
        
        fixed_count += 1
    
    conn.commit()
    return fixed_count

if __name__ == "__main__":
    import sqlite3
    conn = sqlite3.connect("invoice.db")
    fixed = fix_all_pending_invoices(conn)
    print(f"Fixed {fixed} invoices that should have been active")
    conn.close()