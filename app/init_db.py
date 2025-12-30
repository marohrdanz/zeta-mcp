#!/usr/bin/env python3
"""
Database initialization script for Task Manager.

This script creates the database schema and can be used for initial setup
or to reset the database.
"""

import asyncio
import sys
from database import Base, engine

async def init_database():
    """Initialize the database by creating all tables."""
    print("Initializing database...")
    try:
        async with engine.begin() as conn:
            # Drop all tables (use with caution!)
            # await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        print("✓ Database initialized successfully!")
        print("Tables created:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
        
        return True
    except Exception as e:
        print(f"✗ Error initializing database: {e}", file=sys.stderr)
        return False

async def reset_database():
    """Reset the database by dropping and recreating all tables."""
    print("Resetting database (WARNING: This will delete all data!)...")
    try:
        async with engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            print("✓ Dropped all tables")
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("✓ Created all tables")
        
        print("✓ Database reset successfully!")
        return True
    except Exception as e:
        print(f"✗ Error resetting database: {e}", file=sys.stderr)
        return False

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize or reset the Task Manager database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the database (drops all tables and data)"
    )
    args = parser.parse_args()
    
    if args.reset:
        response = input("Are you sure you want to reset the database? This will delete ALL data! (yes/no): ")
        if response.lower() != "yes":
            print("Database reset cancelled.")
            sys.exit(0)
        success = asyncio.run(reset_database())
    else:
        success = asyncio.run(init_database())
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
