# dbapi.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import datetime
import os
import bcrypt
import jwt
from functools import wraps
from typing import Optional

# Lazy database import to avoid startup issues
def get_db():
    """Get database instance with lazy initialization"""
    from database_postgresql import db
    return db

def get_engine():
    """Get database engine with lazy initialization"""
    from database_postgresql import get_engine
    return get_engine()

def get_base():
    """Get SQLAlchemy Base with lazy initialization"""
    from database_postgresql import Base
    return Base

app = Flask(__name__)

# CORS configuration
CORS(app, origins=["https://reporting-frontend-bhrm.onrender.com", "http://localhost:3000", "http://localhost:3001"], supports_credentials=True)

# JWT Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Swagger configuration
SWAGGER_URL = '/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Reporting Application API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Create swagger.json
@app.route('/static/swagger.json')
def create_swagger_docs():
    swagger_doc = {
        "openapi": "3.0.0",
        "info": {
            "title": "Reporting Application API",
            "version": "1.0.0",
            "description": "REST API for Transit Management System Test Dashboard"
        },
        "servers": [
            {
                "url": "https://reporting-backend-kpoz.onrender.com",
                "description": "Production server"
            }
        ],
        "paths": {
            "/api/signup": {
                "post": {
                    "tags": ["auth"],
                    "summary": "User signup",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"},
                                        "email": {"type": "string"},
                                        "firstName": {"type": "string"},
                                        "lastName": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "User created successfully"},
                        "409": {"description": "User already exists"},
                        "500": {"description": "Internal server error"}
                    }
                }
            },
            "/api/login": {
                "post": {
                    "tags": ["auth"],
                    "summary": "User login",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Login successful"},
                        "401": {"description": "Invalid credentials"},
                        "500": {"description": "Internal server error"}
                    }
                }
            },
            "/admin/db-info": {
                "get": {
                    "tags": ["admin"],
                    "summary": "Get database information",
                    "responses": {
                        "200": {"description": "Database info retrieved"}
                    }
                }
            },
            "/admin/db-test": {
                "get": {
                    "tags": ["admin"],
                    "summary": "Test database connection",
                    "responses": {
                        "200": {"description": "Database connection test result"}
                    }
                }
            },
            "/admin/schema-info": {
                "get": {
                    "tags": ["admin"],
                    "summary": "Get database schema information",
                    "responses": {
                        "200": {"description": "Schema information retrieved"}
                    }
                }
            },
            "/admin/generate-data": {
                "post": {
                    "tags": ["admin"],
                    "summary": "Generate test data",
                    "responses": {
                        "200": {"description": "Data generated successfully"},
                        "500": {"description": "Error generating data"}
                    }
                }
            },
            "/admin/reset-db": {
                "post": {
                    "tags": ["admin"],
                    "summary": "Reset database schema",
                    "responses": {
                        "200": {"description": "Database reset successfully"},
                        "500": {"description": "Error resetting database"}
                    }
                }
            },
            "/admin/delete-db": {
                "post": {
                    "tags": ["admin"],
                    "summary": "Delete all data",
                    "responses": {
                        "200": {"description": "Data deleted successfully"},
                        "500": {"description": "Error deleting data"}
                    }
                }
            }
        },
        "tags": [
            {"name": "auth", "description": "Authentication endpoints"},
            {"name": "admin", "description": "Administrative endpoints"}
        ]
    }
    return jsonify(swagger_doc)

# JWT token verification decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            current_user = get_db().get_user_by_email(data['sub'])
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Auth endpoints
@app.route('/api/signup', methods=['POST'])
def signup():
    """User signup endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'password', 'email', 'firstName', 'lastName']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        existing_user = get_db().get_user_by_username(data['username'])
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
        
        existing_email = get_db().get_user_by_email(data['email'])
        if existing_email:
            return jsonify({'error': 'Email already exists'}), 409
        
        # Hash password
        hashed_password = hash_password(data['password'])
        
        # Create user data
        user_data = {
            'username': data['username'],
            'password': hashed_password,
            'email': data['email'],
            'first_name': data['firstName'],
            'last_name': data['lastName']
        }
        
        # Create user
        success = get_db().create_user(user_data)
        if not success:
            return jsonify({'error': 'Failed to create user'}), 500
        
        # Create access token
        access_token = create_access_token(
            data={"sub": data['email']},
            expires_delta=datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return jsonify({
            'message': 'User created successfully',
            'token': access_token,
            'user': {
                'username': data['username'],
                'email': data['email'],
                'first_name': data['firstName'],
                'last_name': data['lastName'],
                'country_code': None,
                'phone': None
            }
        }), 201
        
    except Exception as e:
        print(f"Signup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Get user by username
        user = get_db().get_user_by_username(data['username'])
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not verify_password(data['password'], user['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user['email']},
            expires_delta=datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'user': {
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'country_code': None,
                'phone': None
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Login failed'}), 500

# Admin endpoints
@app.route('/admin/db-info', methods=['GET'])
def get_db_info():
    """Get database information"""
    try:
        engine = get_engine()
        db_url = str(engine.url)
        return jsonify({
            "status": "success",
            "database_type": "PostgreSQL" if "postgresql" in db_url else "SQLite",
            "connection_string": db_url.split("@")[0] + "@***" if "@" in db_url else db_url
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin/db-test', methods=['GET'])
def test_db_connection():
    """Test database connection"""
    try:
        engine = get_engine()
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            return jsonify({
                "status": "success",
                "database_type": "PostgreSQL",
                "version": version
            }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin/schema-info', methods=['GET'])
def get_schema_info():
    """Get database schema information"""
    try:
        engine = get_engine()
        from sqlalchemy import text
        with engine.connect() as conn:
            # Get users table schema
            users_result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """))
            users_schema = [{"column": row[0], "type": row[1], "nullable": row[2]} for row in users_result]
            
            # Get other tables schema
            tables_result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in tables_result]
            
            return jsonify({
                "status": "success",
                "users_schema": users_schema,
                "all_tables": tables
            }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin/generate-data', methods=['POST'])
def generate_data():
    """Generate test data using pscript.py"""
    try:
        # Import and run pscript.py
        import pscript
        pscript.main()
        return jsonify({"status": "success", "message": "Test data generated successfully"}), 200
    except Exception as e:
        print(f"Data generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin/reset-db', methods=['POST'])
def reset_database():
    """Reset database schema"""
    try:
        Base = get_base()
        engine = get_engine()
        print("Resetting database schema...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return jsonify({"status": "success", "message": "Database schema reset successfully"}), 200
    except Exception as e:
        print(f"Reset database error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin/delete-db', methods=['POST'])
def delete_database():
    """Delete all data from database"""
    try:
        engine = get_engine()
        from sqlalchemy import text
        
        # Get all tables
        with engine.connect() as conn:
            tables_result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """))
            tables = [row[0] for row in tables_result]
            
            # Delete all data from each table
            for table in tables:
                conn.execute(text(f"DELETE FROM {table}"))
            
            conn.commit()
        
        return jsonify({"status": "success", "message": "All data deleted successfully"}), 200
    except Exception as e:
        print(f"Delete database error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# Health check endpoints
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        engine = get_engine()
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }), 500

@app.route('/api/startup', methods=['GET'])
def startup_test():
    """Basic startup test - no database required"""
    return jsonify({
        "status": "success",
        "message": "Flask app is running",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

# Test endpoints
@app.route('/api/test-db', methods=['GET'])
def test_database():
    """Test database operations"""
    try:
        # Test connection
        engine = get_engine()
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Test user creation
        test_user_data = {
            'username': 'test_user_db',
            'password': 'testpass',
            'email': 'test@db.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        success = get_db().create_user(test_user_data)
        
        return jsonify({
            "database_connection": "working",
            "user_creation": "success" if success else "failed"
        }), 200
    except Exception as e:
        return jsonify({
            "database_connection": "failed",
            "user_creation": "failed",
            "error": str(e)
        }), 500

# Check database schema endpoint
@app.route('/api/check-schema', methods=['GET'])
def check_schema():
    """Check if database tables exist"""
    try:
        engine = get_engine()
        
        # Check if users table exists
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            """))
            tables = [row[0] for row in result]
            
            if 'users' in tables:
                # Check table structure
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position
                """))
                columns = [dict(row._mapping) for row in result]
                
                return jsonify({
                    "status": "success",
                    "users_table_exists": True,
                    "columns": columns
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "users_table_exists": False,
                    "message": "Users table does not exist"
                }), 500
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Schema check failed: {str(e)}"
        }), 500

# ============================================================================
# COMPLETE CRUD ENDPOINTS FOR ALL TABLES (CRM-STYLE)
# ============================================================================

# Requirements CRUD
@app.route('/api/requirements', methods=['GET'])
def get_requirements():
    """Get all requirements"""
    try:
        requirements = get_db().get_all_requirements()
        return jsonify(requirements), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/requirements', methods=['POST'])
def create_requirement():
    """Create a new requirement"""
    try:
        data = request.get_json()
        success = get_db().create_requirement(data)
        if success:
            return jsonify({"message": "Requirement created successfully"}), 201
        else:
            return jsonify({"error": "Failed to create requirement"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/requirements/<requirement_id>', methods=['GET'])
def get_requirement(requirement_id):
    """Get a specific requirement"""
    try:
        requirement = get_db().get_requirement_by_id(requirement_id)
        if requirement:
            return jsonify(requirement), 200
        else:
            return jsonify({"error": "Requirement not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/requirements/<requirement_id>', methods=['PUT'])
def update_requirement(requirement_id):
    """Update a requirement"""
    try:
        data = request.get_json()
        success = get_db().update_requirement(requirement_id, data)
        if success:
            return jsonify({"message": "Requirement updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update requirement"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/requirements/<requirement_id>', methods=['DELETE'])
def delete_requirement(requirement_id):
    """Delete a requirement"""
    try:
        success = get_db().delete_requirement(requirement_id)
        if success:
            return jsonify({"message": "Requirement deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete requirement"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Test Cases CRUD
@app.route('/api/testcases', methods=['GET'])
def get_testcases():
    """Get all test cases"""
    try:
        testcases = get_db().get_all_test_cases()
        return jsonify(testcases), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testcases', methods=['POST'])
def create_testcase():
    """Create a new test case"""
    try:
        data = request.get_json()
        success = get_db().create_test_case(data)
        if success:
            return jsonify({"message": "Test case created successfully"}), 201
        else:
            return jsonify({"error": "Failed to create test case"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testcases/<testcase_id>', methods=['GET'])
def get_testcase(testcase_id):
    """Get a specific test case"""
    try:
        testcase = get_db().get_test_case_by_id(testcase_id)
        if testcase:
            return jsonify(testcase), 200
        else:
            return jsonify({"error": "Test case not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testcases/<testcase_id>', methods=['PUT'])
def update_testcase(testcase_id):
    """Update a test case"""
    try:
        data = request.get_json()
        success = get_db().update_test_case(testcase_id, data)
        if success:
            return jsonify({"message": "Test case updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update test case"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testcases/<testcase_id>', methods=['DELETE'])
def delete_testcase(testcase_id):
    """Delete a test case"""
    try:
        success = get_db().delete_test_case(testcase_id)
        if success:
            return jsonify({"message": "Test case deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete test case"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Test Runs CRUD
@app.route('/api/testruns', methods=['GET'])
def get_testruns():
    """Get all test runs"""
    try:
        testruns = get_db().get_all_test_runs()
        return jsonify(testruns), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testruns', methods=['POST'])
def create_testrun():
    """Create a new test run"""
    try:
        data = request.get_json()
        success = get_db().create_test_run(data)
        if success:
            return jsonify({"message": "Test run created successfully"}), 201
        else:
            return jsonify({"error": "Failed to create test run"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testruns/<run_id>', methods=['GET'])
def get_testrun(run_id):
    """Get a specific test run"""
    try:
        testrun = get_db().get_test_run_by_id(run_id)
        if testrun:
            return jsonify(testrun), 200
        else:
            return jsonify({"error": "Test run not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testruns/<run_id>', methods=['PUT'])
def update_testrun(run_id):
    """Update a test run"""
    try:
        data = request.get_json()
        success = get_db().update_test_run(run_id, data)
        if success:
            return jsonify({"message": "Test run updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update test run"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testruns/<run_id>', methods=['DELETE'])
def delete_testrun(run_id):
    """Delete a test run"""
    try:
        success = get_db().delete_test_run(run_id)
        if success:
            return jsonify({"message": "Test run deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete test run"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Defects CRUD
@app.route('/api/defects', methods=['GET'])
def get_defects():
    """Get all defects"""
    try:
        defects = get_db().get_all_defects()
        return jsonify(defects), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/defects', methods=['POST'])
def create_defect():
    """Create a new defect"""
    try:
        data = request.get_json()
        success = get_db().create_defect(data)
        if success:
            return jsonify({"message": "Defect created successfully"}), 201
        else:
            return jsonify({"error": "Failed to create defect"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/defects/<defect_id>', methods=['GET'])
def get_defect(defect_id):
    """Get a specific defect"""
    try:
        defect = get_db().get_defect_by_id(defect_id)
        if defect:
            return jsonify(defect), 200
        else:
            return jsonify({"error": "Defect not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/defects/<defect_id>', methods=['PUT'])
def update_defect(defect_id):
    """Update a defect"""
    try:
        data = request.get_json()
        success = get_db().update_defect(defect_id, data)
        if success:
            return jsonify({"message": "Defect updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update defect"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/defects/<defect_id>', methods=['DELETE'])
def delete_defect(defect_id):
    """Delete a defect"""
    try:
        success = get_db().delete_defect(defect_id)
        if success:
            return jsonify({"message": "Defect deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete defect"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Test Type Summary CRUD
@app.route('/api/testtypesummary', methods=['GET'])
def get_testtypesummary():
    """Get all test type summaries"""
    try:
        summaries = get_db().get_all_test_type_summaries()
        return jsonify(summaries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testtypesummary', methods=['POST'])
def create_testtypesummary():
    """Create a new test type summary"""
    try:
        data = request.get_json()
        success = get_db().create_test_type_summary(data)
        if success:
            return jsonify({"message": "Test type summary created successfully"}), 201
        else:
            return jsonify({"error": "Failed to create test type summary"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testtypesummary/<summary_id>', methods=['GET'])
def get_testtypesummary_by_id(summary_id):
    """Get a specific test type summary"""
    try:
        summary = get_db().get_test_type_summary_by_id(summary_id)
        if summary:
            return jsonify(summary), 200
        else:
            return jsonify({"error": "Test type summary not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testtypesummary/<summary_id>', methods=['PUT'])
def update_testtypesummary(summary_id):
    """Update a test type summary"""
    try:
        data = request.get_json()
        success = get_db().update_test_type_summary(summary_id, data)
        if success:
            return jsonify({"message": "Test type summary updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update test type summary"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/testtypesummary/<summary_id>', methods=['DELETE'])
def delete_testtypesummary(summary_id):
    """Delete a test type summary"""
    try:
        success = get_db().delete_test_type_summary(summary_id)
        if success:
            return jsonify({"message": "Test type summary deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete test type summary"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Transit Metrics Daily CRUD
@app.route('/api/transitmetricsdaily', methods=['GET'])
def get_transitmetricsdaily():
    """Get all transit metrics daily"""
    try:
        metrics = get_db().get_all_transit_metrics_daily()
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transitmetricsdaily', methods=['POST'])
def create_transitmetricsdaily():
    """Create a new transit metrics daily"""
    try:
        data = request.get_json()
        success = get_db().create_transit_metrics_daily(data)
        if success:
            return jsonify({"message": "Transit metrics daily created successfully"}), 201
        else:
            return jsonify({"error": "Failed to create transit metrics daily"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transitmetricsdaily/<metric_id>', methods=['GET'])
def get_transitmetricsdaily_by_id(metric_id):
    """Get a specific transit metrics daily"""
    try:
        metric = get_db().get_transit_metrics_daily_by_id(metric_id)
        if metric:
            return jsonify(metric), 200
        else:
            return jsonify({"error": "Transit metrics daily not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transitmetricsdaily/<metric_id>', methods=['PUT'])
def update_transitmetricsdaily(metric_id):
    """Update a transit metrics daily"""
    try:
        data = request.get_json()
        success = get_db().update_transit_metrics_daily(metric_id, data)
        if success:
            return jsonify({"message": "Transit metrics daily updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update transit metrics daily"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transitmetricsdaily/<metric_id>', methods=['DELETE'])
def delete_transitmetricsdaily(metric_id):
    """Delete a transit metrics daily"""
    try:
        success = get_db().delete_transit_metrics_daily(metric_id)
        if success:
            return jsonify({"message": "Transit metrics daily deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete transit metrics daily"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# DASHBOARD ENDPOINTS (EXISTING)
# ============================================================================

@app.route('/api/me', methods=['GET', 'OPTIONS'])
def get_current_user():
    """Get current user information"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Decode token
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = data['sub']
        
        # Get user from database
        user = get_db().get_user_by_email(user_email)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'country_code': None,
                'phone': None
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': 'Authentication failed'}), 500

# Dashboard endpoints are now handled by the CRUD endpoints above
# GET /api/requirements, /api/testcases, /api/testruns, /api/defects, 
# /api/testtypesummary, /api/transitmetricsdaily are all available

if __name__ == '__main__':
    try:
        # Try to create tables on startup
        Base = get_base()
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not create database tables on startup: {e}")
        print("   Tables will be created when first accessed")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
