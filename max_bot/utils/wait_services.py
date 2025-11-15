import asyncio
import os

import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL")


async def wait_for_db():
    while True:
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.close()
            print("✅ PostgreSQL ready")
            break
        except Exception:
            print("⏳ Waiting for PostgreSQL...")
            await asyncio.sleep(2)


async def wait_for_services():
    await asyncio.gather(wait_for_db())
