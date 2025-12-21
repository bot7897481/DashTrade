
from auth import UserDB
import sys

# Initialize DB if needed (usually done by app, but safe to call)
UserDB.create_users_table()

# Create test admin
print("Creating test admin...")
result = UserDB.register_user("testadmin", "test@admin.com", "testpass123", "Test Admin", "admin")

if result['success']:
    print("SUCCESS: Created testadmin")
else:
    print(f"INFO: {result['error']}")
    # If exists, update password just in case
    if "already exists" in result['error']:
        print("User exists, resetting password...")
        # Get ID
        with UserDB.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username='testadmin'")
                uid = cur.fetchone()[0]
                UserDB.update_password(uid, "oldpass", "testpass123") # Update password
                # Since update_password requires old password, we might just force update hash manually
                from bcrypt import hashpw, gensalt
                hashed = hashpw("testpass123".encode('utf-8'), gensalt()).decode('utf-8')
                cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hashed, uid))
                conn.commit()
        print("SUCCESS: Reset password for testadmin")
