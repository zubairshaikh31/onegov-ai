"""
OneGov AI — Full Database Validation Script
"""
import asyncio
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings
from app.models.government import Service, Scheme, KnowledgeChunk, Ministry, Department
from app.models.intelligence import Video, ServiceVideo

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        print("Starting deep database integrity validation...")
        errors = 0

        # 1. Services
        services = (await session.execute(select(Service))).scalars().all()
        print(f" • Found {len(services)} services.")
        
        seen_service_slugs = set()
        for s in services:
            # Check unique slugs
            if s.slug in seen_service_slugs:
                print(f"   [ERROR] Duplicate service slug: {s.slug}")
                errors += 1
            seen_service_slugs.add(s.slug)
            
            # Check description
            if not s.description or len(s.description.strip()) == 0:
                print(f"   [WARNING] Service {s.slug} has empty description.")

            # Check department link
            if s.department_id is None:
                print(f"   [WARNING] Service {s.slug} has no department assigned.")

        # 2. Schemes
        schemes = (await session.execute(select(Scheme))).scalars().all()
        print(f" • Found {len(schemes)} schemes.")
        
        seen_scheme_slugs = set()
        for sch in schemes:
            if sch.slug in seen_scheme_slugs:
                print(f"   [ERROR] Duplicate scheme slug: {sch.slug}")
                errors += 1
            seen_scheme_slugs.add(sch.slug)
            if not sch.description or len(sch.description.strip()) == 0:
                print(f"   [WARNING] Scheme {sch.slug} has empty description.")

        # 3. Knowledge chunks & Embeddings
        chunks = (await session.execute(select(KnowledgeChunk))).scalars().all()
        print(f" • Found {len(chunks)} knowledge chunks.")
        
        for c in chunks:
            if c.embedding is None:
                print(f"   [ERROR] Chunk {c.id} has missing embedding vector!")
                errors += 1
            else:
                dim = len(c.embedding)
                if dim != 768:
                    print(f"   [ERROR] Chunk {c.id} has incorrect embedding dimension: {dim} (expected 768).")
                    errors += 1

        # 4. Service Videos
        videos = (await session.execute(select(Video))).scalars().all()
        print(f" • Found {len(videos)} videos.")
        
        service_videos = (await session.execute(select(ServiceVideo))).scalars().all()
        print(f" • Found {len(service_videos)} service-video mappings.")
        
        service_ids = {s.id for s in services}
        video_ids = {v.id for v in videos}
        
        for sv in service_videos:
            if sv.service_id not in service_ids:
                print(f"   [ERROR] ServiceVideo maps to non-existent service_id: {sv.service_id}")
                errors += 1
            if sv.video_id not in video_ids:
                print(f"   [ERROR] ServiceVideo maps to non-existent video_id: {sv.video_id}")
                errors += 1

        print("==================================================")
        print(f"Validation complete. Total critical errors found: {errors}")
        print("==================================================")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
