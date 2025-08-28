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

# Import PostgreSQL database manager
from database_postgresql import db

load_dotenv()

app = Flask(__name__)
CORS(app)

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Reporting Application API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

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
                "url": "http://localhost:5000",
                "description": "Development server"
            },
            {
                "url": "https://reporting-backend-kpoz.onrender.com",
                "description": "Production server"
            }
        ],
        "paths": {
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
            },
            "/api/v1/results": {
                "post": {
                    "summary": "Unified bulk upload endpoint",
                    "description": "Single endpoint to upload all types of data (requirements, test cases, test runs, defects, test type summaries, transit metrics). Automatically routes data to appropriate tables based on event kind.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UnifiedBulkUploadRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Bulk upload completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BulkUploadResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data or missing required fields"
                        },
                        "500": {
                            "description": "Internal server error"
                        }
                    }
                }
            },
            "/api/v1/results/test-runs": {
                "post": {
                    "summary": "Bulk upload test run results",
                    "description": "Upload multiple test run results in a single request",
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
                        "200": {
                            "description": "Bulk upload completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BulkUploadResponse"
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
            "/api/v1/results/requirements": {
                "post": {
                    "summary": "Bulk upload requirements",
                    "description": "Upload multiple requirements in a single request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BulkRequirementRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Bulk upload completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BulkUploadResponse"
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
            "/api/v1/results/test-cases": {
                "post": {
                    "summary": "Bulk upload test cases",
                    "description": "Upload multiple test cases in a single request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BulkTestCaseRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Bulk upload completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BulkUploadResponse"
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
            "/api/v1/results/defects": {
                "post": {
                    "summary": "Bulk upload defects",
                    "description": "Upload multiple defects in a single request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BulkDefectRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Bulk upload completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BulkUploadResponse"
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
            "/api/v1/results/test-type-summary": {
                "post": {
                    "summary": "Bulk upload test type summaries",
                    "description": "Upload multiple test type summaries in a single request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BulkTestTypeSummaryRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Bulk upload completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BulkUploadResponse"
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
            "/api/v1/results/transit-metrics": {
                "post": {
                    "summary": "Bulk upload transit metrics",
                    "description": "Upload multiple transit metrics in a single request",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BulkTransitMetricRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Bulk upload completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/BulkUploadResponse"
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
            "/api/login": {
                "post": {
                    "summary": "User login",
                    "description": "Authenticate user with username and password",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password"],
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "token": {"type": "string"},
                                            "user": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid credentials"
                        }
                    }
                }
            },
            "/api/signup": {
                "post": {
                    "summary": "User signup",
                    "description": "Create a new user account",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password", "email"],
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"},
                                        "email": {"type": "string"},
                                        "first_name": {"type": "string"},
                                        "last_name": {"type": "string"},
                                        "phone": {"type": "string"},
                                        "country_code": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "user": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid data"
                        },
                        "409": {
                            "description": "User already exists"
                        }
                    }
                }
            },
            "/admin/db-info": {
                "get": {
                    "summary": "Get database information",
                    "description": "Retrieve database connection and table information",
                    "responses": {
                        "200": {
                            "description": "Database information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "database_url": {"type": "string"},
                                            "tables": {"type": "array"},
                                            "connection_status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/admin/db-test": {
                "get": {
                    "summary": "Test database connection",
                    "description": "Test the database connection and return status",
                    "responses": {
                        "200": {
                            "description": "Database connection test result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "message": {"type": "string"},
                                            "timestamp": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/admin/schema-info": {
                "get": {
                    "summary": "Get database schema information",
                    "description": "Retrieve detailed database schema information",
                    "responses": {
                        "200": {
                            "description": "Schema information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "tables": {"type": "array"},
                                            "columns": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/admin/generate-data": {
                "post": {
                    "summary": "Generate test data",
                    "description": "Generate sample test data for all tables",
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "requirements_count": {"type": "integer"},
                                        "test_cases_count": {"type": "integer"},
                                        "test_runs_count": {"type": "integer"},
                                        "defects_count": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Test data generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "generated": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/admin/reset-db": {
                "post": {
                    "summary": "Reset database schema",
                    "description": "Reset all database tables and recreate schema",
                    "responses": {
                        "200": {
                            "description": "Database reset successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/admin/delete-db": {
                "post": {
                    "summary": "Delete all data",
                    "description": "Delete all data from all tables",
                    "responses": {
                        "200": {
                            "description": "All data deleted successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "deleted_tables": {"type": "array"}
                                        }
                                    }
                                }
                            }
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
                    "properties": {
                        "kind": {"type": "string"},
                        "testCase": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "title": {"type": "string"},
                                "component": {"type": "string"}
                            }
                        },
                        "result": {"type": "string"},
                        "executionDate": {"type": "string", "format": "date-time"},
                        "observedTimeMs": {"type": "integer"},
                        "executedBy": {"type": "string"},
                        "remarks": {"type": "string"},
                        "artifacts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "uri": {"type": "string"}
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
                "BulkTestRunRequest": {
                    "type": "object",
                    "required": ["customerId", "sourceSystem", "events"],
                    "properties": {
                        "customerId": {"type": "integer"},
                        "sourceSystem": {"type": "string"},
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "testCase", "result"],
                                "properties": {
                                    "kind": {"type": "string", "enum": ["TEST_RUN"]},
                                    "testCase": {
                                        "type": "object",
                                        "required": ["id", "title", "component"],
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "title": {"type": "string"},
                                            "component": {"type": "string"}
                                        }
                                    },
                                    "result": {"type": "string", "enum": ["Pass", "Fail", "Skip"]},
                                    "executionDate": {"type": "string", "format": "date-time"},
                                    "observedTimeMs": {"type": "integer"},
                                    "executedBy": {"type": "string"},
                                    "remarks": {"type": "string"},
                                    "artifacts": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string"},
                                                "uri": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "BulkRequirementRequest": {
                    "type": "object",
                    "required": ["customerId", "sourceSystem", "events"],
                    "properties": {
                        "customerId": {"type": "integer"},
                        "sourceSystem": {"type": "string"},
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "requirement"],
                                "properties": {
                                    "kind": {"type": "string", "enum": ["REQUIREMENT"]},
                                    "requirement": {
                                        "type": "object",
                                        "required": ["id", "title"],
                                        "properties": {
                                            "id": {"type": "string"},
                                            "title": {"type": "string"},
                                            "description": {"type": "string"},
                                            "component": {"type": "string"},
                                            "priority": {"type": "string"},
                                            "status": {"type": "string"},
                                            "jiraId": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "BulkTestCaseRequest": {
                    "type": "object",
                    "required": ["customerId", "sourceSystem", "events"],
                    "properties": {
                        "customerId": {"type": "integer"},
                        "sourceSystem": {"type": "string"},
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "testCase"],
                                "properties": {
                                    "kind": {"type": "string", "enum": ["TEST_CASE"]},
                                    "testCase": {
                                        "type": "object",
                                        "required": ["id", "title"],
                                        "properties": {
                                            "id": {"type": "string"},
                                            "title": {"type": "string"},
                                            "type": {"type": "string"},
                                            "component": {"type": "string"},
                                            "requirementId": {"type": "string"},
                                            "status": {"type": "string"},
                                            "createdBy": {"type": "string"},
                                            "preCondition": {"type": "string"},
                                            "testSteps": {"type": "string"},
                                            "expectedResult": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "BulkDefectRequest": {
                    "type": "object",
                    "required": ["customerId", "sourceSystem", "events"],
                    "properties": {
                        "customerId": {"type": "integer"},
                        "sourceSystem": {"type": "string"},
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "defect"],
                                "properties": {
                                    "kind": {"type": "string", "enum": ["DEFECT"]},
                                    "defect": {
                                        "type": "object",
                                        "required": ["id", "title"],
                                        "properties": {
                                            "id": {"type": "string"},
                                            "title": {"type": "string"},
                                            "severity": {"type": "string"},
                                            "status": {"type": "string"},
                                            "testCaseId": {"type": "string"},
                                            "reportedBy": {"type": "string"},
                                            "fixedAt": {"type": "string", "format": "date-time"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "BulkTestTypeSummaryRequest": {
                    "type": "object",
                    "required": ["customerId", "sourceSystem", "events"],
                    "properties": {
                        "customerId": {"type": "integer"},
                        "sourceSystem": {"type": "string"},
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "summary"],
                                "properties": {
                                    "kind": {"type": "string", "enum": ["TEST_TYPE_SUMMARY"]},
                                    "summary": {
                                        "type": "object",
                                        "required": ["testType", "metrics"],
                                        "properties": {
                                            "testType": {"type": "string"},
                                            "metrics": {"type": "string"},
                                            "expected": {"type": "string"},
                                            "actual": {"type": "string"},
                                            "status": {"type": "string"},
                                            "testDate": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "BulkTransitMetricRequest": {
                    "type": "object",
                    "required": ["customerId", "sourceSystem", "events"],
                    "properties": {
                        "customerId": {"type": "integer"},
                        "sourceSystem": {"type": "string"},
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "metric"],
                                "properties": {
                                    "kind": {"type": "string", "enum": ["TRANSIT_METRIC"]},
                                    "metric": {
                                        "type": "object",
                                        "required": ["date"],
                                        "properties": {
                                            "date": {"type": "string"},
                                            "fvmTransactions": {"type": "integer"},
                                            "gateTaps": {"type": "integer"},
                                            "busTaps": {"type": "integer"},
                                            "successRateGate": {"type": "number"},
                                            "successRateBus": {"type": "number"},
                                            "avgResponseTime": {"type": "integer"},
                                            "defectCount": {"type": "integer"},
                                            "notes": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "BulkUploadResponse": {
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
                                    "status": {"type": "string", "enum": ["accepted", "duplicate", "failed"]},
                                    "runId": {"type": "string"},
                                    "testCaseId": {"type": "integer"},
                                    "requirementId": {"type": "string"},
                                    "defectId": {"type": "string"},
                                    "testType": {"type": "string"},
                                    "date": {"type": "string"},
                                    "error": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "UnifiedBulkUploadRequest": {
                    "type": "object",
                    "required": ["customerId", "sourceSystem", "events"],
                    "properties": {
                        "customerId": {"type": "integer"},
                        "sourceSystem": {"type": "string"},
                        "events": {
                            "type": "array",
                            "items": {
                                "oneOf": [
                                    {"$ref": "#/components/schemas/TestRunEvent"},
                                    {"$ref": "#/components/schemas/RequirementEvent"},
                                    {"$ref": "#/components/schemas/TestCaseEvent"},
                                    {"$ref": "#/components/schemas/DefectEvent"},
                                    {"$ref": "#/components/schemas/TestTypeSummaryEvent"},
                                    {"$ref": "#/components/schemas/TransitMetricEvent"}
                                ]
                            }
                        }
                    }
                },
                "TestRunEvent": {
                    "type": "object",
                    "required": ["kind", "testCase", "result"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["TEST_RUN"]},
                        "testCase": {
                            "type": "object",
                            "required": ["id", "title", "component"],
                            "properties": {
                                "id": {"type": "integer"},
                                "title": {"type": "string"},
                                "component": {"type": "string"}
                            }
                        },
                        "result": {"type": "string", "enum": ["Pass", "Fail", "Skip"]},
                        "executionDate": {"type": "string", "format": "date-time"},
                        "observedTimeMs": {"type": "integer"},
                        "executedBy": {"type": "string"},
                        "remarks": {"type": "string"},
                        "artifacts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "uri": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "RequirementEvent": {
                    "type": "object",
                    "required": ["kind", "requirement"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["REQUIREMENT"]},
                        "requirement": {
                            "type": "object",
                            "required": ["id", "title"],
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "component": {"type": "string"},
                                "priority": {"type": "string"},
                                "status": {"type": "string"},
                                "jiraId": {"type": "string"}
                            }
                        }
                    }
                },
                "TestCaseEvent": {
                    "type": "object",
                    "required": ["kind", "testCase"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["TEST_CASE"]},
                        "testCase": {
                            "type": "object",
                            "required": ["id", "title"],
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "type": {"type": "string"},
                                "component": {"type": "string"},
                                "requirementId": {"type": "string"},
                                "status": {"type": "string"},
                                "createdBy": {"type": "string"},
                                "preCondition": {"type": "string"},
                                "testSteps": {"type": "string"},
                                "expectedResult": {"type": "string"}
                            }
                        }
                    }
                },
                "DefectEvent": {
                    "type": "object",
                    "required": ["kind", "defect"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["DEFECT"]},
                        "defect": {
                            "type": "object",
                            "required": ["id", "title"],
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "severity": {"type": "string"},
                                "status": {"type": "string"},
                                "testCaseId": {"type": "string"},
                                "reportedBy": {"type": "string"},
                                "fixedAt": {"type": "string", "format": "date-time"}
                            }
                        }
                    }
                },
                "TestTypeSummaryEvent": {
                    "type": "object",
                    "required": ["kind", "summary"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["TEST_TYPE_SUMMARY"]},
                        "summary": {
                            "type": "object",
                            "required": ["testType", "metrics"],
                            "properties": {
                                "testType": {"type": "string"},
                                "metrics": {"type": "string"},
                                "expected": {"type": "string"},
                                "actual": {"type": "string"},
                                "status": {"type": "string"},
                                "testDate": {"type": "string"}
                            }
                        }
                    }
                },
                "TransitMetricEvent": {
                    "type": "object",
                    "required": ["kind", "metric"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["TRANSIT_METRIC"]},
                        "metric": {
                            "type": "object",
                            "required": ["date"],
                            "properties": {
                                "date": {"type": "string"},
                                "fvmTransactions": {"type": "integer"},
                                "gateTaps": {"type": "integer"},
                                "busTaps": {"type": "integer"},
                                "successRateGate": {"type": "number"},
                                "successRateBus": {"type": "number"},
                                "avgResponseTime": {"type": "integer"},
                                "defectCount": {"type": "integer"},
                                "notes": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
    return jsonify(swagger_spec)

def init_database():
    """Initialize the database with all required tables"""
    # Database initialization is now handled by SQLAlchemy in database_postgresql.py
    print("✅ Database initialized via SQLAlchemy")

# Initialize database on startup
init_database()

# Database helper functions - now using PostgreSQL
def create_user(user_data):
    """Create a new user"""
    return db.create_user(user_data)

def get_user_by_username(username):
    """Get user by username"""
    return db.get_user_by_username(username)

def get_user_by_email(email):
    """Get user by email"""
    return db.get_user_by_email(email)

def update_user_password(username, new_password):
    """Update user password"""
    return db.update_user_password(username, new_password)

def db_create_requirement(requirement_data):
    """Create a new requirement"""
    return db.create_requirement(requirement_data)

def get_all_requirements():
    """Get all requirements"""
    return db.get_all_requirements()

def db_get_requirement_by_id(requirement_id):
    """Get requirement by ID"""
    return db.get_requirement_by_id(requirement_id)

def create_test_case(test_case_data):
    """Create a new test case"""
    return db.create_test_case(test_case_data)

def get_all_test_cases():
    """Get all test cases"""
    return db.get_all_test_cases()

def get_test_case_by_id(test_case_id):
    """Get test case by ID"""
    return db.get_test_case_by_id(test_case_id)

def get_test_cases_by_requirement(requirement_id):
    """Get test cases by requirement ID"""
    return db.get_test_cases_by_requirement(requirement_id)

def get_test_cases_with_description():
    """Get test cases with requirement descriptions"""
    return db.get_test_cases_with_description()

def create_test_run(test_run_data):
    """Create a new test run"""
    return db.create_test_run(test_run_data)

def get_all_test_runs():
    """Get all test runs"""
    return db.get_all_test_runs()

def create_defect(defect_data):
    """Create a new defect"""
    return db.create_defect(defect_data)

def get_all_defects():
    """Get all defects"""
    return db.get_all_defects()

def create_test_type_summary(summary_data):
    """Create a new test type summary"""
    return db.create_test_type_summary(summary_data)

def get_all_test_type_summary():
    """Get all test type summaries"""
    return db.get_all_test_type_summary()

def create_transit_metric(metric_data):
    """Create a new transit metric"""
    return db.create_transit_metric(metric_data)

def get_all_transit_metrics():
    """Get all transit metrics"""
    return db.get_all_transit_metrics()

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
        'country_code': country_code,
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    
    if create_user(user_data):
        return jsonify({'message': 'User created successfully'}), 201
    else:
        return jsonify({'error': 'Failed to create user'}), 500

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

# ============================================================================
# UNIFIED BULK UPLOAD API - SINGLE ENDPOINT FOR ALL DATA TYPES
# ============================================================================

@app.route('/api/v1/results', methods=['POST'])
def unified_bulk_upload():
    """Unified bulk upload endpoint - accepts all data types and routes to appropriate tables"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('customerId') or not data.get('sourceSystem') or not data.get('events'):
            return jsonify({"error": "customerId, sourceSystem, and events are required"}), 400
        
        customer_id = data['customerId']
        source_system = data['sourceSystem']
        events = data['events']
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                event_kind = event.get('kind')
                
                # Route based on event kind
                if event_kind == 'TEST_RUN':
                    result = process_test_run_event(event, items)
                    if result['success']:
                        accepted += 1
                    else:
                        failed += 1
                        
                elif event_kind == 'REQUIREMENT':
                    result = process_requirement_event(event, items)
                    if result['success']:
                        accepted += 1
                    elif result['duplicate']:
                        duplicates += 1
                    else:
                        failed += 1
                        
                elif event_kind == 'TEST_CASE':
                    result = process_test_case_event(event, items)
                    if result['success']:
                        accepted += 1
                    elif result['duplicate']:
                        duplicates += 1
                    else:
                        failed += 1
                        
                elif event_kind == 'DEFECT':
                    result = process_defect_event(event, items)
                    if result['success']:
                        accepted += 1
                    elif result['duplicate']:
                        duplicates += 1
                    else:
                        failed += 1
                        
                elif event_kind == 'TEST_TYPE_SUMMARY':
                    result = process_test_type_summary_event(event, items)
                    if result['success']:
                        accepted += 1
                    else:
                        failed += 1
                        
                elif event_kind == 'TRANSIT_METRIC':
                    result = process_transit_metric_event(event, items)
                    if result['success']:
                        accepted += 1
                    elif result['duplicate']:
                        duplicates += 1
                    else:
                        failed += 1
                        
                else:
                    failed += 1
                    items.append({
                        'status': 'failed',
                        'error': f'Unknown event kind: {event_kind}'
                    })
                    
            except Exception as e:
                failed += 1
                items.append({
                    'status': 'failed',
                    'error': str(e)
                })
        
        return jsonify({
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items
        }), 200
        
    except Exception as e:
        print(f"Error in unified bulk upload: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def process_test_run_event(event, items):
    """Process test run event"""
    try:
        test_case = event.get('testCase', {})
        test_case_id = test_case.get('id')
        title = test_case.get('title')
        component = test_case.get('component')
        
        # Generate unique run ID
        run_id = str(uuid.uuid4())
        
        # Create test run data
        test_run_data = {
            'run_id': run_id,
            'test_case_id': str(test_case_id),
            'execution_date': event.get('executionDate'),
            'result': event.get('result'),
            'observed_time': event.get('observedTimeMs'),
            'executed_by': event.get('executedBy'),
            'remarks': event.get('remarks')
        }
        
        # Check if test case exists
        existing_test_case = db.get_test_case_by_id(str(test_case_id))
        if not existing_test_case:
            # Create test case if it doesn't exist
            test_case_data = {
                'test_case_id': str(test_case_id),
                'title': title,
                'component': component,
                'type': 'Automated',
                'status': 'Active',
                'created_by': event.get('executedBy', 'system'),
                'created_at': datetime.datetime.now()
            }
            db.create_test_case(test_case_data)
        
        # Create test run
        if db.create_test_run(test_run_data):
            items.append({
                'status': 'accepted',
                'runId': run_id,
                'testCaseId': test_case_id
            })
            return {'success': True}
        else:
            items.append({
                'status': 'failed',
                'runId': None,
                'testCaseId': test_case_id,
                'error': 'Failed to create test run'
            })
            return {'success': False}
            
    except Exception as e:
        items.append({
            'status': 'failed',
            'runId': None,
            'testCaseId': event.get('testCase', {}).get('id'),
            'error': str(e)
        })
        return {'success': False}

def process_requirement_event(event, items):
    """Process requirement event"""
    try:
        requirement_data = event.get('requirement', {})
        requirement_id = requirement_data.get('id')
        
        # Check if requirement already exists
        existing_requirement = db.get_requirement_by_id(requirement_id)
        if existing_requirement:
            items.append({
                'status': 'duplicate',
                'requirementId': requirement_id,
                'error': 'Requirement already exists'
            })
            return {'success': False, 'duplicate': True}
        
        # Create requirement data
        req_data = {
            'requirement_id': requirement_id,
            'title': requirement_data.get('title'),
            'description': requirement_data.get('description'),
            'component': requirement_data.get('component'),
            'priority': requirement_data.get('priority'),
            'status': requirement_data.get('status', 'Active'),
            'jira_id': requirement_data.get('jiraId'),
            'created_at': datetime.datetime.now()
        }
        
        if db.create_requirement(req_data):
            items.append({
                'status': 'accepted',
                'requirementId': requirement_id
            })
            return {'success': True}
        else:
            items.append({
                'status': 'failed',
                'requirementId': requirement_id,
                'error': 'Failed to create requirement'
            })
            return {'success': False}
            
    except Exception as e:
        items.append({
            'status': 'failed',
            'requirementId': event.get('requirement', {}).get('id'),
            'error': str(e)
        })
        return {'success': False}

def process_test_case_event(event, items):
    """Process test case event"""
    try:
        test_case_data = event.get('testCase', {})
        test_case_id = test_case_data.get('id')
        
        # Check if test case already exists
        existing_test_case = db.get_test_case_by_id(test_case_id)
        if existing_test_case:
            items.append({
                'status': 'duplicate',
                'testCaseId': test_case_id,
                'error': 'Test case already exists'
            })
            return {'success': False, 'duplicate': True}
        
        # Create test case data
        tc_data = {
            'test_case_id': test_case_id,
            'title': test_case_data.get('title'),
            'type': test_case_data.get('type'),
            'component': test_case_data.get('component'),
            'requirement_id': test_case_data.get('requirementId'),
            'status': test_case_data.get('status', 'Active'),
            'created_by': test_case_data.get('createdBy', 'system'),
            'created_at': datetime.datetime.now(),
            'pre_condition': test_case_data.get('preCondition'),
            'test_steps': test_case_data.get('testSteps'),
            'expected_result': test_case_data.get('expectedResult'),
            'uploaded_at': datetime.datetime.now()
        }
        
        if db.create_test_case(tc_data):
            items.append({
                'status': 'accepted',
                'testCaseId': test_case_id
            })
            return {'success': True}
        else:
            items.append({
                'status': 'failed',
                'testCaseId': test_case_id,
                'error': 'Failed to create test case'
            })
            return {'success': False}
            
    except Exception as e:
        items.append({
            'status': 'failed',
            'testCaseId': event.get('testCase', {}).get('id'),
            'error': str(e)
        })
        return {'success': False}

def process_defect_event(event, items):
    """Process defect event"""
    try:
        defect_data = event.get('defect', {})
        defect_id = defect_data.get('id')
        
        # Check if defect already exists
        existing_defect = db.get_defect_by_id(defect_id)
        if existing_defect:
            items.append({
                'status': 'duplicate',
                'defectId': defect_id,
                'error': 'Defect already exists'
            })
            return {'success': False, 'duplicate': True}
        
        # Create defect data
        d_data = {
            'defect_id': defect_id,
            'title': defect_data.get('title'),
            'severity': defect_data.get('severity'),
            'status': defect_data.get('status', 'Open'),
            'test_case_id': defect_data.get('testCaseId'),
            'reported_by': defect_data.get('reportedBy'),
            'created_at': datetime.datetime.now(),
            'fixed_at': defect_data.get('fixedAt')
        }
        
        if db.create_defect(d_data):
            items.append({
                'status': 'accepted',
                'defectId': defect_id
            })
            return {'success': True}
        else:
            items.append({
                'status': 'failed',
                'defectId': defect_id,
                'error': 'Failed to create defect'
            })
            return {'success': False}
            
    except Exception as e:
        items.append({
            'status': 'failed',
            'defectId': event.get('defect', {}).get('id'),
            'error': str(e)
        })
        return {'success': False}

def process_test_type_summary_event(event, items):
    """Process test type summary event"""
    try:
        summary_data = event.get('summary', {})
        
        # Create summary data
        s_data = {
            'test_type': summary_data.get('testType'),
            'metrics': summary_data.get('metrics'),
            'expected': summary_data.get('expected'),
            'actual': summary_data.get('actual'),
            'status': summary_data.get('status'),
            'test_date': summary_data.get('testDate')
        }
        
        if db.create_test_type_summary(s_data):
            items.append({
                'status': 'accepted',
                'testType': summary_data.get('testType')
            })
            return {'success': True}
        else:
            items.append({
                'status': 'failed',
                'testType': summary_data.get('testType'),
                'error': 'Failed to create test type summary'
            })
            return {'success': False}
            
    except Exception as e:
        items.append({
            'status': 'failed',
            'testType': event.get('summary', {}).get('testType'),
            'error': str(e)
        })
        return {'success': False}

def process_transit_metric_event(event, items):
    """Process transit metric event"""
    try:
        metric_data = event.get('metric', {})
        date = metric_data.get('date')
        
        # Check if metric for this date already exists
        existing_metrics = db.get_all_transit_metrics()
        existing_dates = [m.get('Date') for m in existing_metrics]
        if date in existing_dates:
            items.append({
                'status': 'duplicate',
                'date': date,
                'error': 'Metric for this date already exists'
            })
            return {'success': False, 'duplicate': True}
        
        # Create metric data
        m_data = {
            'date': date,
            'fvm_transactions': metric_data.get('fvmTransactions'),
            'gate_taps': metric_data.get('gateTaps'),
            'bus_taps': metric_data.get('busTaps'),
            'success_rate_gate': metric_data.get('successRateGate'),
            'success_rate_bus': metric_data.get('successRateBus'),
            'avg_response_time': metric_data.get('avgResponseTime'),
            'defect_count': metric_data.get('defectCount'),
            'notes': metric_data.get('notes')
        }
        
        if db.create_transit_metric(m_data):
            items.append({
                'status': 'accepted',
                'date': date
            })
            return {'success': True}
        else:
            items.append({
                'status': 'failed',
                'date': date,
                'error': 'Failed to create transit metric'
            })
            return {'success': False}
            
    except Exception as e:
        items.append({
            'status': 'failed',
            'date': event.get('metric', {}).get('date'),
            'error': str(e)
        })
        return {'success': False}

# ============================================================================
# TEST RESULTS API - BULK UPLOAD ENDPOINTS (INDIVIDUAL - KEPT FOR BACKWARD COMPATIBILITY)
# ============================================================================

@app.route('/api/v1/results/test-runs', methods=['POST'])
def bulk_upload_test_runs():
    """Bulk upload test run results"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('customerId') or not data.get('sourceSystem') or not data.get('events'):
            return jsonify({"error": "customerId, sourceSystem, and events are required"}), 400
        
        customer_id = data['customerId']
        source_system = data['sourceSystem']
        events = data['events']
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                if event.get('kind') != 'TEST_RUN':
                    continue
                
                test_case = event.get('testCase', {})
                test_case_id = test_case.get('id')
                title = test_case.get('title')
                component = test_case.get('component')
                
                # Generate unique run ID
                run_id = str(uuid.uuid4())
                
                # Create test run data
                test_run_data = {
                    'run_id': run_id,
                    'test_case_id': str(test_case_id),
                    'execution_date': event.get('executionDate'),
                    'result': event.get('result'),
                    'observed_time': event.get('observedTimeMs'),
                    'executed_by': event.get('executedBy'),
                    'remarks': event.get('remarks')
                }
                
                # Check if test case exists
                existing_test_case = db.get_test_case_by_id(str(test_case_id))
                if not existing_test_case:
                    # Create test case if it doesn't exist
                    test_case_data = {
                        'test_case_id': str(test_case_id),
                        'title': title,
                        'component': component,
                        'type': 'Automated',
                        'status': 'Active',
                        'created_by': event.get('executedBy', 'system'),
                        'created_at': datetime.datetime.now()
                    }
                    db.create_test_case(test_case_data)
                
                # Create test run
                if db.create_test_run(test_run_data):
                    accepted += 1
                    items.append({
                        'status': 'accepted',
                        'runId': run_id,
                        'testCaseId': test_case_id
                    })
                else:
                    failed += 1
                    items.append({
                        'status': 'failed',
                        'runId': None,
                        'testCaseId': test_case_id,
                        'error': 'Failed to create test run'
                    })
                    
            except Exception as e:
                failed += 1
                items.append({
                    'status': 'failed',
                    'runId': None,
                    'testCaseId': event.get('testCase', {}).get('id'),
                    'error': str(e)
                })
        
        return jsonify({
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items
        }), 200
        
    except Exception as e:
        print(f"Error in bulk upload test runs: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/results/requirements', methods=['POST'])
def bulk_upload_requirements():
    """Bulk upload requirements"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('customerId') or not data.get('sourceSystem') or not data.get('events'):
            return jsonify({"error": "customerId, sourceSystem, and events are required"}), 400
        
        customer_id = data['customerId']
        source_system = data['sourceSystem']
        events = data['events']
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                if event.get('kind') != 'REQUIREMENT':
                    continue
                
                requirement_data = event.get('requirement', {})
                requirement_id = requirement_data.get('id')
                
                # Check if requirement already exists
                existing_requirement = db.get_requirement_by_id(requirement_id)
                if existing_requirement:
                    duplicates += 1
                    items.append({
                        'status': 'duplicate',
                        'requirementId': requirement_id,
                        'error': 'Requirement already exists'
                    })
                    continue
                
                # Create requirement data
                req_data = {
                    'requirement_id': requirement_id,
                    'title': requirement_data.get('title'),
                    'description': requirement_data.get('description'),
                    'component': requirement_data.get('component'),
                    'priority': requirement_data.get('priority'),
                    'status': requirement_data.get('status', 'Active'),
                    'jira_id': requirement_data.get('jiraId'),
                    'created_at': datetime.datetime.now()
                }
                
                if db.create_requirement(req_data):
                    accepted += 1
                    items.append({
                        'status': 'accepted',
                        'requirementId': requirement_id
                    })
                else:
                    failed += 1
                    items.append({
                        'status': 'failed',
                        'requirementId': requirement_id,
                        'error': 'Failed to create requirement'
                    })
                    
            except Exception as e:
                failed += 1
                items.append({
                    'status': 'failed',
                    'requirementId': event.get('requirement', {}).get('id'),
                    'error': str(e)
                })
        
        return jsonify({
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items
        }), 200
        
    except Exception as e:
        print(f"Error in bulk upload requirements: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/results/test-cases', methods=['POST'])
def bulk_upload_test_cases():
    """Bulk upload test cases"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('customerId') or not data.get('sourceSystem') or not data.get('events'):
            return jsonify({"error": "customerId, sourceSystem, and events are required"}), 400
        
        customer_id = data['customerId']
        source_system = data['sourceSystem']
        events = data['events']
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                if event.get('kind') != 'TEST_CASE':
                    continue
                
                test_case_data = event.get('testCase', {})
                test_case_id = test_case_data.get('id')
                
                # Check if test case already exists
                existing_test_case = db.get_test_case_by_id(test_case_id)
                if existing_test_case:
                    duplicates += 1
                    items.append({
                        'status': 'duplicate',
                        'testCaseId': test_case_id,
                        'error': 'Test case already exists'
                    })
                    continue
                
                # Create test case data - using exact database column names
                tc_data = {
                    'test_case_id': test_case_id,
                    'title': test_case_data.get('title'),
                    'type': test_case_data.get('type'),
                    'component': test_case_data.get('component'),
                    'requirement_id': test_case_data.get('requirementId'),
                    'status': test_case_data.get('status', 'Active'),
                    'created_by': test_case_data.get('createdBy', 'system'),
                    'created_at': datetime.datetime.now(),
                    'pre_condition': test_case_data.get('preCondition'),
                    'test_steps': test_case_data.get('testSteps'),
                    'expected_result': test_case_data.get('expectedResult'),
                    'uploaded_at': datetime.datetime.now()
                }
                
                if db.create_test_case(tc_data):
                    accepted += 1
                    items.append({
                        'status': 'accepted',
                        'testCaseId': test_case_id
                    })
                else:
                    failed += 1
                    items.append({
                        'status': 'failed',
                        'testCaseId': test_case_id,
                        'error': 'Failed to create test case'
                    })
                    
            except Exception as e:
                failed += 1
                items.append({
                    'status': 'failed',
                    'testCaseId': event.get('testCase', {}).get('id'),
                    'error': str(e)
                })
        
        return jsonify({
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items
        }), 200
        
    except Exception as e:
        print(f"Error in bulk upload test cases: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/results/defects', methods=['POST'])
def bulk_upload_defects():
    """Bulk upload defects"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('customerId') or not data.get('sourceSystem') or not data.get('events'):
            return jsonify({"error": "customerId, sourceSystem, and events are required"}), 400
        
        customer_id = data['customerId']
        source_system = data['sourceSystem']
        events = data['events']
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                if event.get('kind') != 'DEFECT':
                    continue
                
                defect_data = event.get('defect', {})
                defect_id = defect_data.get('id')
                
                # Check if defect already exists
                existing_defect = db.get_defect_by_id(defect_id)
                if existing_defect:
                    duplicates += 1
                    items.append({
                        'status': 'duplicate',
                        'defectId': defect_id,
                        'error': 'Defect already exists'
                    })
                    continue
                
                # Create defect data - using exact database column names
                d_data = {
                    'defect_id': defect_id,
                    'title': defect_data.get('title'),
                    'severity': defect_data.get('severity'),
                    'status': defect_data.get('status', 'Open'),
                    'test_case_id': defect_data.get('testCaseId'),
                    'reported_by': defect_data.get('reportedBy'),
                    'created_at': datetime.datetime.now(),
                    'fixed_at': defect_data.get('fixedAt')
                }
                
                if db.create_defect(d_data):
                    accepted += 1
                    items.append({
                        'status': 'accepted',
                        'defectId': defect_id
                    })
                else:
                    failed += 1
                    items.append({
                        'status': 'failed',
                        'defectId': defect_id,
                        'error': 'Failed to create defect'
                    })
                    
            except Exception as e:
                failed += 1
                items.append({
                    'status': 'failed',
                    'defectId': event.get('defect', {}).get('id'),
                    'error': str(e)
                })
        
        return jsonify({
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items
        }), 200
        
    except Exception as e:
        print(f"Error in bulk upload defects: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/results/test-type-summary', methods=['POST'])
def bulk_upload_test_type_summary():
    """Bulk upload test type summaries"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('customerId') or not data.get('sourceSystem') or not data.get('events'):
            return jsonify({"error": "customerId, sourceSystem, and events are required"}), 400
        
        customer_id = data['customerId']
        source_system = data['sourceSystem']
        events = data['events']
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                if event.get('kind') != 'TEST_TYPE_SUMMARY':
                    continue
                
                summary_data = event.get('summary', {})
                
                # Create summary data - using exact database column names
                s_data = {
                    'test_type': summary_data.get('testType'),
                    'metrics': summary_data.get('metrics'),
                    'expected': summary_data.get('expected'),
                    'actual': summary_data.get('actual'),
                    'status': summary_data.get('status'),
                    'test_date': summary_data.get('testDate')
                }
                
                if db.create_test_type_summary(s_data):
                    accepted += 1
                    items.append({
                        'status': 'accepted',
                        'testType': summary_data.get('testType')
                    })
                else:
                    failed += 1
                    items.append({
                        'status': 'failed',
                        'testType': summary_data.get('testType'),
                        'error': 'Failed to create test type summary'
                    })
                    
            except Exception as e:
                failed += 1
                items.append({
                    'status': 'failed',
                    'testType': event.get('summary', {}).get('testType'),
                    'error': str(e)
                })
        
        return jsonify({
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items
        }), 200
        
    except Exception as e:
        print(f"Error in bulk upload test type summary: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/results/transit-metrics', methods=['POST'])
def bulk_upload_transit_metrics():
    """Bulk upload transit metrics"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        if not data.get('customerId') or not data.get('sourceSystem') or not data.get('events'):
            return jsonify({"error": "customerId, sourceSystem, and events are required"}), 400
        
        customer_id = data['customerId']
        source_system = data['sourceSystem']
        events = data['events']
        
        accepted = 0
        duplicates = 0
        failed = 0
        items = []
        
        for event in events:
            try:
                if event.get('kind') != 'TRANSIT_METRIC':
                    continue
                
                metric_data = event.get('metric', {})
                date = metric_data.get('date')
                
                # Check if metric for this date already exists
                existing_metrics = db.get_all_transit_metrics()
                existing_dates = [m.get('date') for m in existing_metrics]
                if date in existing_dates:
                    duplicates += 1
                    items.append({
                        'status': 'duplicate',
                        'date': date,
                        'error': 'Metric for this date already exists'
                    })
                    continue
                
                # Create metric data - using exact database column names
                m_data = {
                    'date': date,
                    'fvm_transactions': metric_data.get('fvmTransactions'),
                    'gate_taps': metric_data.get('gateTaps'),
                    'bus_taps': metric_data.get('busTaps'),
                    'success_rate_gate': metric_data.get('successRateGate'),
                    'success_rate_bus': metric_data.get('successRateBus'),
                    'avg_response_time': metric_data.get('avgResponseTime'),
                    'defect_count': metric_data.get('defectCount'),
                    'notes': metric_data.get('notes')
                }
                
                if db.create_transit_metric(m_data):
                    accepted += 1
                    items.append({
                        'status': 'accepted',
                        'date': date
                    })
                else:
                    failed += 1
                    items.append({
                        'status': 'failed',
                        'date': date,
                        'error': 'Failed to create transit metric'
                    })
                    
            except Exception as e:
                failed += 1
                items.append({
                    'status': 'failed',
                    'date': event.get('metric', {}).get('date'),
                    'error': str(e)
                })
        
        return jsonify({
            'accepted': accepted,
            'duplicates': duplicates,
            'failed': failed,
            'items': items
        }), 200
        
    except Exception as e:
        print(f"Error in bulk upload transit metrics: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ROOT ROUTE
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API information"""
    return jsonify({
        "message": "Transit Management System Test Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoints": {
            "health_check": "/api/health",
            "health_check_v1": "/api/v1/health",
            "swagger_docs": "/api/docs",
            "api_endpoints": {
                "requirements": "/api/v1/requirements",
                "test_cases": "/api/v1/test-cases", 
                "test_runs": "/api/v1/test-runs",
                "defects": "/api/v1/defects",
                "test_type_summary": "/api/v1/test-type-summary",
                "transit_metrics": "/api/v1/transit-metrics"
            }
        }
    }), 200

# ============================================================================
# API HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "PostgreSQL"
    }), 200

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
            "unified_bulk_upload": "/api/v1/results",
            "individual_bulk_upload": {
                "test_runs": "/api/v1/results/test-runs",
                "requirements": "/api/v1/results/requirements",
                "test_cases": "/api/v1/results/test-cases",
                "defects": "/api/v1/results/defects",
                "test_type_summary": "/api/v1/results/test-type-summary",
                "transit_metrics": "/api/v1/results/transit-metrics"
            },
            "swagger_docs": "/api/docs"
        }
    }), 200

if __name__ == '__main__':
    # Get port from environment variable (Render sets PORT)
    port = int(os.environ.get('PORT', 5000))
    # Use 0.0.0.0 for production (Render), 127.0.0.1 for development
    host = '0.0.0.0' if os.environ.get('FLASK_ENV') == 'production' else '127.0.0.1'
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(host=host, port=port, debug=debug)
