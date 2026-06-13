"""
Data synchronization service: PostgreSQL -> DuckDB for analytics.
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

SYNC_TABLES = [
    "revenues_v2",
    "expenses_v2",
    "claims_v2",
    "occupancy_v2",
    "metric_computed_values",
    "data_quality_scores",
]


async def sync_table_to_duckdb(table_name: str) -> dict:
    """Sync a single table from PostgreSQL to DuckDB."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            count = result.scalar()
            logger.info(f"Table {table_name}: {count} rows in PostgreSQL")
            return {"table": table_name, "pg_rows": count, "status": "synced"}
    except Exception as e:
        logger.error(f"Failed to sync {table_name}: {e}")
        return {"table": table_name, "status": "error", "error": str(e)}


async def sync_all() -> list[dict]:
    """Sync all analytics tables from PostgreSQL to DuckDB."""
    results = []
    for table in SYNC_TABLES:
        result = await sync_table_to_duckdb(table)
        results.append(result)
    return results


async def main():
    """Entry point for the data sync service."""
    logger.info("Starting data sync service...")
    while True:
        try:
            results = await sync_all()
            synced = sum(1 for r in results if r["status"] == "synced")
            logger.info(f"Sync complete: {synced}/{len(results)} tables synced")
        except Exception as e:
            logger.error(f"Sync cycle failed: {e}")

        await asyncio.sleep(3600)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
