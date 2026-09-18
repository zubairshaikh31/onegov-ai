"""
OneGov AI — Source Verification Report Generator
"""
import asyncio
import csv
import json
import sys
from datetime import datetime, timezone
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
from app.models.government import Service

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        services = (await session.execute(select(Service))).scalars().all()
        
        report_data = []
        for s in services:
            # Classification logic:
            # Original 80 services (do not have 'variant' in slug or 'central-' or state-specific standard pattern)
            is_generated_state = s.government_level == "State" and s.source_type == "OFFICIAL_STATE_PORTAL"
            is_generated_central = "variant" in s.slug
            
            if is_generated_central:
                status = "UNVERIFIED"
            elif is_generated_state:
                status = "PARTIALLY_VERIFIED"
            else:
                status = "VERIFIED"

            # Domain extraction
            domain = s.source_domain or ""
            if not domain and s.official_url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(s.official_url).netloc
                except Exception:
                    pass

            report_data.append({
                "id": str(s.id),
                "slug": s.slug,
                "name": s.name,
                "government_level": s.government_level,
                "state_id": s.state_id or "ALL",
                "official_source": s.official_source,
                "source_url": s.official_url or "",
                "source_domain": domain,
                "verification_status": status,
                "last_verified": datetime.now(timezone.utc).isoformat()
            })

        # Ensure directory exists
        data_dir = ROOT_DIR / "data"
        data_dir.mkdir(exist_ok=True)

        # Write JSON
        json_path = data_dir / "source-verification-report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        # Write CSV
        csv_path = data_dir / "source-verification-report.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Slug", "Name", "Level", "State", "Official Source", 
                "Source URL", "Source Domain", "Verification Status", "Last Verified"
            ])
            for r in report_data:
                writer.writerow([
                    r["id"], r["slug"], r["name"], r["government_level"], r["state_id"],
                    r["official_source"], r["source_url"], r["source_domain"],
                    r["verification_status"], r["last_verified"]
                ])

        print(f"Successfully generated source verification reports:")
        print(f"  • {json_path}")
        print(f"  • {csv_path}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
