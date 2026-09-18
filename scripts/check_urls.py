"""
OneGov AI — Application URL Health Checker
"""
import asyncio
import csv
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

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

def check_url_sync(url: str) -> str:
    if not url:
        return "invalid URL"
    if not url.startswith("http://") and not url.startswith("https://"):
        return "invalid URL"
    
    parsed = urlparse(url)
    if not parsed.netloc:
        return "invalid URL"

    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        # 3 second timeout for verification speed
        with urllib.request.urlopen(req, timeout=3.0) as response:
            return str(response.getcode())
    except urllib.error.HTTPError as e:
        return str(e.code)
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            return "timeout"
        # DNS failure / connection error
        return "DNS failure"
    except Exception as e:
        return f"failed: {type(e).__name__}"

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        services = (await session.execute(select(Service))).scalars().all()
        
        # Collect unique URLs to minimize redundant checks
        unique_urls = list(set(s.official_url for s in services if s.official_url))
        logger_info = f"Found {len(services)} services with {len(unique_urls)} unique URLs. Checking health..."
        print(logger_info)

        # Run checks in a thread pool to allow async execution of blocking urllib calls
        loop = asyncio.get_running_loop()
        url_status = {}
        
        # Bounded concurrency checks
        sem = asyncio.Semaphore(15)
        
        async def worker(url):
            async with sem:
                # Run the blocking function in executor
                status = await loop.run_in_executor(None, check_url_sync, url)
                url_status[url] = status
                print(f"  Checked: {url} -> {status}")

        await asyncio.gather(*(worker(u) for u in unique_urls))

        # Build report
        report_rows = []
        for s in services:
            url = s.official_url
            status = url_status.get(url, "invalid URL") if url else "invalid URL"
            report_rows.append([
                str(s.id),
                s.slug,
                s.name,
                s.government_level,
                url or "",
                status
            ])

        # Write CSV
        data_dir = ROOT_DIR / "data"
        data_dir.mkdir(exist_ok=True)
        csv_path = data_dir / "url-health-report.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Slug", "Name", "Level", "Official URL", "HTTP Status"])
            writer.writerows(report_rows)

        print(f"Successfully generated URL health report: \n  • {csv_path}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
