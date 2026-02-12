#!/usr/bin/env python3
"""
Check password reset activity in the database
"""
from auth import UserDB
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime

def check_password_reset_activity():
    """Check recent password reset tokens"""
    try:
        # Ensure table exists
        UserDB.create_password_reset_tokens_table()
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get recent tokens
                cur.execute("""
                    SELECT 
                        prt.id,
                        prt.user_id,
                        u.email,
                        u.username,
                        prt.token,
                        prt.expires_at,
                        prt.used,
                        prt.created_at
                    FROM password_reset_tokens prt
                    JOIN users u ON prt.user_id = u.id
                    ORDER BY prt.created_at DESC
                    LIMIT 10
                """)
                
                tokens = cur.fetchall()
                
                print("=" * 80)
                print("RECENT PASSWORD RESET TOKENS")
                print("=" * 80)
                print()
                
                if not tokens:
                    print("No password reset tokens found in the database.")
                    print("This could mean:")
                    print("  1. No password reset requests have been made yet")
                    print("  2. The table hasn't been created yet")
                    print("  3. All tokens have been deleted")
                    return
                
                for token in tokens:
                    expires_at = token['expires_at']
                    created_at = token['created_at']
                    now = datetime.now()
                    
                    # Check if expired
                    is_expired = now > expires_at if expires_at else False
                    time_until_expiry = expires_at - now if expires_at and not is_expired else None
                    
                    status = "✅ VALID" if not token['used'] and not is_expired else \
                             "❌ USED" if token['used'] else \
                             "⏰ EXPIRED"
                    
                    print(f"Token ID: {token['id']}")
                    print(f"  User: {token['username']} ({token['email']})")
                    print(f"  User ID: {token['user_id']}")
                    print(f"  Token: {token['token'][:30]}...")
                    print(f"  Status: {status}")
                    print(f"  Created: {created_at}")
                    print(f"  Expires: {expires_at}")
                    if time_until_expiry:
                        minutes_left = time_until_expiry.total_seconds() / 60
                        print(f"  Time Left: {int(minutes_left)} minutes")
                    print()
                
                # Summary
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN used = TRUE THEN 1 END) as used_count,
                        COUNT(CASE WHEN used = FALSE AND expires_at > NOW() THEN 1 END) as active_count,
                        COUNT(CASE WHEN used = FALSE AND expires_at <= NOW() THEN 1 END) as expired_count
                    FROM password_reset_tokens
                """)
                
                stats = cur.fetchone()
                if stats:
                    print("-" * 80)
                    print("SUMMARY")
                    print("-" * 80)
                    print(f"Total Tokens:     {stats['total']}")
                    print(f"Active (Valid):   {stats['active_count']}")
                    print(f"Used:             {stats['used_count']}")
                    print(f"Expired:          {stats['expired_count']}")
                    print()
                
    except Exception as e:
        print(f"Error checking password reset activity: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_password_reset_activity()

