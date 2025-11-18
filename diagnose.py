#!/usr/bin/env python3
"""
Diagnostic script to check DashTrade setup
Run this to identify issues preventing the app from starting
"""
import sys
import os

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def check_python_version():
    print_header("Python Version")
    print(f"✅ Python {sys.version}")
    if sys.version_info >= (3, 11):
        print("✅ Python version is compatible (3.11+)")
        return True
    else:
        print("❌ Python version too old. Need 3.11+")
        return False

def check_environment():
    print_header("Environment Variables")

    database_url = os.getenv('DATABASE_URL')
    encryption_key = os.getenv('ENCRYPTION_KEY')

    if database_url:
        print(f"✅ DATABASE_URL is set")
    else:
        print("❌ DATABASE_URL is NOT set")
        print("   → Add your PostgreSQL URL to Replit Secrets")

    if encryption_key:
        print(f"✅ ENCRYPTION_KEY is set")
    else:
        print("⚠️  ENCRYPTION_KEY is NOT set (needed for Trading Bot)")
        print("   → Run: python3 encryption.py")
        print("   → Add the key to Replit Secrets")

    return bool(database_url)

def check_imports():
    print_header("Required Packages")

    packages = {
        'streamlit': 'Streamlit',
        'pandas': 'Pandas',
        'yfinance': 'yfinance',
        'plotly': 'Plotly',
        'psycopg2': 'PostgreSQL driver',
        'bcrypt': 'bcrypt',
        'cryptography': 'Cryptography',
    }

    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✅ {name}: installed")
        except ImportError:
            print(f"❌ {name}: NOT installed")
            all_ok = False

    # Check alpaca-py specifically
    try:
        from alpaca.trading.client import TradingClient
        print(f"✅ alpaca-py: installed")
    except ImportError:
        print(f"❌ alpaca-py: NOT installed")
        print("   → Run: upm install")
        all_ok = False

    return all_ok

def check_files():
    print_header("Required Files")

    required_files = [
        'app.py',
        'auth.py',
        'database.py',
        'bot_database.py',
        'bot_engine.py',
        'pages/7_🤖_Trading_Bot.py',
    ]

    all_ok = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_ok = False

    return all_ok

def check_syntax():
    print_header("Python Syntax Check")

    files_to_check = [
        'app.py',
        'bot_engine.py',
        'bot_database.py',
        'pages/7_🤖_Trading_Bot.py',
    ]

    all_ok = True
    for file in files_to_check:
        if not os.path.exists(file):
            continue

        try:
            with open(file, 'r') as f:
                compile(f.read(), file, 'exec')
            print(f"✅ {file}: syntax OK")
        except SyntaxError as e:
            print(f"❌ {file}: SYNTAX ERROR")
            print(f"   Line {e.lineno}: {e.msg}")
            all_ok = False

    return all_ok

def check_database_connection():
    print_header("Database Connection")

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Cannot test - DATABASE_URL not set")
        return False

    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        print("✅ Database connection successful")

        # Check for bot tables
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('user_api_keys', 'user_bot_configs', 'bot_trades')
        """)
        tables = cur.fetchall()

        if len(tables) >= 3:
            print(f"✅ Bot tables exist ({len(tables)} found)")
        else:
            print(f"⚠️  Bot tables missing ({len(tables)}/6 found)")
            print("   → Run: python3 setup_bot_database.py")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    print("\n" + "🔍" * 30)
    print("  DashTrade Diagnostic Tool")
    print("🔍" * 30)

    results = {
        'Python': check_python_version(),
        'Environment': check_environment(),
        'Packages': check_imports(),
        'Files': check_files(),
        'Syntax': check_syntax(),
        'Database': check_database_connection(),
    }

    print_header("SUMMARY")

    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\nYour app should start. Try running:")
        print("  streamlit run app.py --server.port 5000")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nFix the issues above, then run this script again.")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
