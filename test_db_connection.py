#!/usr/bin/env python3
"""
Test script to verify database connection and basic operations
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

def test_imports():
    """Test if all required modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        import flask
        print("✅ Flask imported successfully")
        
        import flask_cors
        print("✅ Flask-CORS imported successfully")
        
        import flask_swagger_ui
        print("✅ Flask-Swagger-UI imported successfully")
        
        # Test database imports
        import psycopg
        print("✅ psycopg3 imported successfully")
        
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
        
        # Test our database module
        from database_postgresql import db
        print("✅ Database module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        print("\nTesting database connection...")
        
        from database_postgresql import db
        
        # Test if we can get a session
        session = db.get_session()
        print("✅ Database session created successfully")
        
        # Test a simple query
        result = session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        print(f"✅ Database query executed successfully: {row}")
        
        session.close()
        print("✅ Database session closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Main test function"""
    print("=== Database Connection Test ===")
    print(f"Python version: {sys.version}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
    
    # Test imports
    if not test_imports():
        print("❌ Import tests failed")
        return False
    
    # Test database connection
    if not test_database_connection():
        print("❌ Database connection test failed")
        return False
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
