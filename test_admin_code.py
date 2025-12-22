#!/usr/bin/env python3
"""
Test Admin Code Validation
This script helps debug admin code issues.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_admin_code():
    """Test admin code validation"""
    print("="*70)
    print("🔍 Admin Code Validation Test")
    print("="*70)
    
    from auth import UserDB
    
    # Check environment variable
    admin_code_env = os.getenv('ADMIN_CODE', '')
    print(f"\n📋 Environment Variable:")
    print(f"   ADMIN_CODE: {admin_code_env if admin_code_env else '(not set)'}")
    
    # Test codes
    test_codes = [
        '1234-5678-9012-3456',  # Default code
        '1234567890123456',     # Default code without dashes
        '1234-5678-9012-3939',  # User's Railway code
        '1234567890123939',     # User's Railway code without dashes
        'invalid',              # Invalid code
        '',                     # Empty
    ]
    
    print(f"\n🧪 Testing Codes:")
    print("-" * 70)
    
    for code in test_codes:
        if code:
            result = UserDB.validate_admin_code(code)
            status = "✅ VALID" if result else "❌ INVALID"
            print(f"{status}: {code}")
        else:
            result = UserDB.validate_admin_code(None)
            status = "✅ VALID" if result else "❌ INVALID"
            print(f"{status}: (empty)")
    
    print("\n" + "="*70)
    print("💡 Tips:")
    print("   1. If ADMIN_CODE is set in Railway, use that exact code")
    print("   2. If ADMIN_CODE is NOT set, use default: 1234-5678-9012-3456")
    print("   3. Codes work with or without dashes")
    print("   4. Make sure ADMIN_CODE in Railway matches what you're entering")
    print("="*70)

if __name__ == "__main__":
    test_admin_code()

