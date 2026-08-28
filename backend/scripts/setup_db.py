import asyncio

import asyncpg


async def main() -> None:
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/postgres")
    exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname='jobready'")
    if not exists:
        await conn.execute("CREATE USER jobready WITH PASSWORD 'jobready_dev'")
        print("Created user jobready")
    else:
        await conn.execute("ALTER USER jobready WITH PASSWORD 'jobready_dev'")
        print("Updated jobready password")

    exists_db = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname='jobready_db'")
    if not exists_db:
        await conn.execute("CREATE DATABASE jobready_db OWNER jobready")
        print("Created database jobready_db")
    else:
        print("Database jobready_db already exists")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
