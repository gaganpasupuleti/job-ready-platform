import asyncio

import asyncpg


async def main() -> None:
    conn = await asyncpg.connect("postgresql://jobready:jobready_dev@localhost:5432/jobready_db")
    await conn.execute(
        "UPDATE users SET email = 'admin@jobready.dev' WHERE username = 'admin'"
    )
    print("Updated admin email to admin@jobready.dev")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
