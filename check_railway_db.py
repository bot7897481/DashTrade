#!/usr/bin/env python3
"""
Railway Database Connection Checker
Run this to diagnose database connection issues.
"""
import os
import sys

def check_railway_setup():
    """Check Railway database setup"""
    print("="*70)
    print("🔍 Railway Database Connection Checker")
    print("="*70)
    
    # Check if running on Railway
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID')
    print(f"\n📍 Environment:")
    print(f"   Running on Railway: {'✅ YES' if is_railway else '❌ NO (This might be the issue!)'}")
    
    # Check DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    print(f"\n📊 Database Configuration:")
    
    if db_url:
        # Show preview (hide password)
        if '@' in db_url:
            parts = db_url.split('@')
            if len(parts) == 2:
                user_part = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
                if ':' in user_part:
                    user = user_part.split(':')[0]
                    preview = db_url.replace(user_part, f"{user}:***")
                else:
                    preview = db_url.replace(user_part, "***")
            else:
                preview = db_url[:50] + "..."
        else:
            preview = db_url[:50] + "..."
        
        print(f"   DATABASE_URL: ✅ SET")
        print(f"   Preview: {preview}")
        
        # Check if it's localhost
        if 'localhost' in db_url or '127.0.0.1' in db_url:
            print(f"\n   ⚠️  WARNING: DATABASE_URL points to localhost!")
            print(f"   This won't work on Railway!")
        elif 'railway' in db_url.lower() or 'postgres' in db_url.lower():
            print(f"   ✅ Looks like a valid Railway/PostgreSQL URL")
        else:
            print(f"   ⚠️  Unknown database URL format")
    else:
        print(f"   DATABASE_URL: ❌ NOT SET")
        print(f"\n   ⚠️  This is the problem!")
        print(f"   Railway should automatically set DATABASE_URL")
        print(f"   Check Railway → Variables → DATABASE_URL")
    
    # Try to connect
    print(f"\n🔌 Testing Connection:")
    try:
        from database import get_db_connection
        
        with get_db_connection() as conn:
            print(f"   ✅ Connection successful!")
            
            # Try a simple query
            if hasattr(conn, 'cursor'):
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()
                    if version:
                        print(f"   ✅ Database version: {version[0][:50]}...")
            
    except ConnectionError as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"\n💡 Solution:")
        print(f"   1. Make sure PostgreSQL service is added in Railway")
        print(f"   2. Check Railway → Variables → DATABASE_URL exists")
        print(f"   3. Redeploy your Railway service")
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Connection failed: {error_msg[:100]}")
        
        if 'localhost' in error_msg.lower():
            print(f"\n💡 Problem Detected:")
            print(f"   The app is trying to connect to localhost!")
            print(f"\n   This means:")
            print(f"   • You're running the app LOCALLY, not on Railway")
            print(f"   • OR DATABASE_URL is set incorrectly")
            print(f"\n   Solution:")
            print(f"   1. Don't run 'streamlit run app.py' locally")
            print(f"   2. Use your Railway app URL instead")
            print(f"   3. Railway URL looks like: https://your-app.railway.app")
    
    print("\n" + "="*70)
    print("📝 Summary:")
    if not is_railway:
        print("   ⚠️  You're NOT running on Railway")
        print("   → Use Railway URL, don't run locally!")
    elif not db_url:
        print("   ⚠️  DATABASE_URL is not set")
        print("   → Check Railway Variables")
    elif 'localhost' in db_url:
        print("   ⚠️  DATABASE_URL points to localhost")
        print("   → This won't work on Railway!")
    else:
        print("   ✅ Setup looks correct!")
    print("="*70)

if __name__ == "__main__":
    check_railway_setup()




