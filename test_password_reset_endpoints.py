#!/usr/bin/env python3
"""
Test password reset endpoints on Railway
"""
import requests
import json

API_URL = "https://overflowing-spontaneity-production.up.railway.app"

def test_forgot_password(email):
    """Test forgot password endpoint"""
    print(f"\n{'='*70}")
    print("TESTING: POST /api/auth/forgot-password")
    print(f"{'='*70}")
    
    url = f"{API_URL}/api/auth/forgot-password"
    payload = {"email": email}
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post(
            url, 
            json=payload, 
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"Response Body: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Body (raw): {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Request accepted")
            if data.get('success'):
                print("   ✅ Password reset email should be sent")
            else:
                print("   ⚠️  Response indicates failure")
            return True
        else:
            print(f"\n❌ FAILED: Status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Request timed out (>10 seconds)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERROR: Connection failed - {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reset_password(token, new_password):
    """Test reset password endpoint"""
    print(f"\n{'='*70}")
    print("TESTING: POST /api/auth/reset-password")
    print(f"{'='*70}")
    
    url = f"{API_URL}/api/auth/reset-password"
    payload = {
        "token": token,
        "new_password": new_password
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps({**payload, 'token': token[:20] + '...' if len(token) > 20 else token}, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post(
            url, 
            json=payload, 
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response Body: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Body (raw): {response.text}")
        
        if response.status_code == 200 and data.get('success'):
            print("\n✅ SUCCESS: Password reset successful")
            return True
        else:
            print(f"\n❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health():
    """Test health endpoint"""
    print(f"\n{'='*70}")
    print("TESTING: GET /health")
    print(f"{'='*70}")
    
    url = f"{API_URL}/health"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"URL: {url}")
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response (raw): {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: API server is healthy")
            return True
        else:
            print(f"\n❌ FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("PASSWORD RESET ENDPOINT TEST")
    print("="*70)
    print(f"API URL: {API_URL}")
    print("="*70)
    
    # Test health first
    health_ok = test_health()
    
    if not health_ok:
        print("\n❌ API server health check failed. Stopping tests.")
        exit(1)
    
    # Test forgot password
    print("\n" + "="*70)
    print("FORGOT PASSWORD TEST")
    print("="*70)
    email = input("Enter email address to test (or press Enter to skip): ").strip()
    
    if email:
        test_forgot_password(email)
        print("\n" + "="*70)
        print("NOTE: Check your email for the reset link")
        print("      Check Railway logs for email sending status")
        print("="*70)
    
    # Test reset password
    print("\n" + "="*70)
    print("RESET PASSWORD TEST")
    print("="*70)
    token = input("Enter reset token from email (or press Enter to skip): ").strip()
    
    if token:
        new_password = input("Enter new password (min 6 chars): ").strip()
        if new_password and len(new_password) >= 6:
            test_reset_password(token, new_password)
        else:
            print("❌ Password must be at least 6 characters")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Check Railway logs for email sending status")
    print("2. Check your email inbox (and spam folder)")
    print("3. Verify SMTP credentials are set in Railway")
    print("="*70)

