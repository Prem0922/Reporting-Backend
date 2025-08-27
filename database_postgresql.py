import os
import json
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/reporting_db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define SQLAlchemy models
class User(Base):
    __tablename__ = "users"
    
    username = Column(String, primary_key=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    country_code = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

class Requirement(Base):
    __tablename__ = "requirements"
    
    requirement_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    component = Column(String)
    priority = Column(String)
    status = Column(String)
    jira_id = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

class TestCase(Base):
    __tablename__ = "test_cases_structured"
    
    test_case_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    type = Column(String)
    component = Column(String)
    requirement_id = Column(String)
    status = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime)
    pre_condition = Column(Text)
    test_steps = Column(Text)
    expected_result = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class TestRun(Base):
    __tablename__ = "test_runs"
    
    run_id = Column(String, primary_key=True)
    test_run_id = Column(String, nullable=False)
    customer_id = Column(Integer, nullable=False)
    source_system = Column(String, nullable=False)
    test_case_id = Column(String)
    execution_date = Column(String)
    result = Column(String)
    observed_time = Column(Integer)
    executed_by = Column(String)
    remarks = Column(Text)
    artifacts = Column(Text)

class Defect(Base):
    __tablename__ = "defects"
    
    defect_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    severity = Column(String)
    status = Column(String)
    test_case_id = Column(String)
    reported_by = Column(String)
    created_at = Column(DateTime)
    fixed_at = Column(DateTime)

class TestTypeSummary(Base):
    __tablename__ = "test_type_summary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_type = Column(String, nullable=False)
    metrics = Column(String, nullable=False)
    expected = Column(String)
    actual = Column(String)
    status = Column(String)
    test_date = Column(String)

class TransitMetric(Base):
    __tablename__ = "transit_metrics_daily"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    fvm_transactions = Column(Integer)
    gate_taps = Column(Integer)
    bus_taps = Column(Integer)
    success_rate_gate = Column(Float)
    success_rate_bus = Column(Float)
    avg_response_time = Column(Integer)
    defect_count = Column(Integer)
    notes = Column(Text)

class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        # Don't auto-initialize database - let create_db.py handle it
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def init_database(self):
        """Initialize the database with all required tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
    
    def ensure_tables_exist(self):
        """Check if tables exist, create if they don't"""
        try:
            Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            print(f"❌ Error ensuring tables exist: {e}")
    
    # User operations
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user"""
        try:
            session = self.get_session()
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.close()
            return True
        except SQLAlchemyError:
            session.rollback()
            session.close()
            return False
        except Exception as e:
            print(f"Error creating user: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            session = self.get_session()
            user = session.query(User).filter(User.username == username).first()
            session.close()
            
            if user:
                return {
                    'username': user.username,
                    'password': user.password,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'country_code': user.country_code,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            session.close()
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            session = self.get_session()
            user = session.query(User).filter(User.email == email).first()
            session.close()
            
            if user:
                return {
                    'username': user.username,
                    'password': user.password,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'country_code': user.country_code,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            session.close()
            return None
    
    def update_user_password(self, username: str, new_password: str) -> bool:
        """Update user password"""
        try:
            session = self.get_session()
            user = session.query(User).filter(User.username == username).first()
            if user:
                user.password = new_password
                session.commit()
                session.close()
                return True
            session.close()
            return False
        except Exception as e:
            print(f"Error updating password: {e}")
            session.rollback()
            session.close()
            return False
    
    # Requirements operations
    def create_requirement(self, requirement_data: Dict[str, Any]) -> bool:
        """Create a new requirement"""
        try:
            session = self.get_session()
            requirement = Requirement(**requirement_data)
            session.add(requirement)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error creating requirement: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_all_requirements(self) -> List[Dict[str, Any]]:
        """Get all requirements"""
        try:
            session = self.get_session()
            requirements = session.query(Requirement).order_by(Requirement.created_at.desc()).all()
            session.close()
            
            return [{
                'requirement_id': req.requirement_id,
                'title': req.title,
                'description': req.description,
                'component': req.component,
                'priority': req.priority,
                'status': req.status,
                'jira_id': req.jira_id,
                'created_at': req.created_at.isoformat() if req.created_at else None
            } for req in requirements]
        except Exception as e:
            print(f"Error getting requirements: {e}")
            session.close()
            return []
    
    def get_requirement_by_id(self, requirement_id: str) -> Optional[Dict[str, Any]]:
        """Get requirement by ID"""
        try:
            session = self.get_session()
            requirement = session.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
            session.close()
            
            if requirement:
                return {
                    'requirement_id': requirement.requirement_id,
                    'title': requirement.title,
                    'description': requirement.description,
                    'component': requirement.component,
                    'priority': requirement.priority,
                    'status': requirement.status,
                    'jira_id': requirement.jira_id,
                    'created_at': requirement.created_at.isoformat() if requirement.created_at else None
                }
            return None
        except Exception as e:
            print(f"Error getting requirement: {e}")
            session.close()
            return None
    
    # Test Cases operations
    def create_test_case(self, test_case_data: Dict[str, Any]) -> bool:
        """Create a new test case"""
        try:
            session = self.get_session()
            test_case = TestCase(**test_case_data)
            session.add(test_case)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error creating test case: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_all_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases"""
        try:
            session = self.get_session()
            test_cases = session.query(TestCase).order_by(TestCase.created_at.desc()).all()
            session.close()
            
            return [{
                'Test_Case_ID': tc.test_case_id,
                'Title': tc.title,
                'Type': tc.type,
                'Component': tc.component,
                'Requirement_ID': tc.requirement_id,
                'Status': tc.status,
                'Created_by': tc.created_by,
                'Created_at': tc.created_at.isoformat() if tc.created_at else None,
                'PreCondition': tc.pre_condition,
                'Test_Steps': tc.test_steps,
                'Expected_Result': tc.expected_result,
                'Uploaded_At': tc.uploaded_at.isoformat() if tc.uploaded_at else None
            } for tc in test_cases]
        except Exception as e:
            print(f"Error getting test cases: {e}")
            session.close()
            return []
    
    def get_test_case_by_id(self, test_case_id: str) -> Optional[Dict[str, Any]]:
        """Get test case by ID"""
        try:
            session = self.get_session()
            test_case = session.query(TestCase).filter(TestCase.test_case_id == test_case_id).first()
            session.close()
            
            if test_case:
                return {
                    'Test_Case_ID': test_case.test_case_id,
                    'Title': test_case.title,
                    'Type': test_case.type,
                    'Component': test_case.component,
                    'Requirement_ID': test_case.requirement_id,
                    'Status': test_case.status,
                    'Created_by': test_case.created_by,
                    'Created_at': test_case.created_at.isoformat() if test_case.created_at else None,
                    'PreCondition': test_case.pre_condition,
                    'Test_Steps': test_case.test_steps,
                    'Expected_Result': test_case.expected_result,
                    'Uploaded_At': test_case.uploaded_at.isoformat() if test_case.uploaded_at else None
                }
            return None
        except Exception as e:
            print(f"Error getting test case: {e}")
            session.close()
            return None
    
    def get_test_cases_by_requirement(self, requirement_id: str) -> List[Dict[str, Any]]:
        """Get test cases by requirement ID"""
        try:
            session = self.get_session()
            test_cases = session.query(TestCase).filter(TestCase.requirement_id == requirement_id).all()
            session.close()
            
            return [{
                'Test_Case_ID': tc.test_case_id,
                'Title': tc.title,
                'Type': tc.type,
                'Component': tc.component,
                'Requirement_ID': tc.requirement_id,
                'Status': tc.status,
                'Created_by': tc.created_by,
                'Created_at': tc.created_at.isoformat() if tc.created_at else None,
                'PreCondition': tc.pre_condition,
                'Test_Steps': tc.test_steps,
                'Expected_Result': tc.expected_result,
                'Uploaded_At': tc.uploaded_at.isoformat() if tc.uploaded_at else None
            } for tc in test_cases]
        except Exception as e:
            print(f"Error getting test cases by requirement: {e}")
            session.close()
            return []
    
    def get_test_cases_with_description(self) -> List[Dict[str, Any]]:
        """Get test cases with requirement descriptions"""
        try:
            session = self.get_session()
            # Join query to get requirement descriptions
            result = session.execute(text("""
                SELECT tc.*, r.description as requirement_description 
                FROM test_cases_structured tc 
                LEFT JOIN requirements r ON tc.Requirement_ID = r.requirement_id
                ORDER BY tc.Created_At DESC
            """))
            session.close()
            
            return [dict(row._mapping) for row in result]
        except Exception as e:
            print(f"Error getting test cases with description: {e}")
            session.close()
            return []
    
    # Test Runs operations
    def create_test_run(self, test_run_data: Dict[str, Any]) -> bool:
        """Create a new test run"""
        try:
            session = self.get_session()
            test_run = TestRun(**test_run_data)
            session.add(test_run)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error creating test run: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_all_test_runs(self) -> List[Dict[str, Any]]:
        """Get all test runs"""
        try:
            session = self.get_session()
            test_runs = session.query(TestRun).order_by(TestRun.execution_date.desc()).all()
            session.close()
            
            return [{
                'run_id': tr.run_id,
                'test_run_id': tr.test_run_id,
                'customer_id': tr.customer_id,
                'source_system': tr.source_system,
                'test_case_id': tr.test_case_id,
                'execution_date': tr.execution_date,
                'result': tr.result,
                'observed_time': tr.observed_time,
                'executed_by': tr.executed_by,
                'remarks': tr.remarks,
                'artifacts': tr.artifacts
            } for tr in test_runs]
        except Exception as e:
            print(f"Error getting test runs: {e}")
            session.close()
            return []
    
    def get_test_runs_by_run_id(self, test_run_id: str) -> List[Dict[str, Any]]:
        """Get all test cases for a specific test run"""
        try:
            session = self.get_session()
            test_runs = session.query(TestRun).filter(TestRun.test_run_id == test_run_id).all()
            session.close()
            
            return [{
                'run_id': tr.run_id,
                'test_run_id': tr.test_run_id,
                'customer_id': tr.customer_id,
                'source_system': tr.source_system,
                'test_case_id': tr.test_case_id,
                'execution_date': tr.execution_date,
                'result': tr.result,
                'observed_time': tr.observed_time,
                'executed_by': tr.executed_by,
                'remarks': tr.remarks,
                'artifacts': tr.artifacts
            } for tr in test_runs]
        except Exception as e:
            print(f"Error getting test runs by run ID: {e}")
            session.close()
            return []
    
    def get_test_runs_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get all test runs for a customer"""
        try:
            session = self.get_session()
            test_runs = session.query(TestRun).filter(TestRun.customer_id == customer_id).order_by(TestRun.execution_date.desc()).all()
            session.close()
            
            return [{
                'run_id': tr.run_id,
                'test_run_id': tr.test_run_id,
                'customer_id': tr.customer_id,
                'source_system': tr.source_system,
                'test_case_id': tr.test_case_id,
                'execution_date': tr.execution_date,
                'result': tr.result,
                'observed_time': tr.observed_time,
                'executed_by': tr.executed_by,
                'remarks': tr.remarks,
                'artifacts': tr.artifacts
            } for tr in test_runs]
        except Exception as e:
            print(f"Error getting test runs by customer: {e}")
            session.close()
            return []
    
    # Defects operations
    def create_defect(self, defect_data: Dict[str, Any]) -> bool:
        """Create a new defect"""
        try:
            session = self.get_session()
            defect = Defect(**defect_data)
            session.add(defect)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error creating defect: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_all_defects(self) -> List[Dict[str, Any]]:
        """Get all defects"""
        try:
            session = self.get_session()
            defects = session.query(Defect).order_by(Defect.created_at.desc()).all()
            session.close()
            
            return [{
                'DefectID': d.defect_id,
                'Title': d.title,
                'Severity': d.severity,
                'Status': d.status,
                'Test_Case_ID': d.test_case_id,
                'reported_by': d.reported_by,
                'created_at': d.created_at.isoformat() if d.created_at else None,
                'fixed_at': d.fixed_at.isoformat() if d.fixed_at else None
            } for d in defects]
        except Exception as e:
            print(f"Error getting defects: {e}")
            session.close()
            return []
    
    # Test Type Summary operations
    def create_test_type_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Create a new test type summary"""
        try:
            session = self.get_session()
            summary = TestTypeSummary(**summary_data)
            session.add(summary)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error creating test type summary: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_all_test_type_summary(self) -> List[Dict[str, Any]]:
        """Get all test type summaries"""
        try:
            session = self.get_session()
            summaries = session.query(TestTypeSummary).order_by(TestTypeSummary.test_date.desc()).all()
            session.close()
            
            return [{
                'id': s.id,
                'Test_Type': s.test_type,
                'Metrics': s.metrics,
                'Expected': s.expected,
                'Actual': s.actual,
                'Status': s.status,
                'Test_Date': s.test_date
            } for s in summaries]
        except Exception as e:
            print(f"Error getting test type summaries: {e}")
            session.close()
            return []
    
    # Transit Metrics operations
    def create_transit_metric(self, metric_data: Dict[str, Any]) -> bool:
        """Create a new transit metric"""
        try:
            session = self.get_session()
            metric = TransitMetric(**metric_data)
            session.add(metric)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error creating transit metric: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_all_transit_metrics(self) -> List[Dict[str, Any]]:
        """Get all transit metrics"""
        try:
            session = self.get_session()
            metrics = session.query(TransitMetric).order_by(TransitMetric.date.desc()).all()
            session.close()
            
            return [{
                'id': m.id,
                'Date': m.date,
                'FVM_Transactions': m.fvm_transactions,
                'Gate_Taps': m.gate_taps,
                'Bus_Taps': m.bus_taps,
                'Success_Rate_Gate': m.success_rate_gate,
                'Success_Rate_Bus': m.success_rate_bus,
                'Avg_Response_Time': m.avg_response_time,
                'Defect_Count': m.defect_count,
                'Notes': m.notes
            } for m in metrics]
        except Exception as e:
            print(f"Error getting transit metrics: {e}")
            session.close()
            return []
    
    # Bulk operations
    def bulk_create_requirements(self, requirements: List[Dict[str, Any]]) -> int:
        """Create multiple requirements"""
        success_count = 0
        for req in requirements:
            if self.create_requirement(req):
                success_count += 1
        return success_count
    
    def bulk_create_test_cases(self, test_cases: List[Dict[str, Any]]) -> int:
        """Create multiple test cases"""
        success_count = 0
        for tc in test_cases:
            if self.create_test_case(tc):
                success_count += 1
        return success_count
    
    def bulk_create_test_runs(self, test_runs: List[Dict[str, Any]]) -> int:
        """Create multiple test runs"""
        success_count = 0
        for tr in test_runs:
            if self.create_test_run(tr):
                success_count += 1
        return success_count
    
    def bulk_create_defects(self, defects: List[Dict[str, Any]]) -> int:
        """Create multiple defects"""
        success_count = 0
        for defect in defects:
            if self.create_defect(defect):
                success_count += 1
        return success_count
    
    def bulk_create_test_type_summaries(self, summaries: List[Dict[str, Any]]) -> int:
        """Create multiple test type summaries"""
        success_count = 0
        for summary in summaries:
            if self.create_test_type_summary(summary):
                success_count += 1
        return success_count
    
    def bulk_create_transit_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """Create multiple transit metrics"""
        success_count = 0
        for metric in metrics:
            if self.create_transit_metric(metric):
                success_count += 1
        return success_count

# Global database instance
db = DatabaseManager()
