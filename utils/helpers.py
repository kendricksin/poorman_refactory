def format_currency(amount):
    return f"฿{amount:,.2f}"

def format_number(number):
    """Format numbers with comma separators"""
    if isinstance(number, int):
        return f"{number:,}"
    else:
        return f"{number:,.2f}"

def calculate_profit(original_amount, sale_price, chunks_sold):
    chunk_value = original_amount / sale_price * 100
    return format_currency(chunk_value - 100)

def check_invoice_activation(conn, invoice_id):
    """
    Check if an invoice should be activated (all chunks sold) and update status accordingly.
    Returns True if invoice was activated, False otherwise.
    """
    cursor = conn.cursor()
    
    # Get current invoice status
    cursor.execute("""
        SELECT chunks_sold, chunks_total, status, desired_sale_price, owner_user_id
        FROM invoices 
        WHERE invoice_id = ?
    """, (invoice_id,))
    
    invoice = cursor.fetchone()
    
    if not invoice:
        return False
    
    chunks_sold, chunks_total, current_status, sale_price, owner_id = invoice
    
    # Only activate if currently pending and all chunks are sold
    if current_status == 'Pending' and chunks_sold >= chunks_total:
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
        funding_amount = chunks_total * 100  # Total amount buyers paid
        cursor.execute("""
            INSERT INTO cash_transfers (
                invoice_id, event_description, amount, from_party, to_party
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            invoice_id, 
            "Invoice Fully Funded - Cash Released to Owner", 
            funding_amount, 
            "Collective Buyers", 
            f"Invoice Owner (User {owner_id})"
        ))
        
        conn.commit()
        return True
    
    return False

def get_platform_owner_id(conn):
    """Get or create the platform owner's user ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = 'PLATFORM OWNER'")
    result = cursor.fetchone()
    
    if not result:
        # Create platform owner if doesn't exist
        cursor.execute("INSERT INTO users (username) VALUES ('PLATFORM OWNER')")
        platform_owner_id = cursor.lastrowid
        conn.commit()
        return platform_owner_id
    
    return result[0]

def process_invoice_owner_payment(conn, invoice_id, owner_id):
    """
    Process when the invoice owner confirms the original debtor has paid.
    This triggers payouts to all chunk buyers, with 10% platform fee deducted from profits.
    """
    cursor = conn.cursor()
    
    # Get invoice details and verify ownership
    cursor.execute("""
        SELECT original_amount, chunks_total, owner_user_id, status
        FROM invoices 
        WHERE invoice_id = ?
    """, (invoice_id,))
    
    invoice = cursor.fetchone()
    
    if not invoice:
        raise ValueError("Invoice not found")
        
    original_amount, chunks_total, invoice_owner_id, current_status = invoice
    
    # Verify ownership
    if owner_id != invoice_owner_id:
        raise ValueError("User is not the owner of this invoice")
    
    # Verify invoice is active
    if current_status != 'Active':
        raise ValueError("Invoice must be Active to process payment")
    
    # Get platform owner ID
    platform_owner_id = get_platform_owner_id(conn)
    
    # Update invoice status to Paid
    cursor.execute("""
        UPDATE invoices 
        SET status = 'Paid' 
        WHERE invoice_id = ?
    """, (invoice_id,))
    
    # Update all transactions to Paid status
    cursor.execute("""
        UPDATE transactions 
        SET status = 'Paid Out'
        WHERE invoice_id = ? AND status = 'Active'
    """, (invoice_id,))
    
    # Get all buyers for this invoice
    cursor.execute("""
        SELECT DISTINCT buyer_user_id, SUM(chunks_purchased) as total_chunks
        FROM transactions 
        WHERE invoice_id = ?
        GROUP BY buyer_user_id
    """, (invoice_id,))
    
    buyers = cursor.fetchall()
    
    # Calculate profit and platform fee
    total_paid_by_buyers = chunks_total * 100  # Each chunk costs ฿100
    total_profit = original_amount - total_paid_by_buyers
    platform_fee = total_profit * 0.10  # 10% of profit
    net_profit_for_buyers = total_profit - platform_fee
    
    # Calculate adjusted payout per chunk (original proportional share minus platform fee)
    base_payout_per_chunk = original_amount / chunks_total
    platform_fee_per_chunk = platform_fee / chunks_total
    net_payout_per_chunk = base_payout_per_chunk - platform_fee_per_chunk
    
    # Record cash transfer from debtor to owner first
    cursor.execute("""
        INSERT INTO cash_transfers (
            invoice_id, event_description, amount, from_party, to_party
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        invoice_id, 
        "Original Invoice Paid by Debtor", 
        original_amount, 
        "Debtor", 
        f"Invoice Owner (User {owner_id})"
    ))
    
    # Record platform fee (if any profit exists)
    if platform_fee > 0.01:
        cursor.execute("""
            INSERT INTO cash_transfers (
                invoice_id, event_description, amount, from_party, to_party
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            invoice_id, 
            f"Platform Fee (10% of ฿{total_profit:.2f} profit)", 
            platform_fee, 
            f"Invoice Owner (User {owner_id})", 
            f"PLATFORM OWNER (User {platform_owner_id})"
        ))
    
    # Record payout to each buyer (net amount after platform fee)
    total_buyer_payouts = 0
    for buyer_id, chunks in buyers:
        buyer_payout = chunks * net_payout_per_chunk
        total_buyer_payouts += buyer_payout
        
        cursor.execute("""
            INSERT INTO cash_transfers (
                invoice_id, event_description, amount, from_party, to_party
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            invoice_id, 
            f"Payout to Buyer - {chunks} chunks @ ฿{net_payout_per_chunk:.2f}/chunk (after 10% platform fee)", 
            buyer_payout, 
            f"Invoice Owner (User {owner_id})", 
            f"Buyer (User {buyer_id})"
        ))
    
    # Record any remaining amount kept by invoice owner (should be minimal)
    remaining_with_owner = original_amount - platform_fee - total_buyer_payouts
    if remaining_with_owner > 0.01:  # Only record if meaningful amount
        cursor.execute("""
            INSERT INTO cash_transfers (
                invoice_id, event_description, amount, from_party, to_party
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            invoice_id, 
            "Remaining Amount with Invoice Owner", 
            remaining_with_owner, 
            f"Invoice Owner (User {owner_id})", 
            f"Invoice Owner (User {owner_id})"
        ))
    
    conn.commit()
    return True

def get_user_summary(conn, user_id):
    """Get summary statistics for a specific user"""
    cursor = conn.cursor()
    
    # Invoices owned
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(original_amount), 0)
        FROM invoices 
        WHERE owner_user_id = ?
    """, (user_id,))
    owned_count, owned_value = cursor.fetchone()
    
    # Chunks purchased
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(chunks_purchased), 0)
        FROM transactions 
        WHERE buyer_user_id = ?
    """, (user_id,))
    investment_count, chunks_bought = cursor.fetchone()
    
    # Calculate investment value
    investment_value = chunks_bought * 100
    
    return {
        'owned_invoices': owned_count,
        'owned_value': owned_value,
        'investments': investment_count,
        'investment_value': investment_value,
        'chunks_bought': chunks_bought
    }