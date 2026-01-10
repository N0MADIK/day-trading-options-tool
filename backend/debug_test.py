
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

from app.infrastructure.db import engine, Base, AsyncSessionFactory
from app.domain import models
from app.repositories.sqlalchemy.custom_strategy_repo import SQLAlchemyCustomStrategyRepository
from app.services.custom_strategy_service import CustomStrategyService
from app.schemas.custom_strategies import CustomStrategyCreateRequest, StrategyExecutionType

async def main():
    print("Starting debug test...")
    try:
        # Init DB
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSessionFactory() as session:
            print("Session created")
            repo = SQLAlchemyCustomStrategyRepository(session)
            
            # Create Strategy
            strategy_data = CustomStrategyCreateRequest(
                name="Debug Strategy",
                code="pass",
                execution_type=StrategyExecutionType.PYTHON_SCRIPT
            )
            
            print("Creating strategy...")
            strategy_id = await repo.create_custom_strategy(strategy_data)
            print(f"Strategy created: {strategy_id}")
            
            # Verify
            strategy = await repo.get_custom_strategy_by_id(strategy_id)
            print(f"Strategy retrieved: {strategy}")
            
        print("Test passed!")
        
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
