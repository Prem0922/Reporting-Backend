#!/usr/bin/env python3
"""
Complete setup test for Reporting Backend
This script tests all components to ensure everything works
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
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
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_user_creation():
    """Test user creation functionality"""
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
            
            # Clean up - delete test user
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
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("🔍 Testing API endpoints...")
    
    base_url = "https://reporting-backend-kpoz.onrender.com"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            data = response.json()
            print(f"   Database status: {data.get('database_status', 'unknown')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False
    
    # Test docs endpoint
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Docs endpoint working")
        else:
            print(f"❌ Docs endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Docs endpoint test failed: {e}")
    
    return True

def test_frontend_connection():
    """Test frontend connection to backend"""
    print("🔍 Testing frontend-backend connection...")
    
    frontend_url = "https://reporting-frontend-bhrm.onrender.com"
    backend_url = "https://reporting-backend-kpoz.onrender.com"
    
    try:
        # Test if frontend is accessible
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False
    
    try:
        # Test if backend is accessible from frontend perspective
        response = requests.get(f"{backend_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is accessible from frontend")
        else:
            print(f"❌ Backend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend accessibility test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive setup test...")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("User Creation", test_user_creation),
        ("API Endpoints", test_api_endpoints),
        ("Frontend Connection", test_frontend_connection)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
