# dbapi.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import datetime
import traceback
import os
import json
from dotenv import load_dotenv
import uuid
import requests
import bcrypt
import jwt
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import datetime
from werkzeug.utils import secure_filename
import base64

# Import SQLAlchemy text for queries
from sqlalchemy import text

# Lazy database import to avoid startup issues
def get_db():
    """Get database instance with lazy initialization"""
    from database_postgresql import db
    return db

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://reporting-frontend-bhrm.onrender.com", "http://localhost:3000", "http://localhost:3001"], supports_credentials=True)

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

# Add /docs endpoint for easier access (like FastAPI)
DOCS_URL = '/docs'
DOCS_API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Reporting Application API"
    }
)

docs_blueprint = get_swaggerui_blueprint(
    DOCS_URL,
    DOCS_API_URL,
    config={
        'app_name': "Reporting Application API"
    }
)

# Register blueprints with unique names
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL, name='api_swagger')
app.register_blueprint(docs_blueprint, url_prefix=DOCS_URL, name='docs_swagger')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        from database_postgresql import get_engine
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        
        return jsonify({
            "status": "healthy",
            "message": "Backend is running and database is connected",
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "unhealthy",
            "message": f"Backend error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

# Basic startup test endpoint
@app.route('/api/startup', methods=['GET'])
def startup_test():
    """Basic startup test - no database required"""
    return jsonify({
        "status": "success",
        "message": "Flask app is running",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

# Test database endpoint
@app.route('/api/test-db', methods=['GET'])
def test_database():
    """Test database connection and user creation"""
    try:
        # Test basic connection
        from database_postgresql import get_engine
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Test user creation
        test_user = {
            'username': 'test_user_' + str(int(datetime.datetime.now().timestamp())),
            'password': 'test_password',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        success = create_user(test_user)
        
        return jsonify({
            "status": "success",
            "database_connection": "working",
            "user_creation": "working" if success else "failed",
            "message": "Database test completed"
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Database test failed: {str(e)}"
        }), 500

# Swagger JSON endpoint
@app.route('/static/swagger.json')
def create_swagger_spec():
    """Generate Swagger specification"""
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Reporting Application API",
            "description": "REST API for Transit Management System Test Dashboard",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@transit.com"
            }
        },
        "servers": [
            {
                "url": "https://reporting-backend-kpoz.onrender.com",
                "description": "Production server"
            },
            {
                "url": "http://localhost:5000",
                "description": "Development server"
            }
        ],
        "paths": {
            "/api/v1/results/test-runs": {
                "post": {
                    "summary": "Comprehensive Test Results API",
                    "description": "Process various types of test data including test runs, requirements, test cases, defects, test type summary, and transit metrics",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TestResultsRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Test results processed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TestResultsResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        },
                        "500": {
                            "description": "Internal server error"
                        }
                    }
                }
            },
            "/api/v1/requirements": {
                "get": {
                    "summary": "Get all requirements",
                    "description": "Retrieve all requirements from the database",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/Requirement"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create new requirement",
                    "description": "Create a new requirement in the database",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/RequirementRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Requirement created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Requirement"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        }
                    }
                }
            },
            "/api/v1/requirements/{requirement_id}": {
                "get": {
                    "summary": "Get requirement by ID",
                    "description": "Retrieve a specific requirement by its ID",
                    "parameters": [
                        {
                            "name": "requirement_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The requirement ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Requirement"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Requirement not found"
                        }
                    }
                }
            },
            "/api/v1/test-cases": {
                "get": {
                    "summary": "Get all test cases",
                    "description": "Retrieve all test cases from the database",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/TestCase"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create new test case",
                    "description": "Create a new test case in the database",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TestCaseRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Test case created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TestCase"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        }
                    }
                }
            },
            "/api/v1/test-cases/{test_case_id}": {
                "get": {
                    "summary": "Get test case by ID",
                    "description": "Retrieve a specific test case by its ID",
                    "parameters": [
                        {
                            "name": "test_case_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The test case ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TestCase"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Test case not found"
                        }
                    }
                }
            },
            "/api/v1/test-runs": {
                "get": {
                    "summary": "Get all test runs",
                    "description": "Retrieve all test runs from the database",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/TestRun"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create new test run",
                    "description": "Create a new test run in the database",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TestRunRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Test run created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TestRun"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        }
                    }
                }
            },
            "/api/v1/test-runs/bulk": {
                "post": {
                    "summary": "Create multiple test runs",
                    "description": "Create multiple test runs in the database",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BulkTestRunRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Test runs created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BulkTestRunResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        }
                    }
                }
            },
            "/api/v1/defects": {
                "get": {
                    "summary": "Get all defects",
                    "description": "Retrieve all defects from the database",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/Defect"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create new defect",
                    "description": "Create a new defect in the database",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DefectRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Defect created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Defect"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        }
                    }
                }
            },
            "/api/v1/test-type-summary": {
                "get": {
                    "summary": "Get all test type summaries",
                    "description": "Retrieve all test type summaries from the database",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/TestTypeSummary"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create new test type summary",
                    "description": "Create a new test type summary in the database",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TestTypeSummaryRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Test type summary created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TestTypeSummary"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        }
                    }
                }
            },
            "/api/v1/transit-metrics": {
                "get": {
                    "summary": "Get all transit metrics",
                    "description": "Retrieve all transit metrics from the database",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/TransitMetric"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create new transit metric",
                    "description": "Create a new transit metric in the database",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TransitMetricRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Transit metric created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TransitMetric"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Requirement": {
                    "type": "object",
                    "properties": {
                        "requirement_id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "component": {"type": "string"},
                        "priority": {"type": "string"},
                        "status": {"type": "string"},
                        "jira_id": {"type": "string"},
                        "created_at": {"type": "string", "format": "date-time"}
                    }
                },
                "RequirementRequest": {
                    "type": "object",
                    "required": ["requirement_id", "title"],
                    "properties": {
                        "requirement_id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "component": {"type": "string"},
                        "priority": {"type": "string"},
                        "status": {"type": "string"},
                        "jira_id": {"type": "string"}
                    }
                },
                "TestCase": {
                    "type": "object",
                    "properties": {
                        "test_case_id": {"type": "string"},
                        "title": {"type": "string"},
                        "type": {"type": "string"},
                        "component": {"type": "string"},
                        "requirement_id": {"type": "string"},
                        "status": {"type": "string"},
                        "created_by": {"type": "string"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "pre_condition": {"type": "string"},
                        "test_steps": {"type": "string"},
                        "expected_result": {"type": "string"}
                    }
                },
                "TestCaseRequest": {
                    "type": "object",
                    "required": ["test_case_id", "title"],
                    "properties": {
                        "test_case_id": {"type": "string"},
                        "title": {"type": "string"},
                        "type": {"type": "string"},
                        "component": {"type": "string"},
                        "requirement_id": {"type": "string"},
                        "status": {"type": "string"},
                        "created_by": {"type": "string"},
                        "pre_condition": {"type": "string"},
                        "test_steps": {"type": "string"},
                        "expected_result": {"type": "string"}
                    }
                },
                "TestRun": {
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string"},
                        "test_case_id": {"type": "string"},
                        "execution_date": {"type": "string"},
                        "result": {"type": "string"},
                        "observed_time": {"type": "integer"},
                        "executed_by": {"type": "string"},
                        "remarks": {"type": "string"}
                    }
                },
                "TestRunRequest": {
                    "type": "object",
                    "required": ["run_id", "test_case_id", "result"],
                    "properties": {
                        "run_id": {"type": "string"},
                        "test_case_id": {"type": "string"},
                        "execution_date": {"type": "string"},
                        "result": {"type": "string"},
                        "observed_time": {"type": "integer"},
                        "executed_by": {"type": "string"},
                        "remarks": {"type": "string"}
                    }
                },
                "BulkTestRunRequest": {
                    "type": "object",
                    "properties": {
                        "customerId": {"type": "integer"},
                        "sourceSystem": {"type": "string"},
                        "events": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/TestRunEvent"
                            }
                        }
                    }
                },
                "TestRunEvent": {
                    "type": "object",
                    "required": ["kind", "testCase", "result", "executedBy"],
                    "properties": {
                        "kind": {
                            "type": "string",
                            "description": "Event type (Mandatory field)",
                            "enum": ["TEST_RUN"],
                            "example": "TEST_RUN"
                        },
                        "testCase": {
                            "type": "object",
                            "description": "Test case information (Mandatory field)",
                            "required": ["id", "title"],
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Test case identifier (Mandatory field)",
                                    "example": "TC-UI-NAV-001"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Test case title (Mandatory field)",
                                    "example": "Navigation Menu Test"
                                },
                                "component": {
                                    "type": "string",
                                    "description": "Component being tested (Optional field)",
                                    "example": "UI Navigation"
                                }
                            }
                        },
                        "result": {
                            "type": "string",
                            "description": "Test execution result (Mandatory field)",
                            "enum": ["PASS", "FAIL", "SKIP", "BLOCKED"],
                            "example": "PASS"
                        },
                        "executionDate": {
                            "type": "string", 
                            "format": "date-time",
                            "description": "Test execution timestamp (Optional field - defaults to current time)",
                            "example": "2024-12-01T14:30:22.123Z"
                        },
                        "observedTimeMs": {
                            "type": "integer",
                            "description": "Test execution time in milliseconds (Optional field)",
                            "example": 1500
                        },
                        "executedBy": {
                            "type": "string",
                            "description": "Name of the executor or automation tool (Mandatory field)",
                            "example": "UI Navigator"
                        },
                        "remarks": {
                            "type": "string",
                            "description": "Additional notes or comments (Optional field)",
                            "example": "Test completed successfully"
                        },
                        "artifacts": {
                            "type": "array",
                            "description": "Test artifacts like screenshots, logs, etc. (Optional field)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "description": "Artifact type (e.g., screenshot, log, video)",
                                        "example": "screenshot"
                                    },
                                    "uri": {
                                        "type": "string",
                                        "description": "Artifact file path or URL",
                                        "example": "screenshots/test_result.png"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Artifact description",
                                        "example": "Screenshot of test failure"
                                    }
                                }
                            }
                        }
                    }
                },
                "BulkTestRunResponse": {
                    "type": "object",
                    "properties": {
                        "accepted": {"type": "integer"},
                        "duplicates": {"type": "integer"},
                        "failed": {"type": "integer"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "runId": {"type": "string"},
                                    "testCaseId": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "Defect": {
                    "type": "object",
                    "properties": {
                        "defect_id": {"type": "string"},
                        "title": {"type": "string"},
                        "severity": {"type": "string"},
                        "status": {"type": "string"},
                        "test_case_id": {"type": "string"},
                        "reported_by": {"type": "string"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "fixed_at": {"type": "string", "format": "date-time"}
                    }
                },
                "DefectRequest": {
                    "type": "object",
                    "required": ["defect_id", "title"],
                    "properties": {
                        "defect_id": {"type": "string"},
                        "title": {"type": "string"},
                        "severity": {"type": "string"},
                        "status": {"type": "string"},
                        "test_case_id": {"type": "string"},
                        "reported_by": {"type": "string"}
                    }
                },
                "TestTypeSummary": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "test_type": {"type": "string"},
                        "metrics": {"type": "string"},
                        "expected": {"type": "string"},
                        "actual": {"type": "string"},
                        "status": {"type": "string"},
                        "test_date": {"type": "string"}
                    }
                },
                "TestTypeSummaryRequest": {
                    "type": "object",
                    "required": ["test_type", "metrics"],
                    "properties": {
                        "test_type": {"type": "string"},
                        "metrics": {"type": "string"},
                        "expected": {"type": "string"},
                        "actual": {"type": "string"},
                        "status": {"type": "string"},
                        "test_date": {"type": "string"}
                    }
                },
                "TransitMetric": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "date": {"type": "string"},
                        "fvm_transactions": {"type": "integer"},
                        "gate_taps": {"type": "integer"},
                        "bus_taps": {"type": "integer"},
                        "success_rate_gate": {"type": "number"},
                        "success_rate_bus": {"type": "number"},
                        "avg_response_time": {"type": "integer"},
                        "defect_count": {"type": "integer"},
                        "notes": {"type": "string"}
                    }
                },
                "TransitMetricRequest": {
                    "type": "object",
                    "required": ["date"],
                    "properties": {
                        "date": {"type": "string"},
                        "fvm_transactions": {"type": "integer"},
                        "gate_taps": {"type": "integer"},
                        "bus_taps": {"type": "integer"},
                        "success_rate_gate": {"type": "number"},
                        "success_rate_bus": {"type": "number"},
                        "avg_response_time": {"type": "integer"},
                        "defect_count": {"type": "integer"},
                        "notes": {"type": "string"}
                    }
                },
                "TestResultsRequest": {
                    "type": "object",
                    "required": ["customerId", "testRunId", "events"],
                    "properties": {
                        "customerId": {
                            "type": "integer", 
                            "description": "Customer identifier (Mandatory field)",
                            "example": 12345
                        },
                        "testRunId": {
                            "type": "string", 
                            "description": "Test run identifier - groups multiple test cases under one execution run (Mandatory field)",
                            "example": "UI_NAV_RUN_20241201_143022"
                        },
                        "sourceSystem": {
                            "type": "string", 
                            "description": "Source system that generated the test results (Optional field)",
                            "default": "UI Navigator",
                            "enum": ["UI Navigator", "ROBOT", "TESTING_ENV", "MANUAL"]
                        },
                        "events": {
                            "type": "array",
                            "description": "Array of test events to process (Mandatory field)",
                            "items": {
                                "oneOf": [
                                    {"$ref": "#/components/schemas/TestRunEvent"},
                                    {"$ref": "#/components/schemas/RequirementEvent"},
                                    {"$ref": "#/components/schemas/TestCaseEvent"},
                                    {"$ref": "#/components/schemas/DefectEvent"},
                                    {"$ref": "#/components/schemas/TestTypeSummaryEvent"},
                                    {"$ref": "#/components/schemas/TransitMetricsEvent"}
                                ]
                            }
                        }
                    }
                },
                "TestResultsResponse": {
                    "type": "object",
                    "properties": {
                        "accepted": {"type": "integer", "description": "Number of successfully processed events"},
                        "duplicates": {"type": "integer", "description": "Number of duplicate events"},
                        "failed": {"type": "integer", "description": "Number of failed events"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "enum": ["accepted", "duplicate", "failed"]},
                                    "runId": {"type": "string", "description": "Generated run ID for test runs"},
                                    "testCaseId": {"type": "integer", "description": "Test case identifier"},
                                    "requirementId": {"type": "string", "description": "Requirement identifier"},
                                    "defectId": {"type": "string", "description": "Defect identifier"},
                                    "testType": {"type": "string", "description": "Test type for summaries"},
                                    "date": {"type": "string", "description": "Date for transit metrics"},
                                    "error": {"type": "string", "description": "Error message if status is failed"},
                                    "message": {"type": "string", "description": "Additional message for duplicates"},
                                    "eventKind": {"type": "string", "description": "Type of event that was processed"}
                                }
                            }
                        }
                    }
                },
                "RequirementEvent": {
                    "type": "object",
                    "required": ["kind", "title"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["REQUIREMENT"]},
                        "requirementId": {"type": "string", "description": "Requirement identifier"},
                        "title": {"type": "string", "description": "Requirement title"},
                        "description": {"type": "string", "description": "Requirement description"},
                        "component": {"type": "string", "description": "Component name"},
                        "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                        "status": {"type": "string", "enum": ["Draft", "In Progress", "Review", "Approved", "Completed"]},
                        "jiraId": {"type": "string", "description": "JIRA ticket ID"}
                    }
                },
                "TestCaseEvent": {
                    "type": "object",
                    "required": ["kind", "title"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["TEST_CASE"]},
                        "testCaseId": {"type": "string", "description": "Test case identifier"},
                        "title": {"type": "string", "description": "Test case title"},
                        "type": {"type": "string", "enum": ["Feature", "Regression", "Performance", "Security", "Non-Functional"]},
                        "status": {"type": "string", "enum": ["Draft", "In Review", "Approved", "Deprecated"]},
                        "component": {"type": "string", "description": "Component name"},
                        "requirementId": {"type": "string", "description": "Linked requirement ID"},
                        "createdBy": {"type": "string", "description": "Creator name"},
                        "createdAt": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                        "preCondition": {"type": "string", "description": "Pre-conditions for the test"},
                        "testSteps": {"type": "string", "description": "Test execution steps"},
                        "expectedResult": {"type": "string", "description": "Expected test outcome"}
                    }
                },
                "DefectEvent": {
                    "type": "object",
                    "required": ["kind", "title"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["DEFECT"]},
                        "defectId": {"type": "string", "description": "Defect identifier"},
                        "title": {"type": "string", "description": "Defect title"},
                        "description": {"type": "string", "description": "Defect description"},
                        "severity": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                        "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                        "status": {"type": "string", "enum": ["Open", "In Progress", "Resolved", "Closed", "Reopened"]},
                        "component": {"type": "string", "description": "Component name"},
                        "testCaseId": {"type": "string", "description": "Linked test case ID"},
                        "reportedBy": {"type": "string", "description": "Reporter name"},
                        "reportedDate": {"type": "string", "format": "date-time", "description": "Report timestamp"}
                    }
                },
                "TestTypeSummaryEvent": {
                    "type": "object",
                    "required": ["kind", "testType", "metrics"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["TEST_TYPE_SUMMARY"]},
                        "testType": {"type": "string", "description": "Type of test"},
                        "metrics": {"type": "string", "description": "Metric name"},
                        "expected": {"type": "string", "description": "Expected value"},
                        "actual": {"type": "string", "description": "Actual value"},
                        "status": {"type": "string", "enum": ["Pass", "Fail", "Blocked", "Skipped"]},
                        "testDate": {"type": "string", "format": "date-time", "description": "Test execution date"}
                    }
                },
                "TransitMetricsEvent": {
                    "type": "object",
                    "required": ["kind", "date"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["TRANSIT_METRICS"]},
                        "date": {"type": "string", "format": "date", "description": "Date for metrics"},
                        "fvmTransactions": {"type": "integer", "description": "Number of FVM transactions"},
                        "successRateGate": {"type": "number", "description": "Gate success rate percentage"},
                        "successRateBus": {"type": "number", "description": "Bus success rate percentage"},
                        "successRateStation": {"type": "number", "description": "Station success rate percentage"}
                    }
                }
            }
        }
    }
    return jsonify(swagger_spec)

def init_database():
    """Initialize the database with all required tables"""
    try:
        print("🚀 Initializing database...")
        
        # Create all tables (simple approach like CRM)
        from database_postgresql import Base, engine
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully")
        
        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Database initialization will be called when app starts

# Database helper functions - now using PostgreSQL with lazy initialization
def create_user(user_data):
    """Create a new user"""
    return get_db().create_user(user_data)

def get_user_by_username(username):
    """Get user by username"""
    return get_db().get_user_by_username(username)

def get_user_by_email(email):
    """Get user by email"""
    return get_db().get_user_by_email(email)

def update_user_password(username, new_password):
    """Update user password"""
    return get_db().update_user_password(username, new_password)

def db_create_requirement(requirement_data):
    """Create a new requirement"""
    return get_db().create_requirement(requirement_data)

def get_all_requirements():
    """Get all requirements"""
    return get_db().get_all_requirements()

def db_get_requirement_by_id(requirement_id):
    """Get requirement by ID"""
    return get_db().get_requirement_by_id(requirement_id)

def create_test_case(test_case_data):
    """Create a new test case"""
    return get_db().create_test_case(test_case_data)

def get_all_test_cases():
    """Get all test cases"""
    return get_db().get_all_test_cases()

def get_test_case_by_id(test_case_id):
    """Get test case by ID"""
    return get_db().get_test_case_by_id(test_case_id)

def get_test_cases_by_requirement(requirement_id):
    """Get test cases by requirement ID"""
    return get_db().get_test_cases_by_requirement(requirement_id)

def get_test_cases_with_description():
    """Get test cases with requirement descriptions"""
    return get_db().get_test_cases_with_description()

def create_test_run(test_run_data):
    """Create a new test run"""
    return get_db().create_test_run(test_run_data)

def get_all_test_runs():
    """Get all test runs"""
    return get_db().get_all_test_runs()

def create_defect(defect_data):
    """Create a new defect"""
    return get_db().create_defect(defect_data)

def get_all_defects():
    """Get all defects"""
    return get_db().get_all_defects()

def create_test_type_summary(summary_data):
    """Create a new test type summary"""
    return get_db().create_test_type_summary(summary_data)

def get_all_test_type_summary():
    """Get all test type summaries"""
    return get_db().get_all_test_type_summary()

def create_transit_metric(metric_data):
    """Create a new transit metric"""
    return get_db().create_transit_metric(metric_data)

def get_all_transit_metrics():
    """Get all transit metrics"""
    return get_db().get_all_transit_metrics()

JSONBIN_API_KEY = os.getenv("JSONBIN_API_KEY")

JWT_SECRET = os.getenv('JWT_SECRET', 'your_jwt_secret_key')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 7 * 24 * 3600  # 7 days

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', 'your_email@gmail.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your_email_password')
RESET_LINK_BASE = os.getenv('RESET_LINK_BASE', 'http://localhost:3000/reset-password')

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

# --- JWT Utility Functions ---
def create_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header missing or invalid'}), 401
        token = auth_header.split(' ')[1]
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        request.user_id = payload['user_id']
        return f(*args, **kwargs)
    return decorated_function

# --- Test Cases API Endpoints ---
@app.route('/api/testcases', methods=['GET', 'POST'])
def handle_structured_test_cases():
    if request.method == 'GET':
        try:
            test_cases = get_all_test_cases()
            return jsonify(test_cases), 200
        except Exception as e:
            print(f"Error in get_structured_test_cases: {e}")
            traceback.print_exc()
            return jsonify({"error": "Internal server error"}), 500
            
    elif request.method == 'POST':
        try:
            test_cases_data = request.get_json()
            
            if not isinstance(test_cases_data, list):
                return jsonify({"error": "Invalid request format. Expected a list of test cases."}), 400
                
            # Get existing requirement IDs for validation
            existing_requirements = get_all_requirements()
            existing_requirement_ids = {req['requirement_id'] for req in existing_requirements}
            
            uploaded_count = 0
            for test_case in test_cases_data:
                # Validate requirement_id if present
                requirement_id = test_case.get("Requirement_ID")
                if requirement_id and requirement_id not in existing_requirement_ids:
                    print(f"Info: Requirement_ID '{requirement_id}' for Test_Case_ID '{test_case.get('Test_Case_ID')}' not found in requirements table. Keeping the ID for future linking.")
                    # Keep the requirement ID - don't set to None
                    
                # Store test case
                if create_test_case(test_case):
                    uploaded_count += 1
                
            return jsonify({"message": f"Successfully uploaded {uploaded_count} test cases", "success_count": uploaded_count}), 200
            
        except Exception as e:
            print(f"Error in post_structured_test_cases: {e}")
            traceback.print_exc()
            return jsonify({"error": "Internal server error"}), 500

@app.route('/api/structuredtestcases/<test_case_id>', methods=['GET'])
def get_structured_test_case_by_id(test_case_id):
    try:
        test_case = get_test_case_by_id(test_case_id)
        if test_case:
            return jsonify(test_case), 200
        else:
            return jsonify({"error": f"Structured test case with ID {test_case_id} not found"}), 404
    except Exception as e:
        print(f"Error in get_structured_test_case_by_id: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Requirements API Endpoints ---
@app.route('/api/requirements', methods=['POST'])
def create_requirement():
    try:
        data = request.get_json()
        
        # Handle both single object and array of objects
        requirements_to_add = data if isinstance(data, list) else [data]
        
        if not requirements_to_add:
            return jsonify({"error": "No requirements data provided"}), 400

        success_count = 0
        for req in requirements_to_add:
            # Ensure requirement_id exists or generate one
            requirement_id = str(req.get('requirement_id') or str(uuid.uuid4()))
            req['requirement_id'] = requirement_id
            
            if db_create_requirement(req):
                success_count += 1

        return jsonify({
            "message": f"Successfully uploaded {success_count} requirements",
            "success_count": success_count
        }), 201
    except Exception as e:
        print(f"Error creating requirement: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/requirements', methods=['GET'])
def get_requirements():
    try:
        requirements = get_all_requirements()
        return jsonify(requirements), 200
    except Exception as e:
        print(f"Error getting requirements: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/requirements/<requirement_id>', methods=['GET'])
def get_requirement_by_id(requirement_id):
    try:
        requirement = db_get_requirement_by_id(requirement_id)
        if requirement:
            return jsonify(requirement), 200
        else:
            return jsonify({"error": f"Requirement with ID {requirement_id} not found"}), 404
    except Exception as e:
        print(f"Error getting requirement by ID: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Test Runs API Endpoints ---
@app.route('/api/testruns', methods=['POST'])
def receive_test_run_data():
    try:
        data = request.get_json()
        if not isinstance(data, list):
            return jsonify({"error": "Invalid request format. Expected a list of test run results."}), 400

        success_count = 0
        for run in data:
            run_id = run.get('run_id')
            if not run_id:
                return jsonify({"error": "Each test run must have a run_id."}), 400
            if create_test_run(run):
                success_count += 1

        return jsonify({"message": f"{success_count} test run results stored successfully"}), 200

    except Exception as e:
        print(f"Error in receive_test_run_data: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/testruns', methods=['GET'])
def get_test_runs():
    try:
        test_runs = get_all_test_runs()
        return jsonify(test_runs), 200
    except Exception as e:
        print(f"Error in get_test_runs: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Defects API Endpoints ---
@app.route('/api/defects', methods=['POST'])
def receive_defect_data():
    try:
        data = request.get_json()
        if not isinstance(data, list):
            return jsonify({"error": "Invalid request format. Expected a list of defects."}), 400

        success_count = 0
        for defect in data:
            defect_id = defect.get('DefectID')
            if not defect_id:
                return jsonify({"error": "Each defect must have a DefectID."}), 400
            if create_defect(defect):
                success_count += 1

        return jsonify({"message": f"{success_count} defects stored successfully"}), 200

    except Exception as e:
        print(f"Error in receive_defect_data: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/defects', methods=['GET'])
def get_defects():
    try:
        defects = get_all_defects()
        return jsonify(defects), 200
    except Exception as e:
        print(f"Error in get_defects: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Test Type Summary API Endpoints ---
@app.route('/api/testtypesummary', methods=['POST'])
def receive_test_type_summary_data():
    try:
        data = request.get_json()
        if not isinstance(data, list):
            return jsonify({"error": "Invalid request format. Expected a list of test type summary entries."}), 400

        success_count = 0
        for summary_entry in data:
            test_type = summary_entry.get('Test_Type')
            metrics = summary_entry.get('Metrics')
            if not test_type or not metrics:
                return jsonify({"error": "Each test type summary entry must have 'Test_Type' and 'Metrics'."}), 400

            if create_test_type_summary(summary_entry):
                success_count += 1

        return jsonify({"message": f"{success_count} test type summary entries stored successfully"}), 200

    except Exception as e:
        print(f"Error in receive_test_type_summary_data: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/testtypesummary', methods=['GET'])
def get_test_type_summary_data():
    try:
        summary_data = get_all_test_type_summary()
        return jsonify(summary_data), 200
    except Exception as e:
        print(f"Error in get_test_type_summary_data: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Transit Metrics Daily API Endpoints ---
@app.route('/api/transitmetricsdaily', methods=['POST'])
def receive_transit_metrics_data():
    try:
        data = request.get_json()
        
        # If single object is received, convert to list
        if isinstance(data, dict):
            data = [data]
            
        if not isinstance(data, list):
            return jsonify({"error": "Invalid request format. Expected a list of transit metrics entries."}), 400

        success_count = 0
        for metric in data:
            if create_transit_metric(metric):
                success_count += 1

        return jsonify({"message": f"{success_count} transit metrics entries stored successfully"}), 200

    except Exception as e:
        print(f"Error in receive_transit_metrics_data: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/transitmetricsdaily', methods=['GET'])
def get_transit_metrics_data():
    try:
        metrics_data = get_all_transit_metrics()
        return jsonify(metrics_data), 200
    except Exception as e:
        print(f"Error in get_transit_metrics_data: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Additional API Endpoints ---
@app.route('/api/testcases/by_requirement', methods=['GET'])
def get_test_cases_by_requirement_route():
    requirement_id = request.args.get('requirementId')
    if not requirement_id:
        return jsonify({"error": "Missing requirementId parameter"}), 400

    try:
        test_cases = get_test_cases_by_requirement(requirement_id)
        return jsonify(test_cases), 200
    except Exception as e:
        print(f"Error in get_test_cases_by_requirement: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/testcases/with_description', methods=['GET'])
def get_structured_test_cases_with_description():
    try:
        test_cases = get_test_cases_with_description()
        return jsonify(test_cases), 200
    except Exception as e:
        print(f"Error in get_structured_test_cases_with_description: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/test-cases/<test_case_id>', methods=['GET'])
def get_test_case_details_by_id(test_case_id):
    try:
        test_case = get_test_case_by_id(test_case_id)
        if test_case:
            return jsonify(test_case), 200
        else:
            return jsonify({"error": f"Test case with ID {test_case_id} not found"}), 404
    except Exception as e:
        print(f"Error in get_test_case_details_by_id: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Upload Endpoints ---
@app.route('/api/upload/testrail', methods=['POST'])
def upload_testrail_test_cases():
    try:
        test_cases_data = request.get_json()

        if not isinstance(test_cases_data, list):
            return jsonify({"error": "Invalid request format. Expected a list of test cases from the mock API."}), 400

        # Get existing requirement IDs for validation
        existing_requirements = get_all_requirements()
        existing_requirement_ids = {req['requirement_id'] for req in existing_requirements}

        uploaded_count = 0
        for test_case in test_cases_data:
            # Map the fields from the mock TestRail API response
            mapped_test_case = {
                "Test_Case_ID": str(test_case.get("id")),
                "Title": test_case.get("title"),
                "Type": test_case.get("type"),
                "Component": test_case.get("component"),
                "Requirement_ID": str(test_case.get("requirement_id")) if test_case.get("requirement_id") else None,
                "Status": test_case.get("status"),
                "Created_By": test_case.get("created_by"),
                "Uploaded_At": datetime.datetime.now().isoformat()
            }

            test_case_id_for_doc = mapped_test_case["Test_Case_ID"]
            requirement_id_for_validation = mapped_test_case["Requirement_ID"]

            if not test_case_id_for_doc:
                print(f"Skipping test case due to missing ID: {test_case}")
                continue

            # Validate requirement_id if present
            if requirement_id_for_validation and requirement_id_for_validation not in existing_requirement_ids:
                print(f"Info: Requirement_ID '{requirement_id_for_validation}' for Test_Case_ID '{test_case_id_for_doc}' not found in requirements table. Keeping the ID for future linking.")
                # Keep the requirement ID - don't set to None

            if create_test_case(mapped_test_case):
                uploaded_count += 1

        return jsonify({"message": f"{uploaded_count} test cases from TestRail mock API uploaded successfully."}), 200

    except Exception as e:
        print(f"Error in upload_testrail_test_cases: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/testcases/upload/url', methods=['POST'])
def upload_test_cases_from_url():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "Missing 'url' in request body"}), 400

        headers = {}
        if JSONBIN_API_KEY:
            headers['X-Master-Key'] = JSONBIN_API_KEY
            headers['Content-Type'] = 'application/json'

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        test_cases_data = response.json()

        if not isinstance(test_cases_data, list):
            return jsonify({"error": "Invalid data format from URL. Expected a list of test cases."}), 400

        # Get existing requirement IDs for validation
        existing_requirements = get_all_requirements()
        existing_requirement_ids = {req['requirement_id'] for req in existing_requirements}

        uploaded_count = 0
        for test_case in test_cases_data:
            test_case_id = test_case.get('Test_Case_ID')
            requirement_id = test_case.get('Requirement_ID')
            if not test_case_id:
                return jsonify({"error": "Each test case must have a Test_Case_ID."}), 400
            if requirement_id and str(requirement_id) not in existing_requirement_ids:
                print(f"Info: Requirement_ID '{requirement_id}' for Test_Case_ID '{test_case_id}' not found in requirements table. Keeping the ID for future linking.")
                # Keep the requirement ID - don't set to None
            if create_test_case(test_case):
                uploaded_count += 1

        return jsonify({"message": f"{uploaded_count} test cases uploaded successfully from URL"}), 200

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from URL: {e}")
        return jsonify({"error": f"Error fetching data from URL: {e}"}), 400
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from URL: {e}")
        return jsonify({"error": "Invalid JSON format from URL"}), 400
    except Exception as e:
        print(f"Error in upload_test_cases_from_url: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/testcases/upload/local', methods=['POST'])
def upload_test_cases_from_local():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file:
            test_cases_data = json.load(file)

            if not isinstance(test_cases_data, list):
                return jsonify({"error": "Invalid file format. Expected a JSON list of test cases."}), 400

            # Get existing requirement IDs for validation
            existing_requirements = get_all_requirements()
            existing_requirement_ids = {req['requirement_id'] for req in existing_requirements}

            uploaded_count = 0
            for test_case in test_cases_data:
                test_case_id = test_case.get('Test_Case_ID')
                requirement_id = test_case.get('Requirement_ID')
                if not test_case_id:
                    return jsonify({"error": "Each test case must have a Test_Case_ID."}), 400
                if requirement_id and str(requirement_id) not in existing_requirement_ids:
                    print(f"Info: Requirement_ID '{requirement_id}' for Test_Case_ID '{test_case_id}' not found in requirements table. Keeping the ID for future linking.")
                    # Keep the requirement ID - don't set to None
                if create_test_case(test_case):
                    uploaded_count += 1

            return jsonify({"message": f"{uploaded_count} test cases uploaded successfully from local file"}), 200

        return jsonify({"error": "No valid file uploaded"}), 400

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from uploaded file: {e}")
        return jsonify({"error": "Invalid JSON file format"}), 400
    except Exception as e:
        print(f"Error in upload_test_cases_from_local: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- URL Upload Endpoints for other entities ---
@app.route('/api/requirements/upload/url', methods=['POST'])
def upload_requirements_from_url():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "URL is required"}), 400

        response = requests.get(url)
        if not response.ok:
            return jsonify({"error": f"Failed to fetch data from URL: {response.status_code}"}), 400

        requirements_data = response.json()
        if not isinstance(requirements_data, list):
            return jsonify({"error": "Invalid data format. Expected a list of requirements."}), 400

        success_count = 0
        for req in requirements_data:
            requirement_id = str(req.get('requirement_id'))
            if not requirement_id:
                continue
            if db_create_requirement(req):
                success_count += 1

        return jsonify({"message": f"{success_count} requirements uploaded successfully"}), 200
    except Exception as e:
        print(f"Error uploading requirements from URL: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/testruns/upload/url', methods=['POST'])
def upload_testruns_from_url():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "URL is required"}), 400

        response = requests.get(url)
        if not response.ok:
            return jsonify({"error": f"Failed to fetch data from URL: {response.status_code}"}), 400

        testruns_data = response.json()
        if not isinstance(testruns_data, list):
            return jsonify({"error": "Invalid data format. Expected a list of test runs."}), 400

        success_count = 0
        for tr in testruns_data:
            run_id = str(tr.get('run_id'))
            if not run_id:
                continue
            if create_test_run(tr):
                success_count += 1

        return jsonify({"message": f"{success_count} test runs uploaded successfully"}), 200
    except Exception as e:
        print(f"Error uploading test runs from URL: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/defects/upload/url', methods=['POST'])
def upload_defects_from_url():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "URL is required"}), 400

        response = requests.get(url)
        if not response.ok:
            return jsonify({"error": f"Failed to fetch data from URL: {response.status_code}"}), 400

        defects_data = response.json()
        if not isinstance(defects_data, list):
            return jsonify({"error": "Invalid data format. Expected a list of defects."}), 400

        success_count = 0
        for defect in defects_data:
            defect_id = str(defect.get('DefectID'))
            if not defect_id:
                continue
            if create_defect(defect):
                success_count += 1

        return jsonify({"message": f"{success_count} defects uploaded successfully"}), 200
    except Exception as e:
        print(f"Error uploading defects from URL: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/testtypesummary/upload/url', methods=['POST'])
def upload_testtypesummary_from_url():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "URL is required"}), 400

        response = requests.get(url)
        if not response.ok:
            return jsonify({"error": f"Failed to fetch data from URL: {response.status_code}"}), 400

        summary_data = response.json()
        if not isinstance(summary_data, list):
            return jsonify({"error": "Invalid data format. Expected a list of test type summaries."}), 400

        success_count = 0
        for summary in summary_data:
            if create_test_type_summary(summary):
                success_count += 1

        return jsonify({"message": f"{success_count} test type summaries uploaded successfully"}), 200
    except Exception as e:
        print(f"Error uploading test type summaries from URL: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/transitmetricsdaily/upload/url', methods=['POST'])
def upload_transitmetrics_from_url():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "URL is required"}), 400

        response = requests.get(url)
        if not response.ok:
            return jsonify({"error": f"Failed to fetch data from URL: {response.status_code}"}), 400

        metrics_data = response.json()
        if not isinstance(metrics_data, list):
            return jsonify({"error": "Invalid data format. Expected a list of transit metrics."}), 400

        success_count = 0
        for metric in metrics_data:
            if create_transit_metric(metric):
                success_count += 1

        return jsonify({"message": f"{success_count} transit metrics uploaded successfully"}), 200
    except Exception as e:
        print(f"Error uploading transit metrics from URL: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Auth Endpoints ---
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    phone = data.get('phone')
    country_code = data.get('countryCode')
    
    if not username or not password or not email:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409
    
    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_data = {
        'username': username,
        'password': hashed_pw,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'phone': phone,
        'country_code': country_code
    }
    
    try:
        print(f"Attempting to create user: {username}")
        success = create_user(user_data)
        print(f"User creation result: {success}")
        if success:
            return jsonify({'message': 'User created successfully'}), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
    except Exception as e:
        print(f"Signup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Signup failed: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = get_user_by_username(username)
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    token = create_jwt_token(username)
    return jsonify({'token': token, 'user': {
        'username': user['username'],
        'email': user['email'],
        'first_name': user.get('first_name'),
        'last_name': user.get('last_name'),
        'phone': user.get('phone'),
        'country_code': user.get('country_code')
    }}), 200

@app.route('/api/me', methods=['GET'])
@login_required
def get_me():
    user_id = request.user_id
    user = get_user_by_username(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'username': user['username'],
        'email': user['email'],
        'first_name': user.get('first_name'),
        'last_name': user.get('last_name'),
        'phone': user.get('phone'),
        'country_code': user.get('country_code')
    }), 200

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    method = data.get('method')
    value = data.get('value')
    
    if not method or not value:
        return jsonify({'error': 'Missing method or value'}), 400
    
    user = None
    if method == 'email':
        user = get_user_by_email(value)
    elif method == 'phone':
        # Note: Phone lookup not implemented in current database schema
        # You would need to add a phone field index or implement phone lookup
        pass
    
    # If user exists and has email, send reset email
    if user and user.get('email'):
        try:
            reset_token = jwt.encode(
                {'username': user['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, 
                JWT_SECRET, 
                algorithm=JWT_ALGORITHM
            )
            reset_link = f"{RESET_LINK_BASE}?token={reset_token}"
            subject = "Password Reset Request"
            body = f"Hello {user['username']},\n\nTo reset your password, click the link below (valid for 30 minutes):\n{reset_link}\n\nIf you did not request this, please ignore this email."
            
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = user['email']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, user['email'], msg.as_string())
        except Exception as e:
            print(f"Error sending reset email: {e}")
            # For privacy, do not reveal error to user
    
    # For privacy, always return success
    return jsonify({'message': 'If the account exists, reset instructions have been sent.'}), 200

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('newPassword')
    
    if not token or not new_password:
        return jsonify({'error': 'Missing token or new password'}), 400
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get('username')
        if not username:
            return jsonify({'error': 'Invalid token'}), 400
        
        user = get_user_by_username(username)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if update_user_password(username, hashed_pw):
            return jsonify({'message': 'Password has been reset successfully.'}), 200
        else:
            return jsonify({'error': 'Failed to update password.'}), 500
            
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Reset link has expired.'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid or tampered reset link.'}), 400
    except Exception as e:
        print(f"Error in reset_password: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# REST API v1 ENDPOINTS - Comprehensive API for all entities
# ============================================================================

# --- Requirements v1 API ---
@app.route('/api/v1/requirements', methods=['GET'])
def get_requirements_v1():
    """Get all requirements - REST API v1"""
    try:
        requirements = get_all_requirements()
        return jsonify(requirements), 200
    except Exception as e:
        print(f"Error getting requirements: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/requirements', methods=['POST'])
def create_requirement_v1():
    """Create new requirement - REST API v1"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('requirement_id') or not data.get('title'):
            return jsonify({"error": "requirement_id and title are required"}), 400
        
        if db_create_requirement(data):
            return jsonify(data), 201
        else:
            return jsonify({"error": "Failed to create requirement"}), 500
    except Exception as e:
        print(f"Error creating requirement: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/requirements/<requirement_id>', methods=['GET'])
def get_requirement_by_id_v1(requirement_id):
    """Get requirement by ID - REST API v1"""
    try:
        requirement = db_get_requirement_by_id(requirement_id)
        if requirement:
            return jsonify(requirement), 200
        else:
            return jsonify({"error": f"Requirement with ID {requirement_id} not found"}), 404
    except Exception as e:
        print(f"Error getting requirement by ID: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Test Cases v1 API ---
@app.route('/api/v1/test-cases', methods=['GET'])
def get_test_cases_v1():
    """Get all test cases - REST API v1"""
    try:
        test_cases = get_all_test_cases()
        return jsonify(test_cases), 200
    except Exception as e:
        print(f"Error getting test cases: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/test-cases', methods=['POST'])
def create_test_case_v1():
    """Create new test case - REST API v1"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('test_case_id') or not data.get('title'):
            return jsonify({"error": "test_case_id and title are required"}), 400
        
        if create_test_case(data):
            return jsonify(data), 201
        else:
            return jsonify({"error": "Failed to create test case"}), 500
    except Exception as e:
        print(f"Error creating test case: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/test-cases/<test_case_id>', methods=['GET'])
def get_test_case_by_id_v1(test_case_id):
    """Get test case by ID - REST API v1"""
    try:
        test_case = get_test_case_by_id(test_case_id)
        if test_case:
            return jsonify(test_case), 200
        else:
            return jsonify({"error": f"Test case with ID {test_case_id} not found"}), 404
    except Exception as e:
        print(f"Error getting test case by ID: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# --- Test Runs v1 API ---
@app.route('/api/v1/test-runs', methods=['GET'])
def get_test_runs_v1():
    """Get all test runs - REST API v1"""
    try:
        test_runs = get_all_test_runs()
        return jsonify(test_runs), 200
    except Exception as e:
        print(f"Error getting test runs: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/test-runs', methods=['POST'])
def create_test_run_v1():
    """Create new test run - REST API v1"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('run_id') or not data.get('test_case_id') or not data.get('result'):
            return jsonify({"error": "run_id, test_case_id, and result are required"}), 400
        
        if create_test_run(data):
            return jsonify(data), 201
        else:
            return jsonify({"error": "Failed to create test run"}), 500
    except Exception as e:
        print(f"Error creating test run: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/test-runs/bulk', methods=['POST'])
def create_bulk_test_runs_v1():
    """Create multiple test runs - REST API v1 (similar to your sample)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        events = data.get('events', [])
        if not events:
            return jsonify({"error": "No events provided"}), 400
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                # Extract test case info
                test_case = event.get('testCase', {})
                test_case_id = str(test_case.get('id', ''))
                
                # Create test run data
                test_run_data = {
                    'run_id': str(uuid.uuid4()),  # Generate unique run ID
                    'test_case_id': test_case_id,
                    'execution_date': event.get('executionDate', datetime.datetime.now().isoformat()),
                    'result': event.get('result', 'Unknown'),
                    'observed_time': event.get('observedTimeMs', 0),
                    'executed_by': event.get('executedBy', 'Unknown'),
                    'remarks': event.get('remarks', '')
                }
                
                if create_test_run(test_run_data):
                    accepted += 1
                    items.append({
                        'status': 'accepted',
                        'runId': test_run_data['run_id'],
                        'testCaseId': int(test_case_id) if test_case_id.isdigit() else 0
                    })
                else:
                    failed += 1
                    items.append({
                        'status': 'failed',
                        'runId': test_run_data['run_id'],
                        'testCaseId': int(test_case_id) if test_case_id.isdigit() else 0
                    })
                    
            except Exception as e:
                failed += 1
                print(f"Error processing event: {e}")
                items.append({
                    'status': 'failed',
                    'runId': str(uuid.uuid4()),
                    'testCaseId': 0
                })
        
        response = {
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        print(f"Error creating bulk test runs: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Defects v1 API ---
@app.route('/api/v1/defects', methods=['GET'])
def get_defects_v1():
    """Get all defects - REST API v1"""
    try:
        defects = get_all_defects()
        return jsonify(defects), 200
    except Exception as e:
        print(f"Error getting defects: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/defects', methods=['POST'])
def create_defect_v1():
    """Create new defect - REST API v1"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('defect_id') or not data.get('title'):
            return jsonify({"error": "defect_id and title are required"}), 400
        
        if create_defect(data):
            return jsonify(data), 201
        else:
            return jsonify({"error": "Failed to create defect"}), 500
    except Exception as e:
        print(f"Error creating defect: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Test Type Summary v1 API ---
@app.route('/api/v1/test-type-summary', methods=['GET'])
def get_test_type_summary_v1():
    """Get all test type summaries - REST API v1"""
    try:
        summaries = get_all_test_type_summary()
        return jsonify(summaries), 200
    except Exception as e:
        print(f"Error getting test type summaries: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/test-type-summary', methods=['POST'])
def create_test_type_summary_v1():
    """Create new test type summary - REST API v1"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('test_type') or not data.get('metrics'):
            return jsonify({"error": "test_type and metrics are required"}), 400
        
        if create_test_type_summary(data):
            return jsonify(data), 201
        else:
            return jsonify({"error": "Failed to create test type summary"}), 500
    except Exception as e:
        print(f"Error creating test type summary: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Transit Metrics v1 API ---
@app.route('/api/v1/transit-metrics', methods=['GET'])
def get_transit_metrics_v1():
    """Get all transit metrics - REST API v1"""
    try:
        metrics = get_all_transit_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        print(f"Error getting transit metrics: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/transit-metrics', methods=['POST'])
def create_transit_metric_v1():
    """Create new transit metric - REST API v1"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('date'):
            return jsonify({"error": "date is required"}), 400
        
        if create_transit_metric(data):
            return jsonify(data), 201
        else:
            return jsonify({"error": "Failed to create transit metric"}), 500
    except Exception as e:
        print(f"Error creating transit metric: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Comprehensive Test Results API ---
@app.route('/api/v1/results/test-runs', methods=['POST'])
def process_test_results():
    """Comprehensive Test Results API - handles all types of test data with enhanced validation"""
    try:
        # Check if request has files (multipart/form-data) or JSON
        if request.files:
            # Handle file upload with JSON data
            data = request.form.get('data')
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON data"}), 400
        else:
            # Handle JSON-only request
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        customer_id = data.get('customerId')
        test_run_id = data.get('testRunId')  # This is the missing parameter you mentioned
        source_system = data.get('sourceSystem', 'UI Navigator')
        events = data.get('events', [])
        
        if not customer_id:
            return jsonify({"error": "customerId is required"}), 400
        if not test_run_id:
            return jsonify({"error": "testRunId is required"}), 400
        if not events:
            return jsonify({"error": "No events provided"}), 400
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                event_kind = event.get('kind', '').upper()
                
                if event_kind == 'TEST_RUN':
                    result = process_test_run_event_v2(event, customer_id, test_run_id, source_system, request.files)
                elif event_kind == 'REQUIREMENT':
                    result = process_requirement_event(event, customer_id, source_system)
                elif event_kind == 'TEST_CASE':
                    result = process_test_case_event(event, customer_id, source_system)
                elif event_kind == 'DEFECT':
                    result = process_defect_event(event, customer_id, source_system)
                elif event_kind == 'TEST_TYPE_SUMMARY':
                    result = process_test_type_summary_event(event, customer_id, source_system)
                elif event_kind == 'TRANSIT_METRICS':
                    result = process_transit_metrics_event(event, customer_id, source_system)
                else:
                    result = {
                        'status': 'failed',
                        'error': f'Unknown event kind: {event_kind}'
                    }
                
                if result['status'] == 'accepted':
                    accepted += 1
                elif result['status'] == 'duplicate':
                    duplicates += 1
                else:
                    failed += 1
                
                items.append(result)
                
            except Exception as e:
                failed += 1
                print(f"Error processing event: {e}")
                items.append({
                    'status': 'failed',
                    'error': str(e),
                    'eventKind': event.get('kind', 'Unknown')
                })
        
        response = {
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items,
            'testRunId': test_run_id,
            'customerId': customer_id
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        print(f"Error processing test results: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def process_test_run_event_v2(event, customer_id, test_run_id, source_system, files=None):
    """Process a test run event with enhanced validation and file support"""
    try:
        test_case = event.get('testCase', {})
        test_case_id = str(test_case.get('id', ''))
        
        # Validate required fields
        if not test_case_id:
            return {
                'status': 'failed',
                'error': 'testCase.id is required'
            }
        
        if not event.get('result'):
            return {
                'status': 'failed',
                'error': 'result is required'
            }
        
        if not event.get('executedBy'):
            return {
                'status': 'failed',
                'error': 'executedBy is required'
            }
        
        # Process artifacts
        artifacts = []
        if event.get('artifacts'):
            for artifact in event['artifacts']:
                artifacts.append({
                    'type': artifact.get('type', 'unknown'),
                    'uri': artifact.get('uri', ''),
                    'description': artifact.get('description', '')
                })
        
        # Handle file uploads if present
        if files:
            for file_key, file_obj in files.items():
                if file_obj and file_obj.filename:
                    filepath = save_artifact_file(file_obj, test_run_id, test_case_id)
                    if filepath:
                        artifacts.append({
                            'type': 'uploaded_file',
                            'uri': filepath,
                            'filename': file_obj.filename,
                            'description': f'Uploaded file: {file_obj.filename}'
                        })
        
        # Create test run data
        test_run_data = {
            'run_id': str(uuid.uuid4()),
            'test_run_id': test_run_id,
            'customer_id': customer_id,
            'source_system': source_system,
            'test_case_id': test_case_id,
            'execution_date': event.get('executionDate', datetime.datetime.now().isoformat()),
            'result': event.get('result'),
            'observed_time': event.get('observedTimeMs', 0),
            'executed_by': event.get('executedBy'),
            'remarks': event.get('remarks', ''),
            'artifacts': json.dumps(artifacts) if artifacts else None
        }
        
        # Check for duplicates (same test run, same test case)
        existing_runs = get_db().get_test_runs_by_run_id(test_run_id)
        duplicate_found = any(
            run.get('test_case_id') == test_case_id
            for run in existing_runs
        )
        
        if duplicate_found:
            return {
                'status': 'duplicate',
                'runId': test_run_data['run_id'],
                'testCaseId': test_case_id,
                'message': f'Test case {test_case_id} already exists in test run {test_run_id}'
            }
        
        if get_db().create_test_run(test_run_data):
            return {
                'status': 'accepted',
                'runId': test_run_data['run_id'],
                'testCaseId': test_case_id,
                'testRunId': test_run_id,
                'result': test_run_data['result'],
                'executedBy': test_run_data['executed_by'],
                'artifacts': len(artifacts)
            }
        else:
            return {
                'status': 'failed',
                'runId': test_run_data['run_id'],
                'testCaseId': test_case_id,
                'error': 'Failed to create test run'
            }
            
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }

def process_test_run_event(event, customer_id, source_system):
    """Process a test run event"""
    try:
        test_case = event.get('testCase', {})
        test_case_id = str(test_case.get('id', ''))
        
        # Create test run data
        test_run_data = {
            'run_id': str(uuid.uuid4()),
            'test_case_id': test_case_id,
            'execution_date': event.get('executionDate', datetime.datetime.now().isoformat()),
            'result': event.get('result', 'Unknown'),
            'observed_time': event.get('observedTimeMs', 0),
            'executed_by': event.get('executedBy', 'Unknown'),
            'remarks': event.get('remarks', '')
        }
        
        # Check for duplicates (same test case, same execution date, same result)
        existing_runs = get_all_test_runs()
        duplicate_found = any(
            run.get('test_case_id') == test_case_id and
            run.get('execution_date') == test_run_data['execution_date'] and
            run.get('result') == test_run_data['result']
            for run in existing_runs
        )
        
        if duplicate_found:
            return {
                'status': 'duplicate',
                'runId': test_run_data['run_id'],
                'testCaseId': int(test_case_id) if test_case_id.isdigit() else 0,
                'message': 'Duplicate test run detected'
            }
        
        if create_test_run(test_run_data):
            return {
                'status': 'accepted',
                'runId': test_run_data['run_id'],
                'testCaseId': int(test_case_id) if test_case_id.isdigit() else 0
            }
        else:
            return {
                'status': 'failed',
                'runId': test_run_data['run_id'],
                'testCaseId': int(test_case_id) if test_case_id.isdigit() else 0,
                'error': 'Failed to create test run'
            }
            
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }

def process_requirement_event(event, customer_id, source_system):
    """Process a requirement event"""
    try:
        requirement_data = {
            'requirement_id': event.get('requirementId', str(uuid.uuid4())),
            'title': event.get('title', ''),
            'description': event.get('description', ''),
            'component': event.get('component', ''),
            'priority': event.get('priority', 'Medium'),
            'status': event.get('status', 'Draft'),
            'jira_id': event.get('jiraId', '')
        }
        
        if get_db().create_requirement(requirement_data):
            return {
                'status': 'accepted',
                'requirementId': requirement_data['requirement_id'],
                'title': requirement_data['title']
            }
        else:
            return {
                'status': 'failed',
                'requirementId': requirement_data['requirement_id'],
                'error': 'Failed to create requirement'
            }
            
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }

def process_test_case_event(event, customer_id, source_system):
    """Process a test case event"""
    try:
        test_case_data = {
            'test_case_id': event.get('testCaseId', str(uuid.uuid4())),
            'title': event.get('title', ''),
            'type': event.get('type', 'Feature'),
            'status': event.get('status', 'Draft'),
            'component': event.get('component', ''),
            'requirement_id': event.get('requirementId', ''),
            'created_by': event.get('createdBy', source_system),
            'created_at': event.get('createdAt', datetime.datetime.now().isoformat()),
            'pre_condition': event.get('preCondition', ''),
            'test_steps': event.get('testSteps', ''),
            'expected_result': event.get('expectedResult', '')
        }
        
        if get_db().create_test_case(test_case_data):
            return {
                'status': 'accepted',
                'testCaseId': test_case_data['test_case_id'],
                'title': test_case_data['title']
            }
        else:
            return {
                'status': 'failed',
                'testCaseId': test_case_data['test_case_id'],
                'error': 'Failed to create test case'
            }
            
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }

def process_defect_event(event, customer_id, source_system):
    """Process a defect event"""
    try:
        defect_data = {
            'defect_id': event.get('defectId', str(uuid.uuid4())),
            'title': event.get('title', ''),
            'severity': event.get('severity', 'Medium'),
            'status': event.get('status', 'Open'),
            'test_case_id': event.get('testCaseId', ''),
            'reported_by': event.get('reportedBy', source_system),
            'created_at': event.get('reportedDate', datetime.datetime.now().isoformat())
        }
        
        if get_db().create_defect(defect_data):
            return {
                'status': 'accepted',
                'defectId': defect_data['defect_id'],
                'title': defect_data['title']
            }
        else:
            return {
                'status': 'failed',
                'defectId': defect_data['defect_id'],
                'error': 'Failed to create defect'
            }
            
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }

def process_test_type_summary_event(event, customer_id, source_system):
    """Process a test type summary event"""
    try:
        summary_data = {
            'test_type': event.get('testType', ''),
            'metrics': event.get('metrics', ''),
            'expected': event.get('expected', ''),
            'actual': event.get('actual', ''),
            'status': event.get('status', ''),
            'test_date': event.get('testDate', datetime.datetime.now().isoformat())
        }
        
        if get_db().create_test_type_summary(summary_data):
            return {
                'status': 'accepted',
                'testType': summary_data['test_type'],
                'metrics': summary_data['metrics']
            }
        else:
            return {
                'status': 'failed',
                'testType': summary_data['test_type'],
                'error': 'Failed to create test type summary'
            }
            
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }

def process_transit_metrics_event(event, customer_id, source_system):
    """Process a transit metrics event"""
    try:
        metrics_data = {
            'date': event.get('date', datetime.datetime.now().strftime('%Y-%m-%d')),
            'fvm_transactions': event.get('fvmTransactions', 0),
            'gate_taps': event.get('gateTaps', 0),
            'bus_taps': event.get('busTaps', 0),
            'success_rate_gate': event.get('successRateGate', 0.0),
            'success_rate_bus': event.get('successRateBus', 0.0),
            'avg_response_time': event.get('avgResponseTime', 0),
            'defect_count': event.get('defectCount', 0),
            'notes': event.get('notes', '')
        }
        
        if get_db().create_transit_metric(metrics_data):
            return {
                'status': 'accepted',
                'date': metrics_data['date'],
                'fvmTransactions': metrics_data['fvm_transactions']
            }
        else:
            return {
                'status': 'failed',
                'date': metrics_data['date'],
                'error': 'Failed to create transit metrics'
            }
            
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }

# ============================================================================
# API HEALTH CHECK
# ============================================================================



@app.route('/api/v1/health', methods=['GET'])
def health_check_v1():
    """Health check endpoint - REST API v1"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "PostgreSQL",
        "endpoints": {
            "requirements": "/api/v1/requirements",
            "test_cases": "/api/v1/test-cases",
            "test_runs": "/api/v1/test-runs",
            "defects": "/api/v1/defects",
            "test_type_summary": "/api/v1/test-type-summary",
            "transit_metrics": "/api/v1/transit-metrics",
            "swagger_docs": "/api/docs"
        }
    }), 200

# File upload configuration
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'log'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_artifact_file(file, test_run_id, test_case_id):
    """Save uploaded artifact file and return the file path"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create unique filename with test run and case info
        unique_filename = f"{test_run_id}_{test_case_id}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        return filepath
    return None

# --- Test Results Reading APIs ---
@app.route('/api/v1/results/test-runs', methods=['GET'])
def get_test_results():
    """Get test results with filtering options"""
    try:
        # Query parameters
        customer_id = request.args.get('customerId', type=int)
        test_run_id = request.args.get('testRunId')
        test_case_id = request.args.get('testCaseId')
        result = request.args.get('result')  # Pass, Fail, etc.
        source_system = request.args.get('sourceSystem')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get all test runs
        test_runs = get_all_test_runs()
        
        # Apply filters
        filtered_runs = []
        for run in test_runs:
            if customer_id and run.get('customer_id') != customer_id:
                continue
            if test_run_id and run.get('test_run_id') != test_run_id:
                continue
            if test_case_id and run.get('test_case_id') != test_case_id:
                continue
            if result and run.get('result') != result:
                continue
            if source_system and run.get('source_system') != source_system:
                continue
            filtered_runs.append(run)
        
        # Apply pagination
        total_count = len(filtered_runs)
        paginated_runs = filtered_runs[offset:offset + limit]
        
        response = {
            'testRuns': paginated_runs,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'hasMore': offset + limit < total_count
            },
            'filters': {
                'customerId': customer_id,
                'testRunId': test_run_id,
                'testCaseId': test_case_id,
                'result': result,
                'sourceSystem': source_system
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error getting test results: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/results/test-runs/<test_run_id>', methods=['GET'])
def get_test_run_by_id(test_run_id):
    """Get all test cases for a specific test run"""
    try:
        test_runs = get_db().get_test_runs_by_run_id(test_run_id)
        
        if not test_runs:
            return jsonify({"error": f"Test run {test_run_id} not found"}), 404
        
        # Group by test case and calculate summary
        test_cases = {}
        summary = {
            'total': len(test_runs),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'totalTime': 0
        }
        
        for run in test_runs:
            test_case_id = run.get('test_case_id')
            if test_case_id not in test_cases:
                test_cases[test_case_id] = {
                    'testCaseId': test_case_id,
                    'result': run.get('result'),
                    'executedBy': run.get('executed_by'),
                    'executionDate': run.get('execution_date'),
                    'observedTime': run.get('observed_time'),
                    'remarks': run.get('remarks'),
                    'artifacts': run.get('artifacts')
                }
            
            # Update summary
            result = run.get('result', '').lower()
            if 'pass' in result:
                summary['passed'] += 1
            elif 'fail' in result:
                summary['failed'] += 1
            else:
                summary['skipped'] += 1
            
            summary['totalTime'] += run.get('observed_time', 0)
        
        response = {
            'testRunId': test_run_id,
            'customerId': test_runs[0].get('customer_id') if test_runs else None,
            'sourceSystem': test_runs[0].get('source_system') if test_runs else None,
            'summary': summary,
            'testCases': list(test_cases.values())
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error getting test run: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/results/customers/<int:customer_id>/test-runs', methods=['GET'])
def get_customer_test_runs(customer_id):
    """Get all test runs for a customer"""
    try:
        test_runs = get_db().get_test_runs_by_customer(customer_id)
        
        # Group by test run ID
        test_run_groups = {}
        for run in test_runs:
            run_id = run.get('test_run_id')
            if run_id not in test_run_groups:
                test_run_groups[run_id] = {
                    'testRunId': run_id,
                    'sourceSystem': run.get('source_system'),
                    'totalCases': 0,
                    'passed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'totalTime': 0,
                    'lastExecution': run.get('execution_date')
                }
            
            group = test_run_groups[run_id]
            group['totalCases'] += 1
            group['totalTime'] += run.get('observed_time', 0)
            
            result = run.get('result', '').lower()
            if 'pass' in result:
                group['passed'] += 1
            elif 'fail' in result:
                group['failed'] += 1
            else:
                group['skipped'] += 1
        
        response = {
            'customerId': customer_id,
            'testRuns': list(test_run_groups.values()),
            'totalTestRuns': len(test_run_groups)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error getting customer test runs: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize database before starting the app (like CRM)
    print("🚀 Starting Reporting Backend...")
    
    try:
        # Create database tables
        from database_postgresql import Base, get_engine
        Base.metadata.create_all(bind=get_engine())
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️  Warning: Database initialization failed: {e}")
        print("🔄 Continuing startup - database will be initialized on first use")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
