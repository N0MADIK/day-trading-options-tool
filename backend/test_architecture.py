#!/usr/bin/env python3
"""
Simple test script to verify the new architecture setup
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if we can import the basic modules"""
    try:
        print("Testing basic imports...")
        
        # Test core imports
        from app.core.config import settings
        print(f"✓ Config loaded: {settings.app_name}")
        
        # Test domain imports
        from app.domain.errors import NotFoundError, ConflictError
        print("✓ Domain errors imported")
        
        from app.domain.models import TickerWatchlist, OptionWatchlist
        print("✓ Domain models imported")
        
        # Test schemas
        from app.schemas.watchlist import TickerWatchlistCreate, OptionWatchlistCreate
        print("✓ Schemas imported")
        
        print("\n🎉 All basic imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_architecture():
    """Test the architecture pattern"""
    try:
        print("\nTesting architecture pattern...")
        
        # Test service creation (without database)
        from app.services.watchlist_service import WatchlistService
        print("✓ Service class imported")
        
        # Test repository interfaces
        from app.repositories.watchlist_repo import TickerWatchlistRepository
        print("✓ Repository interface imported")
        
        print("✓ Architecture pattern looks good!")
        return True
        
    except ImportError as e:
        print(f"❌ Architecture test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing New FastAPI Architecture Setup")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test architecture
    if not test_architecture():
        success = False
    
    if success:
        print("\n✅ Architecture setup is ready!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install sqlalchemy[asyncio] aiosqlite alembic pydantic-settings")
        print("2. Create database migration: alembic revision --autogenerate")
        print("3. Run migration: alembic upgrade head")
        print("4. Start server: python -m app.main")
    else:
        print("\n❌ Some issues found. Check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()
