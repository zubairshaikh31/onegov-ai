"""
OneGov AI — Video Report Generator
"""
import asyncio
import csv
import json
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
from app.models.government import Service
from app.models.intelligence import Video, ServiceVideo

OFFICIAL_CHANNELS = {
    "aadhaar uidai", "uidai", "morth india", "ministry of external affairs", 
    "passport seva official", "income tax department", "income tax india",
    "national informatics centre", "digital india", "mygov india", "epfo",
    "ministry of health and family welfare", "pib india"
}

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        services = (await session.execute(select(Service))).scalars().all()
        videos = (await session.execute(select(Video))).scalars().all()
        service_videos = (await session.execute(select(ServiceVideo))).scalars().all()

        total_services = len(services)
        
        # Build mapping of service to its videos
        s_to_vids = {}
        for sv in service_videos:
            s_to_vids.setdefault(sv.service_id, []).append(sv.video_id)

        vid_dict = {v.id: v for v in videos}

        services_with_videos = 0
        services_without_videos = 0
        
        official_count = 0
        educational_count = 0
        unverified_count = 0
        broken_count = 0
        review_count = 0

        detail_records = []

        for s in services:
            v_ids = s_to_vids.get(s.id, [])
            if not v_ids:
                services_without_videos += 1
                detail_records.append({
                    "service_id": str(s.id),
                    "service_slug": s.slug,
                    "service_name": s.name,
                    "video_id": "None",
                    "video_url": "No verified video available.",
                    "title": "No verified video available.",
                    "channel_name": "None",
                    "classification": "None",
                    "status": "UNVERIFIED"
                })
                continue

            services_with_videos += 1
            for v_id in v_ids:
                v = vid_dict.get(v_id)
                if not v:
                    continue
                
                ch_name = (v.channel_name or "").lower().strip()
                
                # Classify
                if any(oc in ch_name for oc in OFFICIAL_CHANNELS):
                    classification = "Official Video"
                    status = "VERIFIED_OFFICIAL"
                    official_count += 1
                elif "government" in ch_name or "govt" in ch_name or (s.state_id and s.state_id.lower() in ch_name):
                    classification = "Official Video"
                    status = "VERIFIED_OFFICIAL"
                    official_count += 1
                else:
                    classification = "Educational Video"
                    status = "EDUCATIONAL"
                    educational_count += 1

                if v.verification_status == "BROKEN":
                    status = "BROKEN"
                    broken_count += 1
                elif v.verification_status == "REQUIRES_REVIEW":
                    status = "UNVERIFIED"
                    review_count += 1
                elif v.verification_status == "UNVERIFIED" and status != "EDUCATIONAL":
                    status = "UNVERIFIED"
                    unverified_count += 1

                detail_records.append({
                    "service_id": str(s.id),
                    "service_slug": s.slug,
                    "service_name": s.name,
                    "video_id": v.youtube_video_id,
                    "video_url": v.youtube_url or f"https://www.youtube.com/watch?v={v.youtube_video_id}",
                    "title": v.title or "",
                    "channel_name": v.channel_name or "Unknown",
                    "classification": classification,
                    "status": status
                })

        summary = {
            "total_services": total_services,
            "services_with_videos": services_with_videos,
            "services_without_videos": services_without_videos,
            "official_videos": official_count,
            "educational_videos": educational_count,
            "unverified_videos": unverified_count,
            "broken_videos": broken_count,
            "videos_requiring_review": review_count
        }

        report_json = {
            "summary": summary,
            "details": detail_records
        }

        # Ensure directory exists
        data_dir = ROOT_DIR / "data"
        data_dir.mkdir(exist_ok=True)

        # Write JSON
        json_path = data_dir / "video-report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_json, f, indent=2)

        # Write CSV
        csv_path = data_dir / "video-report.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Service ID", "Service Slug", "Service Name", "Video ID", 
                "Video URL", "Video Title", "Channel Name", 
                "Channel Classification", "Verification Status"
            ])
            for r in detail_records:
                writer.writerow([
                    r["service_id"], r["service_slug"], r["service_name"],
                    r["video_id"], r["video_url"], r["title"],
                    r["channel_name"], r["classification"], r["status"]
                ])

        print(f"Successfully generated video reports:")
        print(f"  • {json_path}")
        print(f"  • {csv_path}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
