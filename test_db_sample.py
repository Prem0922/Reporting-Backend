#!/usr/bin/env python3
"""
Simple database test for Reporting Backend
This script tests the database connection like the CRM does
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database():
    """Test database connection and table creation"""
    print("🔍 Testing database connection...")
    
    try:
        from database_postgresql import engine, Base
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
        
        # Test table creation
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # List tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_creation():
    """Test user creation"""
    print("🔍 Testing user creation...")
    
    try:
        from database_postgresql import db
        
        # Test user data
        test_user = {
            'username': 'test_user',
            'password': 'test_password_hash',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '1234567890',
            'country_code': '+1'
        }
        
        # Try to create user
        success = db.create_user(test_user)
        
        if success:
            print("✅ User creation successful")
            
            # Clean up
            try:
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text("DELETE FROM users WHERE username = 'test_user'"))
                    conn.commit()
                print("✅ Test user cleaned up")
            except:
                pass
                
            return True
        else:
            print("❌ User creation failed")
            return False
            
    except Exception as e:
        print(f"❌ User creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Reporting Database (CRM-style)...")
    print("=" * 50)
    
    # Test database connection
    db_success = test_database()
    
    if db_success:
        # Test user creation
        user_success = test_user_creation()
        
        if user_success:
            print("\n🎉 All tests passed! Database is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ User creation test failed.")
            sys.exit(1)
    else:
        print("\n❌ Database connection test failed.")
        sys.exit(1)
