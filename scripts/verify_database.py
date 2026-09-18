"""
OneGov AI — Database Integrity Verification & Quality Assurance Tool
"""
import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Ensure correct path resolution
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure stdout/stderr handles UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings
from app.models.government import (
    Service,
    Scheme,
    Category,
    Department,
    Ministry,
    KnowledgeChunk,
)
from app.models.intelligence import Video, ServiceVideo

URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

SLUG_REGEX = re.compile(r'^[a-z0-9-]+$')

class DatabaseVerifier:
    def __init__(self, session: AsyncSession) -> None:
        self.db = session
        self.errors = []
        self.warnings = []

    async def verify_all(self) -> bool:
        logger.info("Starting comprehensive database integrity verification...")
        
        await self.verify_slugs()
        await self.verify_duplicates()
        await self.verify_foreign_keys_and_orphans()
        await self.verify_urls()
        await self.verify_missing_metadata()
        await self.verify_videos_and_embeddings()

        self.print_report()
        
        # Return True if there are NO critical errors, False otherwise
        return len(self.errors) == 0

    async def verify_slugs(self) -> None:
        logger.info("Verifying slug formatting...")
        # Check Services
        services = (await self.db.execute(select(Service))).scalars().all()
        for s in services:
            if not s.slug:
                self.errors.append(f"Critical: Service ID {s.id} has empty slug")
            elif not SLUG_REGEX.match(s.slug):
                self.errors.append(f"Critical: Service '{s.name}' has invalid slug format: '{s.slug}'")

        # Check Schemes
        schemes = (await self.db.execute(select(Scheme))).scalars().all()
        for sc in schemes:
            if not sc.slug:
                self.errors.append(f"Critical: Scheme ID {sc.id} has empty slug")
            elif not SLUG_REGEX.match(sc.slug):
                self.errors.append(f"Critical: Scheme '{sc.name}' has invalid slug format: '{sc.slug}'")

    async def verify_duplicates(self) -> None:
        logger.info("Checking for duplicate names or slugs...")
        # Check duplicate service slugs
        rows = (await self.db.execute(text("SELECT slug, COUNT(*) FROM services GROUP BY slug HAVING COUNT(*) > 1;"))).all()
        for r in rows:
            self.errors.append(f"Critical: Duplicate service slug detected: '{r[0]}' ({r[1]} occurrences)")

        # Check duplicate scheme slugs
        rows = (await self.db.execute(text("SELECT slug, COUNT(*) FROM schemes GROUP BY slug HAVING COUNT(*) > 1;"))).all()
        for r in rows:
            self.errors.append(f"Critical: Duplicate scheme slug detected: '{r[0]}' ({r[1]} occurrences)")

    async def verify_foreign_keys_and_orphans(self) -> None:
        logger.info("Checking foreign key references and orphan records...")
        
        # 1. Services pointing to non-existent Category
        orphans = (await self.db.execute(text(
            "SELECT s.id, s.name, s.category_id FROM services s LEFT JOIN categories c ON s.category_id = c.id WHERE s.category_id IS NOT NULL AND c.id IS NULL;"
        ))).all()
        for o in orphans:
            self.errors.append(f"Critical: Service '{o[1]}' (ID: {o[0]}) references non-existent Category ID: {o[2]}")

        # 2. Services pointing to non-existent Department
        orphans = (await self.db.execute(text(
            "SELECT s.id, s.name, s.department_id FROM services s LEFT JOIN departments d ON s.department_id = d.id WHERE s.department_id IS NOT NULL AND d.id IS NULL;"
        ))).all()
        for o in orphans:
            self.errors.append(f"Critical: Service '{o[1]}' (ID: {o[0]}) references non-existent Department ID: {o[2]}")

        # 3. Schemes pointing to non-existent Ministry
        orphans = (await self.db.execute(text(
            "SELECT s.id, s.name, s.ministry_id FROM schemes s LEFT JOIN ministries m ON s.ministry_id = m.id WHERE s.ministry_id IS NOT NULL AND m.id IS NULL;"
        ))).all()
        for o in orphans:
            self.errors.append(f"Critical: Scheme '{o[1]}' (ID: {o[0]}) references non-existent Ministry ID: {o[2]}")

    async def verify_urls(self) -> None:
        logger.info("Verifying URL formats and checking for broken/missing links...")
        
        # Check Services
        services = (await self.db.execute(select(Service))).scalars().all()
        for s in services:
            if not s.official_url:
                self.warnings.append(f"Warning: Service '{s.name}' is missing an official URL")
            elif not URL_REGEX.match(s.official_url) and not s.official_url.startswith("mock://"):
                self.errors.append(f"Critical: Service '{s.name}' has invalid URL: '{s.official_url}'")

        # Check Schemes
        schemes = (await self.db.execute(select(Scheme))).scalars().all()
        for sc in schemes:
            if not sc.official_url:
                self.warnings.append(f"Warning: Scheme '{sc.name}' is missing an official URL")
            elif not URL_REGEX.match(sc.official_url) and not sc.official_url.startswith("mock://"):
                self.errors.append(f"Critical: Scheme '{sc.name}' has invalid URL: '{sc.official_url}'")

    async def verify_missing_metadata(self) -> None:
        logger.info("Checking for missing categories, departments, or source info...")
        
        # Services missing category
        missing_cat = (await self.db.execute(select(Service).where(Service.category_id.is_(None)))).scalars().all()
        for s in missing_cat:
            self.warnings.append(f"Warning: Service '{s.name}' has no assigned category")

        # Services missing department (State level services might not always have specific central departments, which is fine, but we flag as warning)
        missing_dept = (await self.db.execute(select(Service).where(Service.department_id.is_(None), Service.government_level == "Central"))).scalars().all()
        for s in missing_dept:
            self.warnings.append(f"Warning: Central Service '{s.name}' has no assigned department")

    async def verify_videos_and_embeddings(self) -> None:
        logger.info("Verifying associated videos and knowledge chunk vector embeddings...")
        
        # Services missing videos
        services = (await self.db.execute(select(Service))).scalars().all()
        for s in services:
            links = (await self.db.execute(select(ServiceVideo).where(ServiceVideo.service_id == s.id))).scalars().all()
            if not links:
                self.warnings.append(f"Warning: Service '{s.name}' has no linked educational videos")

        # Knowledge chunks missing embeddings
        chunks = (await self.db.execute(select(KnowledgeChunk))).scalars().all()
        missing_emb = [c for c in chunks if c.embedding is None]
        if missing_emb:
            self.warnings.append(f"Warning: {len(missing_emb)} knowledge chunks are missing vector embeddings (embeddings generation skipped/failed)")

    def print_report(self) -> None:
        print("\n" + "="*70)
        print("DATABASE INTEGRITY AUDIT REPORT")
        print("="*70)
        
        print(f" • Total Critical Errors Found : {len(self.errors)}")
        print(f" • Total Warnings Found        : {len(self.warnings)}")
        print("-"*70)

        if self.errors:
            print("\n❌ CRITICAL ERRORS:")
            for err in self.errors[:30]:
                print(f"  [ERROR] {err}")
            if len(self.errors) > 30:
                print(f"  ...and {len(self.errors) - 30} more errors.")
        else:
            print("\n✓ No critical data integrity errors found!")

        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warn in self.warnings[:20]:
                print(f"  [WARN] {warn}")
            if len(self.warnings) > 20:
                print(f"  ...and {len(self.warnings) - 20} more warnings.")
        else:
            print("\n✓ No warnings found!")
        
        print("="*70 + "\n")

async def main() -> None:
    db_url = settings.DATABASE_URL
    logger.info(f"Connecting to database for verification: {db_url.split('@')[-1]}")
    engine = create_async_engine(db_url, echo=False)

    async with AsyncSession(engine) as session:
        verifier = DatabaseVerifier(session)
        is_clean = await verifier.verify_all()

    await engine.dispose()
    
    if not is_clean:
        logger.error("Database verification failed with critical errors. Exiting with status 1.")
        sys.exit(1)
    else:
        logger.info("Database verification succeeded. All checks green.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
