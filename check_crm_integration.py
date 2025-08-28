#!/usr/bin/env python3
"""
CRM Integration Check Script

This script checks if the CRM system (deployed on Render) is sending data to the Reporting API.
It examines:
1. Database for CRM-related test runs
2. API logs for incoming requests
3. Network connectivity between CRM and Reporting
"""

import requests
import json
from datetime import datetime, timedelta
from database_postgresql import db

def check_database_for_crm_data():
    """Check database for CRM-related test runs"""
    print("🔍 Checking Database for CRM Data")
    print("=" * 50)
    
    try:
        # Get all test runs
        test_runs = db.get_all_test_runs()
        
        print(f"Total test runs in database: {len(test_runs)}")
        
        # Filter for CRM-related data
        crm_runs = []
        other_runs = []
        
        for run in test_runs:
            source_system = run.get('source_system', '').lower()
            if 'crm' in source_system or 'ui navigator' in source_system:
                crm_runs.append(run)
            else:
                other_runs.append(run)
        
        print(f"\n📊 CRM-Related Test Runs: {len(crm_runs)}")
        print(f"📊 Other Test Runs: {len(other_runs)}")
        
        if crm_runs:
            print("\n🔍 Recent CRM Test Runs:")
            for run in crm_runs[:10]:  # Show last 10
                print(f"  - Test Run ID: {run.get('test_run_id', 'N/A')}")
                print(f"    Customer ID: {run.get('customer_id', 'N/A')}")
                print(f"    Source System: {run.get('source_system', 'N/A')}")
                print(f"    Test Case: {run.get('test_case_id', 'N/A')}")
                print(f"    Result: {run.get('result', 'N/A')}")
                print(f"    Executed By: {run.get('executed_by', 'N/A')}")
                print(f"    Date: {run.get('execution_date', 'N/A')}")
                print("    " + "-" * 40)
        else:
            print("\n❌ No CRM-related test runs found in database")
        
        # Check for specific CRM patterns
        print("\n🔍 Looking for CRM-specific patterns:")
        crm_patterns = ['CRM', 'crm', 'customer', 'transit', 'card']
        for run in test_runs:
            for pattern in crm_patterns:
                if pattern in str(run).lower():
                    print(f"  Found pattern '{pattern}' in test run: {run.get('test_run_id', 'N/A')}")
                    break
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def check_api_endpoints():
    """Check if API endpoints are accessible"""
    print("\n🌐 Checking API Endpoints")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    endpoints = [
        "/api/health",
        "/api/v1/results/test-runs",
        "/api/v1/results/customers/12345/test-runs"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"✅ {endpoint}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if 'testRuns' in data:
                    print(f"   - Test runs count: {len(data.get('testRuns', []))}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def check_crm_render_url():
    """Check if CRM Render URL is accessible"""
    print("\n🌐 Checking CRM Render URL")
    print("=" * 50)
    
    # You'll need to replace this with your actual CRM Render URL
    crm_urls = [
        "https://your-crm-app.onrender.com",  # Replace with actual URL
        "https://crm-transit.onrender.com",   # Example
        "https://transit-crm.onrender.com"    # Example
    ]
    
    for url in crm_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {url}: Not accessible - {e}")

def check_network_connectivity():
    """Check network connectivity between systems"""
    print("\n🌐 Checking Network Connectivity")
    print("=" * 50)
    
    # Test if Reporting API can be reached from external
    try:
        # Test local API
        local_response = requests.get("http://127.0.0.1:5000/api/health")
        print(f"✅ Local API (127.0.0.1:5000): {local_response.status_code}")
        
        # Test if API is accessible from external (if deployed)
        # You'll need to replace with your actual Reporting API URL
        external_urls = [
            "https://your-reporting-api.onrender.com",  # Replace with actual URL
            "https://reporting-transit.onrender.com"    # Example
        ]
        
        for url in external_urls:
            try:
                response = requests.get(f"{url}/api/health", timeout=10)
                print(f"✅ External API ({url}): {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ External API ({url}): Not accessible - {e}")
                
    except Exception as e:
        print(f"❌ Error checking connectivity: {e}")

def check_recent_activity():
    """Check for recent activity in the last 24 hours"""
    print("\n⏰ Checking Recent Activity (Last 24 Hours)")
    print("=" * 50)
    
    try:
        test_runs = db.get_all_test_runs()
        
        # Filter for recent activity (last 24 hours)
        recent_runs = []
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for run in test_runs:
            execution_date = run.get('execution_date')
            if execution_date:
                try:
                    # Parse the execution date
                    if 'T' in execution_date:
                        run_time = datetime.fromisoformat(execution_date.replace('Z', '+00:00'))
                    else:
                        run_time = datetime.strptime(execution_date, '%Y-%m-%d %H:%M:%S')
                    
                    if run_time > cutoff_time:
                        recent_runs.append(run)
                except:
                    pass  # Skip if date parsing fails
        
        print(f"Recent test runs (last 24h): {len(recent_runs)}")
        
        if recent_runs:
            print("\n📊 Recent Activity:")
            for run in recent_runs[:5]:  # Show last 5
                print(f"  - {run.get('test_run_id', 'N/A')} | {run.get('source_system', 'N/A')} | {run.get('execution_date', 'N/A')}")
        else:
            print("❌ No recent activity found")
            
    except Exception as e:
        print(f"❌ Error checking recent activity: {e}")

def check_crm_integration_config():
    """Check CRM integration configuration"""
    print("\n⚙️ Checking CRM Integration Configuration")
    print("=" * 50)
    
    # Check if there are any CRM-specific environment variables or config
    import os
    
    crm_related_env_vars = [
        'CRM_API_URL',
        'CRM_WEBHOOK_URL',
        'CRM_INTEGRATION_KEY',
        'REPORTING_API_URL'
    ]
    
    print("Environment Variables:")
    for var in crm_related_env_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value[:20]}..." if len(value) > 20 else f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # Check for CRM integration files
    crm_files = [
        'crm_integration.py',
        'reporting_integration.py',
        'webhook_handler.py'
    ]
    
    print("\nCRM Integration Files:")
    for file in crm_files:
        if os.path.exists(file):
            print(f"  ✅ {file}: Found")
        else:
            print(f"  ❌ {file}: Not found")

def main():
    """Run all CRM integration checks"""
    print("🚀 CRM Integration Check")
    print("=" * 60)
    
    # Check if Reporting API is running
    try:
        response = requests.get("http://127.0.0.1:5000/api/health")
        if response.status_code != 200:
            print("❌ Reporting API is not running. Please start it first.")
            return
        print("✅ Reporting API is running")
    except Exception as e:
        print(f"❌ Cannot connect to Reporting API: {e}")
        print("Please start the Flask server with: python dbapi.py")
        return
    
    # Run all checks
    check_database_for_crm_data()
    check_api_endpoints()
    check_crm_render_url()
    check_network_connectivity()
    check_recent_activity()
    check_crm_integration_config()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("To verify CRM integration:")
    print("1. Check if CRM test runs appear in the database")
    print("2. Verify CRM Render URL is accessible")
    print("3. Ensure network connectivity between CRM and Reporting")
    print("4. Check for recent activity from CRM system")
    print("5. Verify CRM integration configuration")

if __name__ == "__main__":
    main()
