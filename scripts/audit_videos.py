"""
OneGov AI — YouTube Video Audit Tool
"""
import csv
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

import asyncio

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
        
        official_gov = 0
        official_min = 0
        official_dept = 0
        state_gov = 0
        third_party = 0

        report_rows = []

        for s in services:
            v_ids = s_to_vids.get(s.id, [])
            if not v_ids:
                services_without_videos += 1
                report_rows.append([
                    str(s.id), s.slug, s.name, s.government_level, "", "", "", "", "None", "UNVERIFIED"
                ])
                continue

            services_with_videos += 1
            for v_id in v_ids:
                v = vid_dict.get(v_id)
                if not v:
                    continue
                
                # Check channel type
                ch_name = (v.channel_name or "").lower().strip()
                
                # Classification
                is_official = False
                ch_type = "Third-Party Educational"
                
                if any(oc in ch_name for oc in OFFICIAL_CHANNELS):
                    is_official = True
                    if "ministry" in ch_name or "morth" in ch_name:
                        ch_type = "Official Ministry"
                        official_min += 1
                    elif "department" in ch_name or "tax" in ch_name or "uidai" in ch_name or "epfo" in ch_name:
                        ch_type = "Official Department"
                        official_dept += 1
                    else:
                        ch_type = "Official Government"
                        official_gov += 1
                elif "government" in ch_name or "govt" in ch_name or s.state_id and s.state_id.lower() in ch_name:
                    ch_type = "State Government"
                    state_gov += 1
                else:
                    third_party += 1

                report_rows.append([
                    str(s.id),
                    s.slug,
                    s.name,
                    s.government_level,
                    v.youtube_video_id,
                    v.youtube_url,
                    v.title,
                    v.channel_name or "Unknown",
                    ch_type,
                    v.verification_status
                ])

        # Write CSV
        data_dir = ROOT_DIR / "data"
        data_dir.mkdir(exist_ok=True)
        csv_path = data_dir / "video-coverage-report.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Service ID", "Service Slug", "Service Name", "Level", 
                "Video ID", "Video URL", "Video Title", "Channel Name", 
                "Channel Classification", "Verification Status"
            ])
            writer.writerows(report_rows)

        print("="*60)
        print("YOUTUBE VIDEO AUDIT REPORT SUMMARY")
        print("="*60)
        print(f"Total Services:                 {total_services}")
        print(f"Services With Videos:           {services_with_videos}")
        print(f"Services Without Videos:        {services_without_videos}")
        print(f"Official Government Channel:     {official_gov}")
        print(f"Official Ministry Channel:       {official_min}")
        print(f"Official Department Channel:     {official_dept}")
        print(f"State Government Channel:        {state_gov}")
        print(f"Third-Party Educational:        {third_party}")
        print("="*60)
        print(f"Successfully generated video coverage report: \n  • {csv_path}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
