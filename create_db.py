#!/usr/bin/env python3
"""
Database Creation Script for Reporting Application
Creates PostgreSQL database and tables using SQLAlchemy
"""

from database_postgresql import db, Base, engine

def create_database():
    """Create database tables"""
    try:
        # Drop all tables first to ensure clean slate
        Base.metadata.drop_all(bind=engine)
        print("🗑️ Dropped existing tables")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        print("📊 Tables created:")
        print("   - users")
        print("   - requirements")
        print("   - test_cases_structured")
        print("   - test_runs")
        print("   - defects")
        print("   - test_type_summary")
        print("   - transit_metrics_daily")
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating PostgreSQL Database Tables")
    print("=" * 50)
    create_database()