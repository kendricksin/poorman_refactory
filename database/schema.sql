-- schema.sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE invoices (
    invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL,
    debtor_name TEXT NOT NULL,
    original_amount REAL NOT NULL,
    payment_terms TEXT,
    desired_sale_price REAL NOT NULL,
    chunks_total INTEGER NOT NULL,
    chunks_sold INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id)
);

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    buyer_user_id INTEGER NOT NULL,
    chunks_purchased INTEGER NOT NULL,
    purchase_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Pending Activation',
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (buyer_user_id) REFERENCES users(user_id)
);

CREATE TABLE cash_transfers (
    transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    event_description TEXT NOT NULL,
    event_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    amount REAL NOT NULL,
    from_party TEXT NOT NULL,
    to_party TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
);