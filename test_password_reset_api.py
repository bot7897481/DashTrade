#!/usr/bin/env python3
"""
Test script to verify password reset API endpoints are working
"""
import requests
import json
import sys
import os

# Get API URL from environment or use default
API_URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('API_URL', 'http://localhost:8081')

def test_forgot_password(email):
    """Test forgot password endpoint"""
    print(f"\n{'='*60}")
    print("Testing: POST /api/auth/forgot-password")
    print(f"{'='*60}")
    
    url = f"{API_URL}/api/auth/forgot-password"
    payload = {"email": email}
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Forgot password request sent")
            return True
        else:
            print(f"\n❌ FAILED: Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {API_URL}")
        print("   Make sure the API server is running")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def test_reset_password(token, new_password):
    """Test reset password endpoint"""
    print(f"\n{'='*60}")
    print("Testing: POST /api/auth/reset-password")
    print(f"{'='*60}")
    
    url = f"{API_URL}/api/auth/reset-password"
    payload = {
        "token": token,
        "new_password": new_password
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps({**payload, 'token': token[:20] + '...'}, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Password reset successful")
            return True
        else:
            print(f"\n❌ FAILED: Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {API_URL}")
        print("   Make sure the API server is running")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def test_health():
    """Test health endpoint"""
    print(f"\n{'='*60}")
    print("Testing: GET /health")
    print(f"{'='*60}")
    
    url = f"{API_URL}/health"
    
    try:
        response = requests.get(url)
        print(f"URL: {url}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: API server is healthy")
            return True
        else:
            print(f"\n❌ FAILED: Status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {API_URL}")
        print("   Make sure the API server is running")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    import os
    
    print("="*60)
    print("PASSWORD RESET API TEST")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Note: Set API_URL environment variable or pass as argument")
    print("="*60)
    
    # Test health first
    if not test_health():
        print("\n❌ API server is not accessible. Please check:")
        print("   1. Is the API server running on Railway?")
        print("   2. Is the API_URL correct?")
        print("   3. Check Railway deployment logs")
        sys.exit(1)
    
    # Test forgot password
    test_email = input("\nEnter email to test forgot password (or press Enter to skip): ").strip()
    if test_email:
        test_forgot_password(test_email)
    
    # Test reset password
    test_token = input("\nEnter reset token to test reset password (or press Enter to skip): ").strip()
    if test_token:
        test_password = input("Enter new password: ").strip()
        if test_password:
            test_reset_password(test_token, test_password)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

