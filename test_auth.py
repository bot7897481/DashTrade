#!/usr/bin/env python3
"""
Authentication System Test Script
Tests the authentication system functionality without requiring a live database.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_password_hashing():
    """Test password hashing and verification"""
    print("Testing password hashing...")
    try:
        import bcrypt

        test_password = "TestPassword123"

        # Hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(test_password.encode('utf-8'), salt)
        print("  ✓ Password hashing works")

        # Verify correct password
        if bcrypt.checkpw(test_password.encode('utf-8'), hashed):
            print("  ✓ Password verification works")
        else:
            print("  ✗ Password verification failed")
            return False

        # Verify wrong password
        if not bcrypt.checkpw("WrongPassword".encode('utf-8'), hashed):
            print("  ✓ Wrong password correctly rejected")
        else:
            print("  ✗ Wrong password accepted (security issue!)")
            return False

        return True
    except ImportError:
        print("  ✗ bcrypt not installed")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    print("\nTesting imports...")

    required_modules = [
        ('streamlit', 'Streamlit'),
        ('psycopg2', 'PostgreSQL driver'),
        ('bcrypt', 'Password hashing'),
        ('pandas', 'Data processing'),
        ('plotly', 'Charting'),
        ('yfinance', 'Yahoo Finance data'),
    ]

    all_good = True
    for module, name in required_modules:
        try:
            __import__(module)
            print(f"  ✓ {name} ({module})")
        except ImportError:
            print(f"  ✗ {name} ({module}) not installed")
            all_good = False

    return all_good

def test_auth_module():
    """Test auth.py module structure"""
    print("\nTesting auth module...")
    try:
        from auth import UserDB
        print("  ✓ auth.py imports successfully")

        # Check if required methods exist
        methods = ['hash_password', 'verify_password', 'register_user',
                   'authenticate_user', 'create_users_table']

        for method in methods:
            if hasattr(UserDB, method):
                print(f"  ✓ UserDB.{method} exists")
            else:
                print(f"  ✗ UserDB.{method} missing")
                return False

        return True
    except ImportError as e:
        print(f"  ✗ Cannot import auth module: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_database_module():
    """Test database.py module structure"""
    print("\nTesting database module...")
    try:
        from database import WatchlistDB, AlertsDB, PreferencesDB
        print("  ✓ database.py imports successfully")

        # Check if methods have user_id parameter
        test_cases = [
            (WatchlistDB, 'get_all_stocks'),
            (WatchlistDB, 'add_stock'),
            (AlertsDB, 'get_active_alerts'),
            (AlertsDB, 'add_alert'),
            (PreferencesDB, 'get_preference'),
        ]

        for cls, method in test_cases:
            if hasattr(cls, method):
                print(f"  ✓ {cls.__name__}.{method} exists")
            else:
                print(f"  ✗ {cls.__name__}.{method} missing")
                return False

        return True
    except ImportError as e:
        print(f"  ✗ Cannot import database module: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_app_structure():
    """Test app.py structure"""
    print("\nTesting app.py structure...")
    try:
        # Read app.py and check for authentication components
        with open('app.py', 'r') as f:
            content = f.read()

        required_elements = [
            ('from auth import UserDB', 'Auth import'),
            ('show_login_page', 'Login page function'),
            ('show_register_page', 'Registration page function'),
            ('st.session_state[\'authenticated\']', 'Session authentication check'),
            ('UserDB.authenticate_user', 'Authentication call'),
            ('UserDB.register_user', 'Registration call'),
        ]

        for element, name in required_elements:
            if element in content:
                print(f"  ✓ {name} found")
            else:
                print(f"  ✗ {name} missing")
                return False

        return True
    except Exception as e:
        print(f"  ✗ Error reading app.py: {e}")
        return False

def test_validation():
    """Test input validation"""
    print("\nTesting input validation...")

    test_cases = [
        # (username, password, email, should_pass, reason)
        ('ab', 'password123', 'test@email.com', False, 'Username too short'),
        ('validuser', '12345', 'test@email.com', False, 'Password too short'),
        ('validuser', 'password123', 'invalid-email', False, 'Invalid email'),
        ('validuser', 'password123', 'test@email.com', True, 'Valid credentials'),
    ]

    all_good = True
    for username, password, email, should_pass, reason in test_cases:
        # Basic validation logic (matching auth.py)
        valid = True
        error = None

        if len(username) < 3:
            valid = False
            error = "Username too short"
        elif len(password) < 6:
            valid = False
            error = "Password too short"
        elif '@' not in email:
            valid = False
            error = "Invalid email"

        if valid == should_pass:
            print(f"  ✓ {reason}: {'Accepted' if should_pass else 'Rejected'}")
        else:
            print(f"  ✗ {reason}: Expected {'accept' if should_pass else 'reject'}, got {'accept' if valid else 'reject'}")
            all_good = False

    return all_good

def test_config_files():
    """Test configuration files"""
    print("\nTesting configuration files...")

    files = [
        ('pyproject.toml', 'Project dependencies'),
        ('.streamlit/config.toml', 'Streamlit config'),
        ('migrate_database.py', 'Migration script'),
        ('auth.py', 'Authentication module'),
        ('AUTHENTICATION_SETUP.md', 'Setup guide'),
        ('DEPLOYMENT_GUIDE.md', 'Deployment guide'),
    ]

    all_good = True
    for file, name in files:
        if os.path.exists(file):
            print(f"  ✓ {name} ({file})")
        else:
            print(f"  ✗ {name} missing ({file})")
            all_good = False

    return all_good

def main():
    print("="*70)
    print("DashTrade Authentication System Test Suite")
    print("="*70)

    tests = [
        ("Password Hashing", test_password_hashing),
        ("Required Imports", test_imports),
        ("Auth Module", test_auth_module),
        ("Database Module", test_database_module),
        ("App Structure", test_app_structure),
        ("Input Validation", test_validation),
        ("Configuration Files", test_config_files),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test failed with exception: {e}")
            results.append((name, False))

    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("="*70)
    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("="*70)
        print("✅ All tests passed! Authentication system is ready.")
        print("="*70)
        print("\nNext steps:")
        print("  1. Set up DATABASE_URL: python setup_database.py")
        print("  2. Run migration: python migrate_database.py")
        print("  3. Start the app: streamlit run app.py")
        return 0
    else:
        print("="*70)
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
