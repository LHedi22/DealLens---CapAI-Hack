import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

engine = create_async_engine("sqlite+aiosqlite:///./convictai.db")
Session = async_sessionmaker(engine)

async def check():
    async with Session() as s:
        tables = (await s.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))).all()
        print("Tables:", [t[0] for t in tables])

        pipeline = (await s.execute(text(
            "SELECT startup_name, decision, esg_composite, compliance_health_score FROM deal_history WHERE is_pipeline=1"
        ))).all()
        print("\nPipeline companies:")
        for r in pipeline:
            print(" ", r)

        agreements = (await s.execute(text(
            "SELECT startup_name, source_type, total_committed_tnd FROM monitor_agreements"
        ))).all()
        print("\nMonitor agreements:", agreements)

        snapshots = (await s.execute(text(
            "SELECT startup_name, compliance_health_score FROM monitor_ledger_snapshots"
        ))).all()
        print("Monitor snapshots:", snapshots)

        profiles = (await s.execute(text(
            "SELECT company_name, extraction_source, profile_confidence FROM synergy_profiles"
        ))).all()
        print("\nSynergy profiles:", profiles)

asyncio.run(check())
