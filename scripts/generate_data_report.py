"""
OneGov AI — Database Verification & Audit Report Generator
"""
import asyncio
import sys
import re
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings
from app.models.government import (
    Service,
    Scheme,
    Category,
    Department,
    Ministry,
    KnowledgeChunk,
    RequiredDocument,
    ApplicationStep,
    ServiceDocument,
)
from app.models.intelligence import Video, ServiceVideo

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        # Fetch data
        services = (await session.execute(select(Service))).scalars().all()
        schemes = (await session.execute(select(Scheme))).scalars().all()
        categories = {c.id: c.name for c in (await session.execute(select(Category))).scalars().all()}
        depts_objs = (await session.execute(select(Department))).scalars().all()
        departments = {d.id: d.name for d in depts_objs}
        dept_to_min = {d.id: d.ministry_id for d in depts_objs}
        ministries = {m.id: m.name for m in (await session.execute(select(Ministry))).scalars().all()}

        total_services = len(services)
        total_schemes = len(schemes)

        central_services = sum(1 for s in services if s.government_level == "Central")
        state_services = sum(1 for s in services if s.government_level == "State")

        services_by_state = Counter(s.state_id for s in services if s.state_id)
        services_by_cat = Counter(categories.get(s.category_id, "Unknown/None") for s in services)
        services_by_dept = Counter(departments.get(s.department_id, "Unknown/None") for s in services)
        services_by_min = Counter(ministries.get(dept_to_min.get(s.department_id), "Unknown/None") for s in services if s.department_id)

        schemes_by_state = Counter(sch.state_name for sch in schemes if sch.state_name)
        schemes_by_min = Counter(ministries.get(sch.ministry_id, "Unknown/None") for sch in schemes)

        # Verification & quality audits
        dup_names = []
        dup_slugs = []
        dup_urls = []
        
        name_counts = Counter(s.name for s in services)
        slug_counts = Counter(s.slug for s in services)
        url_counts = Counter(s.official_url for s in services if s.official_url)

        dup_names = [name for name, count in name_counts.items() if count > 1]
        dup_slugs = [slug for slug, count in slug_counts.items() if count > 1]
        dup_urls = [url for url, count in url_counts.items() if count > 1]

        missing_desc = sum(1 for s in services if not s.description)
        missing_cat = sum(1 for s in services if not s.category_id)
        missing_dept = sum(1 for s in services if not s.department_id and s.government_level == "Central")
        missing_source_url = sum(1 for s in services if not s.source_url)
        missing_apply_url = sum(1 for s in services if not s.official_apply_link)
        missing_eligibility = sum(1 for s in services if not s.eligibility_description)
        
        # Checked documents and steps
        doc_links = (await session.execute(select(ServiceDocument.service_id))).scalars().all()
        services_with_docs = set(doc_links)
        missing_docs = sum(1 for s in services if s.id not in services_with_docs)

        step_links = (await session.execute(select(ApplicationStep.service_id))).scalars().all()
        services_with_steps = set(step_links)
        missing_steps = sum(1 for s in services if s.id not in services_with_steps)

        missing_fees = sum(1 for s in services if s.fee_amount is None)
        missing_proc_time = sum(1 for s in services if not s.processing_time)
        missing_ver_status = sum(1 for s in services if not s.verification_status)

        # Distinguish unique / state-specific / template / verified
        template_records = sum(1 for s in services if s.government_level == "State" and s.source_type == "OFFICIAL_STATE_PORTAL")
        independently_sourced = sum(1 for s in services if s.source_type != "OFFICIAL_STATE_PORTAL" or s.government_level == "Central")
        
        # Verification status check
        verified_records = sum(1 for s in services if s.verification_status == "VERIFIED")
        unverified_records = sum(1 for s in services if s.verification_status == "UNVERIFIED")

        print("="*60)
        print("ONEGOV AI DATABASE REPORT")
        print("="*60)
        print(f"Total Services:          {total_services}")
        print(f"  Central Services:      {central_services}")
        print(f"  State/UT Services:     {state_services}")
        print(f"Total Schemes:           {total_schemes}")
        print("-"*60)
        
        print("\nSERVICES BY STATE:")
        for state, count in sorted(services_by_state.items(), key=lambda x: -x[1]):
            print(f"  • {state:<5}: {count}")

        print("\nSERVICES BY CATEGORY:")
        for cat, count in sorted(services_by_cat.items(), key=lambda x: -x[1]):
            print(f"  • {cat:<35}: {count}")

        print("\nSERVICES BY MINISTRY:")
        for min_name, count in sorted(services_by_min.items(), key=lambda x: -x[1]):
            print(f"  • {min_name[:45]:<45}: {count}")

        print("\nSERVICES BY DEPARTMENT:")
        for dept, count in sorted(services_by_dept.items(), key=lambda x: -x[1]):
            print(f"  • {dept[:45]:<45}: {count}")

        print("\nSCHEMES BY STATE/UT:")
        for state, count in sorted(schemes_by_state.items(), key=lambda x: -x[1]):
            print(f"  • {state:<35}: {count}")

        print("\nSCHEMES BY MINISTRY:")
        for min_name, count in sorted(schemes_by_min.items(), key=lambda x: -x[1]):
            print(f"  • {min_name[:45]:<45}: {count}")

        print("="*60)
        print("SERVICES QUALITY & CHECKS AUDIT")
        print("="*60)
        print(f"Duplicate Names:          {len(dup_names)}")
        print(f"Duplicate Slugs:          {len(dup_slugs)}")
        print(f"Duplicate Official URLs:   {len(dup_urls)}")
        print(f"Missing Descriptions:     {missing_desc}")
        print(f"Missing Categories:       {missing_cat}")
        print(f"Missing Departments (C):  {missing_dept}")
        print(f"Missing Source URLs:      {missing_source_url}")
        print(f"Missing Application URLs: {missing_apply_url}")
        print(f"Missing Eligibility:      {missing_eligibility}")
        print(f"Missing Documents:        {missing_docs}")
        print(f"Missing App Steps:        {missing_steps}")
        print(f"Missing Fees:             {missing_fees}")
        print(f"Missing Processing Time:  {missing_proc_time}")
        print(f"Missing Verification:     {missing_ver_status}")
        print("-"*60)
        print(f"Unique Services:          {total_services - template_records}")
        print(f"State-Specific Services:  {state_services}")
        print(f"Generated/Template Recs:  {template_records}")
        print(f"Independently Sourced:   {independently_sourced}")
        print(f"Verified Records (DB):    {verified_records}")
        print(f"Unverified Records (DB):  {unverified_records}")
        print("="*60)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
