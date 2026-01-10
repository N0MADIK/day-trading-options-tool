import asyncio
import sys
import os

# Add path
sys.path.append(os.getcwd())

from app.infrastructure.db import Base, engine
# Import all models
from app.models import *

async def main():
    print("Starting DB verification...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("SUCCESS: Tables created")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
