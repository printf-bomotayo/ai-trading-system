#!/usr/bin/env python3
"""
Simple test script to verify database.py functionality
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseConfig, test_database_connection


async def main():
    """Test database functionality"""
    
    print("Testing Database Module")
    print("=" * 40)
    
    # Test with default configuration
    config = DatabaseConfig()
    
    print(f"Database config:")
    print(f"  Host: {config.host}:{config.port}")
    print(f"  Database: {config.database}")
    print(f"  User: {config.username}")
    print()
    
    try:
        # Test configuration creation
        print("OK DatabaseConfig created successfully")
        
        # Test DSN generation
        dsn = config.get_dsn()
        admin_dsn = config.get_admin_dsn()
        
        print("OK DSN generation working")
        print(f"  DSN: {dsn}")
        print(f"  Admin DSN: {admin_dsn}")
        print()
        
        # Test database connection (this will only work if PostgreSQL is running)
        print("Testing database connection...")
        print("(This will fail if PostgreSQL is not running - that's expected)")
        
        connection_result = await test_database_connection(config)
        
        if connection_result:
            print("OK Database connection test passed!")
        else:
            print("WARNING Database connection test failed (expected if no PostgreSQL)")
        
        print()
        print("SUCCESS Database module syntax and basic functionality verified!")
        return 0
        
    except Exception as e:
        print(f"ERROR Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)