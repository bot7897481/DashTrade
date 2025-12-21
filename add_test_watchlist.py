
from auth import UserDB
import sqlite3
import os

# Connect to DB
conn = sqlite3.connect('dashtrade.db') # Assuming SQLite based on local config
cur = conn.cursor()

# Get user ID
cur.execute("SELECT id FROM users WHERE username='testadmin'")
res = cur.fetchone()
if res:
    user_id = res[0]
    print(f"Found testadmin ID: {user_id}")
    
    # Add to watchlist
    # Table: watchlist (id, user_id, symbol, name, added_at, notes)
    try:
        cur.execute("INSERT INTO watchlist (user_id, symbol, name) VALUES (?, ?, ?)", (user_id, 'AAPL', 'Apple Inc.'))
        conn.commit()
        print("Added AAPL to watchlist")
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
else:
    print("User not found")
    
conn.close()
