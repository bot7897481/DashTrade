#!/usr/bin/env python3
"""
Railway Setup Helper Script
This script helps you verify that your DashTrade app is ready for Railway deployment.
"""

import os
import sys
import subprocess

def check_files():
    """Check if all required files exist"""
    required_files = [
        'Procfile',
        'requirements.txt',
        'Dockerfile',
        'finalize_setup.py',
        'app.py',
        'database.py',
        'auth.py'
    ]

    print("📁 Checking required files...")
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            missing.append(file)

    if missing:
        print(f"\n❌ Missing files: {', '.join(missing)}")
        return False

    print("✅ All required files present")
    return True

def check_procfile():
    """Check Procfile format"""
    print("\n📋 Checking Procfile...")
    try:
        with open('Procfile', 'r') as f:
            content = f.read().strip()

        lines = content.split('\n')
        expected_processes = ['web:', 'release:', 'bot:', 'alerts:', 'webhook:']

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if ':' not in line:
                print(f"  ❌ Invalid line: {line}")
                return False

            process_name = line.split(':')[0] + ':'
            if process_name in expected_processes:
                print(f"  ✅ {process_name.strip()}")
            else:
                print(f"  ⚠️  Unexpected process: {process_name.strip()}")

        print("✅ Procfile looks good")
        return True

    except Exception as e:
        print(f"❌ Error reading Procfile: {e}")
        return False

def check_requirements():
    """Check if key dependencies are in requirements.txt"""
    print("\n📦 Checking requirements.txt...")
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()

        required_deps = [
            'streamlit',
            'psycopg2-binary',
            'bcrypt',
            'python-dotenv',
            'yfinance',
            'plotly'
        ]

        missing_deps = []
        for dep in required_deps:
            if dep.lower() in content.lower():
                print(f"  ✅ {dep}")
            else:
                print(f"  ❌ {dep} - MISSING")
                missing_deps.append(dep)

        if missing_deps:
            print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
            return False

        print("✅ All key dependencies present")
        return True

    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def check_git_status():
    """Check git status and remote"""
    print("\n🔗 Checking Git configuration...")

    try:
        # Check if we're in a git repo
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Not a git repository")
            return False

        print("✅ Git repository detected")

        # Check remote
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if 'github.com' in result.stdout:
            print("✅ GitHub remote configured")
            # Extract repo URL
            for line in result.stdout.split('\n'):
                if 'origin' in line and 'github.com' in line:
                    url = line.split()[1]
                    print(f"  📍 Repository: {url}")
                    break
        else:
            print("⚠️  No GitHub remote found")
            print("  💡 Make sure to add your GitHub repository as origin")

        return True

    except Exception as e:
        print(f"❌ Error checking git: {e}")
        return False

def show_next_steps():
    """Show next steps for Railway deployment"""
    print("\n" + "="*70)
    print("🚀 NEXT STEPS FOR RAILWAY DEPLOYMENT")
    print("="*70)

    print("\n1. Push your code to GitHub:")
    print("   git add .")
    print("   git commit -m 'Ready for Railway deployment'")
    print("   git push origin main")

    print("\n2. Set up Railway project:")
    print("   • Go to https://railway.app")
    print("   • Click 'New Project'")
    print("   • Select 'Deploy from GitHub repo'")
    print("   • Choose your DashTrade repository")

    print("\n3. Add PostgreSQL database:")
    print("   • In Railway: '+ Add Service' → 'Database' → 'PostgreSQL'")
    print("   • Railway will automatically set DATABASE_URL")

    print("\n4. Deploy and access:")
    print("   • Railway will auto-deploy on push")
    print("   • Get your app URL from Railway dashboard")
    print("   • Default admin: admin / admin123! (change immediately!)")

    print("\n5. Verify deployment:")
    print("   • Check Railway logs for any errors")
    print("   • Test login with admin credentials")

    print("\n📖 Full guide: See RAILWAY_DEPLOYMENT.md")

def main():
    print("="*70)
    print("       DashTrade Railway Setup Checker")
    print("="*70)

    all_good = True

    # Run all checks
    checks = [
        check_files,
        check_procfile,
        check_requirements,
        check_git_status
    ]

    for check in checks:
        if not check():
            all_good = False

    if all_good:
        print("\n🎉 ALL CHECKS PASSED!")
        print("Your DashTrade app is ready for Railway deployment!")
    else:
        print("\n❌ SOME CHECKS FAILED")
        print("Please fix the issues above before deploying to Railway.")

    show_next_steps()

if __name__ == "__main__":
    main()
