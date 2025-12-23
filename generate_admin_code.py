#!/usr/bin/env python3
"""
Generate Admin Activation Code
This script generates a secure 16-digit admin code for your dashboard.
"""
import secrets
import os

def generate_admin_code():
    """Generate a secure 16-digit admin code"""
    # Generate 16 random digits
    code = ''.join([str(secrets.randbelow(10)) for _ in range(16)])
    
    # Format with dashes for readability
    formatted_code = f"{code[:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"
    
    return code, formatted_code

if __name__ == "__main__":
    print("="*70)
    print("🔑 Admin Activation Code Generator")
    print("="*70)
    
    code, formatted_code = generate_admin_code()
    
    print(f"\n✅ Generated Admin Code:")
    print(f"   {formatted_code}")
    print(f"\n📋 To use this code:")
    print(f"   1. Copy the code above")
    print(f"   2. Go to Railway → Your Project → Variables")
    print(f"   3. Add new variable:")
    print(f"      Name: ADMIN_CODE")
    print(f"      Value: {code}")
    print(f"   4. Users can enter this code during registration to become admin")
    print(f"\n💡 Default code (if ADMIN_CODE not set): 1234-5678-9012-3456")
    print("="*70)


