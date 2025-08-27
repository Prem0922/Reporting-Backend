#!/usr/bin/env python3
"""
Check Deployed Systems Integration

This script checks the actual deployed CRM and POS systems on Render
and verifies their integration with the Reporting API.
"""

import requests
import json
from datetime import datetime

# Actual deployed URLs from your Render dashboard
CRM_URL = "https://crm-n577.onrender.com"  # CRM Backend
POS_URL = "https://pos-b0w3.onrender.com"  # POS Frontend
CRM_FRONTEND_URL = "https://crm-frontend-86aq.onrender.com"  # CRM Frontend
POS_BACKEND_URL = "https://pos-backend-820t.onrender.com"  # POS Backend
REPORTING_API_URL = "http://127.0.0.1:5000"  # Your local Reporting API

def check_crm_system():
    """Check if CRM systems are accessible and working"""
    print("🔍 Checking Deployed CRM Systems")
    print("=" * 50)
    
    # Check CRM Frontend
    try:
        response = requests.get(f"{CRM_FRONTEND_URL}", timeout=10)
        print(f"✅ CRM Frontend ({CRM_FRONTEND_URL}): {response.status_code}")
    except Exception as e:
        print(f"❌ CRM Frontend Error: {e}")
    
    # Check CRM Backend
    try:
        # Check CRM health endpoint
        response = requests.get(f"{CRM_URL}/health", timeout=10)
        print(f"✅ CRM Backend Health ({CRM_URL}): {response.status_code}")
        
        # Check CRM API endpoints
        crm_endpoints = [
            "/api/customers",
            "/api/cards", 
            "/api/trips",
            "/api/cases"
        ]
        
        for endpoint in crm_endpoints:
            try:
                response = requests.get(f"{CRM_URL}{endpoint}", timeout=10)
                print(f"✅ CRM Backend {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"❌ CRM Backend {endpoint}: Error - {e}")
                
    except Exception as e:
        print(f"❌ CRM Backend System Error: {e}")

def check_pos_system():
    """Check if POS systems are accessible and working"""
    print("\n🔍 Checking Deployed POS Systems")
    print("=" * 50)
    
    # Check POS Frontend
    try:
        response = requests.get(f"{POS_URL}", timeout=10)
        print(f"✅ POS Frontend ({POS_URL}): {response.status_code}")
    except Exception as e:
        print(f"❌ POS Frontend Error: {e}")
    
    # Check POS Backend
    try:
        response = requests.get(f"{POS_BACKEND_URL}/health", timeout=10)
        print(f"✅ POS Backend Health ({POS_BACKEND_URL}): {response.status_code}")
        
        # Check POS Backend API endpoints
        pos_endpoints = [
            "/api/transactions",
            "/api/cards",
            "/api/taps"
        ]
        
        for endpoint in pos_endpoints:
            try:
                response = requests.get(f"{POS_BACKEND_URL}{endpoint}", timeout=10)
                print(f"✅ POS Backend {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"❌ POS Backend {endpoint}: Error - {e}")
                
    except Exception as e:
        print(f"❌ POS Backend System Error: {e}")

def check_reporting_api():
    """Check if Reporting API is accessible"""
    print("\n🔍 Checking Reporting API")
    print("=" * 50)
    
    try:
        response = requests.get(f"{REPORTING_API_URL}/api/health", timeout=10)
        print(f"✅ Reporting API Health: {response.status_code}")
        
        # Check test runs endpoint
        response = requests.get(f"{REPORTING_API_URL}/api/v1/results/test-runs", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Reporting API Test Runs: {len(data.get('testRuns', []))} runs")
        else:
            print(f"❌ Reporting API Test Runs: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Reporting API Error: {e}")

def test_crm_to_reporting_integration():
    """Test if CRM can send data to Reporting API"""
    print("\n🔍 Testing CRM to Reporting Integration")
    print("=" * 50)
    
    # Simulate what the real CRM would send
    test_payload = {
        "customerId": 9999,
        "testRunId": f"CRM_REAL_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "sourceSystem": "CRM",
        "events": [
            {
                "kind": "TEST_RUN",
                "testCase": {
                    "id": "CRM_REAL_CUSTOMER_CREATE_9999",
                    "title": "Real CRM Customer Creation Test",
                    "component": "CRM System"
                },
                "result": "Pass",
                "executedBy": "CRM System",
                "executionDate": datetime.now().isoformat(),
                "observedTimeMs": 500,
                "remarks": "Real CRM integration test"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{REPORTING_API_URL}/api/v1/results/test-runs",
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ CRM to Reporting Integration: {data.get('accepted', 0)} events accepted")
            return True
        else:
            print(f"❌ CRM to Reporting Integration Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CRM to Reporting Integration Error: {e}")
        return False

def check_crm_configuration():
    """Check CRM configuration for Reporting API integration"""
    print("\n🔍 Checking CRM Configuration")
    print("=" * 50)
    
    try:
        # Try to access CRM configuration or environment
        response = requests.get(f"{CRM_URL}/api/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print("✅ CRM Configuration accessible")
            if 'reporting_api_url' in config:
                print(f"   Reporting API URL: {config['reporting_api_url']}")
            else:
                print("   ❌ No Reporting API URL configured")
        else:
            print(f"❌ Cannot access CRM configuration: {response.status_code}")
            
    except Exception as e:
        print(f"❌ CRM Configuration Error: {e}")

def check_recent_crm_activity():
    """Check for recent CRM activity in Reporting API"""
    print("\n🔍 Checking Recent CRM Activity")
    print("=" * 50)
    
    try:
        response = requests.get(f"{REPORTING_API_URL}/api/v1/results/test-runs")
        if response.status_code == 200:
            data = response.json()
            test_runs = data.get('testRuns', [])
            
            # Filter for CRM data from the last hour
            recent_crm_runs = []
            for run in test_runs:
                if run.get('source_system', '').lower() == 'crm':
                    recent_crm_runs.append(run)
            
            print(f"Total CRM test runs: {len(recent_crm_runs)}")
            
            if recent_crm_runs:
                print("\n📊 Recent CRM Activity:")
                for run in recent_crm_runs[:5]:
                    print(f"  - {run.get('test_run_id', 'N/A')} | {run.get('test_case_id', 'N/A')} | {run.get('result', 'N/A')}")
            else:
                print("❌ No recent CRM activity found")
                
    except Exception as e:
        print(f"❌ Error checking CRM activity: {e}")

def main():
    """Run all deployment checks"""
    print("🚀 Deployed Systems Integration Check")
    print("=" * 60)
    
    # Check all systems
    check_crm_system()
    check_pos_system()
    check_reporting_api()
    check_crm_configuration()
    test_crm_to_reporting_integration()
    check_recent_crm_activity()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("CRM Backend: https://crm-n577.onrender.com")
    print("CRM Frontend: https://crm-frontend-86aq.onrender.com")
    print("POS Backend: https://pos-backend-820t.onrender.com")
    print("POS Frontend: https://pos-b0w3.onrender.com")
    print("Reporting API: http://127.0.0.1:5000 (Local)")
    print("\nTo enable real CRM integration:")
    print("1. Deploy Reporting API to Render")
    print("2. Update CRM Backend configuration to use deployed Reporting API URL")
    print("3. Verify CRM is sending real data")

if __name__ == "__main__":
    main()
