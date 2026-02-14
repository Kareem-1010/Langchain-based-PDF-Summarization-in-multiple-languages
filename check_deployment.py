#!/usr/bin/env python3
"""
Pre-deployment verification script
Checks if everything is ready for deployment to Render
"""

import os
import sys

def check_file_exists(filename, description):
    """Check if a required file exists"""
    if os.path.exists(filename):
        print(f"✓ {description}: {filename}")
        return True
    else:
        print(f"✗ {description} MISSING: {filename}")
        return False

def check_env_var(var_name):
    """Check if environment variable exists"""
    value = os.getenv(var_name)
    if value and value != f"your_{var_name.lower()}_here":
        print(f"✓ {var_name} is set")
        return True
    else:
        print(f"✗ {var_name} NOT SET or using placeholder")
        return False

def check_gitignore():
    """Check if .env is in .gitignore"""
    try:
        with open('.gitignore', 'r') as f:
            content = f.read()
            if '.env' in content:
                print("✓ .env is in .gitignore (secure)")
                return True
            else:
                print("✗ .env NOT in .gitignore (SECURITY RISK!)")
                return False
    except FileNotFoundError:
        print("✗ .gitignore file missing")
        return False

def check_database_url():
    """Check if DATABASE_URL is properly formatted"""
    url = os.getenv('DATABASE_URL', '')
    if 'railway.internal' in url:
        print("✗ DATABASE_URL uses internal Railway URL (won't work from Render)")
        print("  → Use the PUBLIC Railway URL instead")
        return False
    elif url.startswith('postgresql://') or url.startswith('postgres://'):
        print("✓ DATABASE_URL looks valid")
        return True
    else:
        print("✗ DATABASE_URL doesn't look like a PostgreSQL URL")
        return False

def main():
    print("="*70)
    print("🚀 Pre-Deployment Verification for Render + Railway")
    print("="*70 + "\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    all_checks_passed = True
    
    print("📁 Checking Required Files:")
    print("-" * 70)
    all_checks_passed &= check_file_exists('requirements.txt', 'Dependencies file')
    all_checks_passed &= check_file_exists('app.py', 'Main application')
    all_checks_passed &= check_file_exists('models.py', 'Database models')
    all_checks_passed &= check_file_exists('config.py', 'Configuration')
    all_checks_passed &= check_file_exists('build.sh', 'Build script')
    all_checks_passed &= check_file_exists('Procfile', 'Process file')
    all_checks_passed &= check_file_exists('render.yaml', 'Render config')
    all_checks_passed &= check_file_exists('.gitignore', 'Git ignore file')
    
    print("\n🔐 Checking Environment Variables:")
    print("-" * 70)
    all_checks_passed &= check_env_var('DATABASE_URL')
    all_checks_passed &= check_database_url()
    all_checks_passed &= check_env_var('SECRET_KEY')
    all_checks_passed &= check_env_var('ENCRYPTION_KEY')
    
    print("\n🔒 Checking Security:")
    print("-" * 70)
    all_checks_passed &= check_gitignore()
    
    print("\n📦 Checking Python Imports:")
    print("-" * 70)
    try:
        import flask
        print(f"✓ Flask {flask.__version__}")
    except ImportError:
        print("✗ Flask not installed")
        all_checks_passed = False
    
    try:
        import psycopg2
        print("✓ psycopg2 (PostgreSQL driver)")
    except ImportError:
        print("✗ psycopg2 not installed")
        all_checks_passed = False
    
    try:
        import langchain
        print("✓ LangChain")
    except ImportError:
        print("✗ LangChain not installed")
        all_checks_passed = False
    
    try:
        import sentence_transformers
        print("✓ sentence-transformers")
    except ImportError:
        print("✗ sentence-transformers not installed")
        all_checks_passed = False
    
    try:
        import gunicorn
        print("✓ Gunicorn (production server)")
    except ImportError:
        print("✗ Gunicorn not installed (needed for production)")
        all_checks_passed = False
    
    print("\n" + "="*70)
    
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED! You're ready to deploy!")
        print("\n📚 Next Steps:")
        print("1. Push to GitHub: git push origin main")
        print("2. Go to Render Dashboard: https://dashboard.render.com")
        print("3. Create New Web Service")
        print("4. Connect your repository")
        print("5. Set environment variables")
        print("6. Deploy!")
        print("\n📖 See DEPLOYMENT.md for detailed instructions")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print("\n🔧 Fix the issues above before deploying.")
        print("📖 See DEPLOYMENT.md for detailed instructions")
        return 1

if __name__ == '__main__':
    sys.exit(main())
