#!/usr/bin/env python3
"""
PostgreSQL Setup Script for Reporting Application
This script helps set up PostgreSQL database for local development
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2 import OperationalError

def check_postgresql_installed():
    """Check if PostgreSQL is installed"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL is installed")
            print(f"   Version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ PostgreSQL is not installed or not in PATH")
    return False

def check_postgresql_connection():
    """Check if we can connect to PostgreSQL server"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="postgres",
            password="password"
        )
        conn.close()
        print("✅ Successfully connected to PostgreSQL server")
        return True
    except OperationalError as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check if the default password is 'password'")
        print("3. Verify PostgreSQL is listening on port 5432")
        return False

def check_postgresql_version():
    """Check PostgreSQL version"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="postgres",
            password="password"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"   PostgreSQL version: {version[0]}")
        return True
    except Exception as e:
        print(f"❌ Error checking version: {e}")
        return False

def create_database():
    """Create the reporting database"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="postgres",
            password="password"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='reporting_db'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE reporting_db")
            print("✅ Created database 'reporting_db'")
        else:
            print("✅ Database 'reporting_db' already exists")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def create_env_file():
    """Create .env file with PostgreSQL configuration"""
    env_content = """# PostgreSQL Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/reporting_db

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_here_change_in_production

# Email Configuration (for password reset)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_password
RESET_LINK_BASE=http://localhost:3000/reset-password

# Twilio Configuration (optional)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# JSONBin API Key (optional)
JSONBIN_API_KEY=your_jsonbin_api_key
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with PostgreSQL configuration")
        print("   Please update the values in .env file as needed")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    print("🚀 PostgreSQL Setup for Reporting Application")
    print("=" * 50)
    
    # Check if PostgreSQL is installed
    if not check_postgresql_installed():
        print("\n📥 To install PostgreSQL:")
        print("1. Download from: https://www.postgresql.org/download/")
        print("2. Install with default settings")
        print("3. Set password as 'password' during installation")
        print("4. Add PostgreSQL to your PATH")
        print("\nAfter installation, run this script again.")
        return
    
    # Check connection
    if not check_postgresql_connection():
        print("\n🔧 To fix connection issues:")
        print("1. Start PostgreSQL service")
        print("2. Check if password is 'password'")
        print("3. Verify port 5432 is not blocked")
        return
    
    # Check version
    check_postgresql_version()
    
    # Create database
    if not create_database():
        return
    
    # Create .env file
    if not create_env_file():
        return
    
    print("\n🎉 PostgreSQL setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update the .env file with your actual values")
    print("2. Run: python create_db.py")
    print("3. Run: python pscript.py")
    print("4. Run: python start_backends.py")
    print("5. In another terminal: cd test-dashboard-ui && npm start")

if __name__ == "__main__":
    main()
