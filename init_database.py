#!/usr/bin/env python3
"""
Database initialization script for Reporting Backend
This script ensures all database tables are created properly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database components
from database_postgresql import Base, engine

def init_database():
    """Initialize the database with all required tables"""
    try:
        print("🚀 Initializing database...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        print("📋 Created tables:")
        
        # List all tables
        inspector = engine.dialect.inspector(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            print(f"   - {table}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("🎉 Database initialization completed successfully!")
        sys.exit(0)
    else:
        print("💥 Database initialization failed!")
        sys.exit(1)
