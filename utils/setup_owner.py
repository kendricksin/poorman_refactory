# utils/setup_platform_owner.py

def setup_platform_owner(conn):
    """
    Create or verify the PLATFORM OWNER user exists.
    This user automatically receives 10% of profits from all deals.
    """
    cursor = conn.cursor()
    
    # Check if PLATFORM OWNER already exists
    cursor.execute("SELECT user_id FROM users WHERE username = 'PLATFORM OWNER'")
    existing = cursor.fetchone()
    
    if existing:
        print(f"PLATFORM OWNER already exists with ID: {existing[0]}")
        return existing[0]
    else:
        # Create the PLATFORM OWNER user
        cursor.execute("INSERT INTO users (username) VALUES ('PLATFORM OWNER')")
        platform_owner_id = cursor.lastrowid
        conn.commit()
        
        print(f"Created PLATFORM OWNER with ID: {platform_owner_id}")
        return platform_owner_id

def get_platform_owner_id(conn):
    """Get the platform owner's user ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = 'PLATFORM OWNER'")
    result = cursor.fetchone()
    
    if not result:
        # Create platform owner if doesn't exist
        return setup_platform_owner(conn)
    
    return result[0]

if __name__ == "__main__":
    import sqlite3
    conn = sqlite3.connect("invoice.db")
    setup_platform_owner(conn)
    conn.close()