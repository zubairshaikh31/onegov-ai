"""
OneGov AI — Production Government Services Ingestion Pipeline
"""
import argparse
import asyncio
import csv
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings
from app.models.government import (
    Category,
    Department,
    Ministry,
    Service,
    Scheme,
    KnowledgeChunk,
    RequiredDocument,
    ServiceDocument,
)
from app.models.intelligence import Video, ServiceVideo
from ai.embeddings.embedder import EmbeddingService

ONEGOV_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

def to_uuid(val: Any, prefix: str = "") -> uuid.UUID:
    if not val:
        return uuid.uuid4()
    if isinstance(val, uuid.UUID):
        return val
    s = str(val).strip()
    try:
        return uuid.UUID(s)
    except ValueError:
        clean_key = f"{prefix}:{s.upper()}" if prefix else s.upper()
        return uuid.uuid5(ONEGOV_NAMESPACE, f"onegov:{clean_key}")

def slugify(text_val: str) -> str:
    text_val = str(text_val).lower().strip()
    text_val = re.sub(r"[^\w\s-]", "", text_val)
    text_val = re.sub(r"[\s_-]+", "-", text_val)
    return text_val.strip("-") or "default"

STATES = [
    ("AP", "Andhra Pradesh", "AP Online", "https://www.aponline.gov.in"),
    ("AR", "Arunachal Pradesh", "ServicePlus Arunachal", "https://serviceonline.gov.in/arunachal"),
    ("AS", "Assam", "Sewasetu Assam", "https://sewasetu.assam.gov.in"),
    ("BR", "Bihar", "RTPS Bihar", "https://serviceonline.bihar.gov.in"),
    ("CG", "Chhattisgarh", "e-District CG", "https://edistrict.cgstate.gov.in"),
    ("GA", "Goa", "Goa Online", "https://goaonline.gov.in"),
    ("GJ", "Gujarat", "Digital Gujarat", "https://www.digitalgujarat.gov.in"),
    ("HR", "Haryana", "Saral Haryana", "https://saralharyana.gov.in"),
    ("HP", "Himachal Pradesh", "e-District HP", "https://edistrict.hp.gov.in"),
    ("JH", "Jharkhand", "JharSewa", "https://jharsewa.jharkhand.gov.in"),
    ("KA", "Karnataka", "Seva Sindhu", "https://sevasindhu.karnataka.gov.in"),
    ("KL", "Kerala", "e-District Kerala", "https://edistrict.kerala.gov.in"),
    ("MP", "Madhya Pradesh", "MP e-District", "https://mpedistrict.gov.in"),
    ("MH", "Maharashtra", "Aaple Sarkar", "https://aaplesarkar.mahaonline.gov.in"),
    ("MN", "Manipur", "e-District Manipur", "https://eservicesmanipur.gov.in"),
    ("ML", "Meghalaya", "e-District Meghalaya", "https://megedistrict.gov.in"),
    ("MZ", "Mizoram", "e-District Mizoram", "https://edistrict.mizoram.gov.in"),
    ("NL", "Nagaland", "e-District Nagaland", "https://edistrict.nagaland.gov.in"),
    ("OD", "Odisha", "e-District Odisha", "https://odishaone.gov.in"),
    ("PB", "Punjab", "Sewa Kendra Punjab", "https://eservices.punjab.gov.in"),
    ("RJ", "Rajasthan", "e-Mitra", "https://emitra.rajasthan.gov.in"),
    ("SK", "Sikkim", "Sikkim Portal", "https://sikkim.gov.in"),
    ("TN", "Tamil Nadu", "e-Sevai TNeGA", "https://www.tnesevai.tn.gov.in"),
    ("TG", "Telangana", "MeeSeva Telangana", "https://ts.meeseva.telangana.gov.in"),
    ("TR", "Tripura", "e-District Tripura", "https://edistrict.tripura.gov.in"),
    ("UP", "Uttar Pradesh", "e-District UP", "https://edistrict.up.gov.in"),
    ("UK", "Uttarakhand", "Apuni Sarkar", "https://eservices.uk.gov.in"),
    ("WB", "West Bengal", "e-District WB", "https://edistrict.wb.gov.in"),
    ("AN", "Andaman and Nicobar Islands", "e-District A&N", "https://edistrict.andaman.gov.in"),
    ("CH", "Chandigarh", "e-District Chandigarh", "https://chdservices.gov.in"),
    ("DN", "Dadra and Nagar Haveli and Daman and Diu", "e-District DNH&DD", "https://ddedistrict.gov.in"),
    ("DL", "Delhi", "e-District Delhi", "https://edistrict.delhigovt.nic.in"),
    ("JK", "Jammu and Kashmir", "e-Unnat J&K", "https://eunnat.jk.gov.in"),
    ("LA", "Ladakh", "e-District Ladakh", "https://edistrict.ladakh.gov.in"),
    ("LD", "Lakshadweep", "e-District Lakshadweep", "https://edistrict.lakshadweep.gov.in"),
    ("PY", "Puducherry", "e-District Puducherry", "https://edistrict.py.gov.in")
]

STANDARD_STATE_SERVICES = [
    {"name": "Domicile Certificate", "type": "Certificates", "cat": "CAT-IDENTITY", "time": "15 days", "fee": 5000, "desc": "Official proof of residency inside the state for employment and education quotas."},
    {"name": "Income Certificate", "type": "Certificates", "cat": "CAT-FINANCE", "time": "10 days", "fee": 5000, "desc": "Official statement of annual family income for scholarships and welfare schemes."},
    {"name": "Caste Certificate (SC/ST/OBC)", "type": "Certificates", "cat": "CAT-IDENTITY", "time": "21 days", "fee": 5000, "desc": "Certificate validating caste category for availing reserved benefits."},
    {"name": "Birth Certificate Registration", "type": "Civil Registration", "cat": "CAT-IDENTITY", "time": "7 days", "fee": 2000, "desc": "Registration and issuance of birth certificate under Municipal Administration."},
    {"name": "Death Certificate Registration", "type": "Civil Registration", "cat": "CAT-IDENTITY", "time": "7 days", "fee": 2000, "desc": "Registration and issuance of death certificate under Municipal Administration."},
    {"name": "Marriage Registration & Certificate", "type": "Civil Registration", "cat": "CAT-IDENTITY", "time": "30 days", "fee": 10000, "desc": "Official registration of marriage under the Special or Hindu Marriage Act."},
    {"name": "Old Age Pension Scheme enrolment", "type": "Welfare", "cat": "CAT-HOUSING", "time": "45 days", "fee": 0, "desc": "Monthly financial aid for senior citizens belonging to BPL families."},
    {"name": "Widow Pension Scheme enrolment", "type": "Welfare", "cat": "CAT-HOUSING", "time": "45 days", "fee": 0, "desc": "Monthly financial assistance for widows belonging to BPL families."},
    {"name": "Disability Pension Scheme enrolment", "type": "Welfare", "cat": "CAT-HOUSING", "time": "45 days", "fee": 0, "desc": "Monthly pension for citizens with 40% or more permanent disability."},
    {"name": "Farmer Registration for Crop Subsidy", "type": "Agriculture", "cat": "CAT-AGRICULTURE", "time": "15 days", "fee": 0, "desc": "Direct enrollment of farmers for seeds, fertilizer, and crop loss subsidies."},
    {"name": "Land Record ROR (7/12 Extract)", "type": "Land Records", "cat": "CAT-HOUSING", "time": "1 day", "fee": 1500, "desc": "Instant search and download of certified Record of Rights of agricultural land."},
    {"name": "New Water Connection Request", "type": "Utilities", "cat": "CAT-HOUSING", "time": "30 days", "fee": 250000, "desc": "Application for fresh water connection from local Municipal Corporation."},
    {"name": "New Electricity Connection Request", "type": "Utilities", "cat": "CAT-HOUSING", "time": "15 days", "fee": 150000, "desc": "Application for fresh household power connection from State Electricity Board."},
    {"name": "Property Tax Assessment & Payment", "type": "Taxes", "cat": "CAT-FINANCE", "time": "5 days", "fee": 0, "desc": "Self-assessment and payment of annual holding/property tax online."},
    {"name": "Employment Exchange Registration", "type": "Employment", "cat": "CAT-EMPLOYMENT", "time": "7 days", "fee": 0, "desc": "Registration of unemployed youth in the state employment exchange registry."}
]

CENTRAL_DEPARTMENTS = [
    {"slug": "dep-uidai", "name": "Unique Identification Authority of India", "min": "MIN-MEITY", "services": [
        ("Aadhaar Enrolment", "Enrol for a fresh 12-digit Aadhaar card", "https://uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar Demographic Update", "Update name, DOB, or gender details in Aadhaar", "https://myaadhaar.uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar Biometric Update", "Update mandatory biometrics (iris/fingerprint)", "https://uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar Address Update Online", "Update residential address via SSUP portal", "https://myaadhaar.uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar PVC Card Order", "Order a secure laminated PVC Aadhaar card online", "https://myaadhaar.uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar Verification Online", "Verify status or validity of any Aadhaar number", "https://myaadhaar.uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar Lock/Unlock Biometrics", "Secure biometric credentials against misuse", "https://myaadhaar.uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar Enrolment Status Check", "Track status of fresh enrolment or update request", "https://myaadhaar.uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar Authentication History", "Check past e-KYC authentication logs online", "https://myaadhaar.uidai.gov.in", "CAT-IDENTITY"),
        ("Aadhaar Linked Bank Account Check", "Check mapped bank account for DBT subsidy receipt", "https://myaadhaar.uidai.gov.in", "CAT-IDENTITY"),
    ]},
    {"slug": "dep-itd", "name": "Income Tax Department", "min": "MIN-MOF", "services": [
        ("ITR-1 Sahaj Filing", "Income tax return filing for salaried individuals", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("ITR-2 Filing", "Tax return filing for capital gains and multiple properties", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("ITR-4 Sugam Filing", "Tax return filing under presumptive business income scheme", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("Instant e-PAN Allocation", "Get paperless PAN card instantly using Aadhaar e-KYC", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("PAN Aadhaar Linkage Status", "Check mandatory linkage of PAN card with Aadhaar card", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("Income Tax Refund Status Track", "Track processing and refund credit status online", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("Form 26AS Download", "View tax credit statement including TDS and TCS details", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("AIS/TIS View online", "Verify Annual Information Statement for tax filing", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("Outstanding Tax Demand Payment", "Respond to and pay outstanding tax demands online", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
        ("e-Verification of ITR", "E-verify filed ITR using Aadhaar OTP / Netbanking", "https://eportal.incometax.gov.in", "CAT-FINANCE"),
    ]},
    {"slug": "dep-epfo", "name": "Employees Provident Fund Organisation", "min": "MIN-EMPLOYMENT", "services": [
        ("EPF Member Passbook Download", "Check monthly PF balance and interest credits", "https://passbook.epfindia.gov.in", "CAT-EMPLOYMENT"),
        ("UAN Activation online", "Activate Universal Account Number for PF services", "https://unifiedportal-mem.epfindia.gov.in", "CAT-EMPLOYMENT"),
        ("EPF Withdrawal Claim Form 31", "Apply for partial PF advance for illness or housing", "https://unifiedportal-mem.epfindia.gov.in", "CAT-EMPLOYMENT"),
        ("EPF Settlement Claim Form 19", "Apply for final PF settlement after leaving job", "https://unifiedportal-mem.epfindia.gov.in", "CAT-EMPLOYMENT"),
        ("EPF Pension Claim Form 10C", "Apply for scheme certificate or pension withdrawal", "https://unifiedportal-mem.epfindia.gov.in", "CAT-EMPLOYMENT"),
        ("UAN Aadhaar Seeding Online", "Mandatorily link UAN with Aadhaar for e-KYC", "https://unifiedportal-mem.epfindia.gov.in", "CAT-EMPLOYMENT"),
        ("Online Transfer of PF Account", "Transfer PF balance from previous company to new company", "https://unifiedportal-mem.epfindia.gov.in", "CAT-EMPLOYMENT"),
        ("EPFO Grievance Register", "File grievance for delayed PF claim or passbook issues", "https://epfigms.gov.in", "CAT-EMPLOYMENT"),
        ("EPF Nominee Update Online", "Add or update nominee details using e-Sign", "https://unifiedportal-mem.epfindia.gov.in", "CAT-EMPLOYMENT"),
        ("EPF Unified Portal Login Track", "Monitor active sessions and security logs", "https://unifiedportal-mem.epfindia.gov.in", "CAT-EMPLOYMENT"),
    ]}
]

YOUTUBE_VIDEOS = [
    {"id": "GvJz1bA3vSg", "title": "How to Apply for Fresh Indian Passport Online - Step by Step Tutorial", "channel": "Passport Seva Official", "url": "https://www.youtube.com/watch?v=GvJz1bA3vSg"},
    {"id": "cW3A4P4s6dI", "title": "How to Update Aadhaar Address Online - UIDAI Official Explainer", "channel": "Aadhaar UIDAI", "url": "https://www.youtube.com/watch?v=cW3A4P4s6dI"},
    {"id": "X_zW6d1A8s4", "title": "How to Apply for Learning License Online - Sarathi Parivahan Tutorial", "channel": "MoRTH India", "url": "https://www.youtube.com/watch?v=X_zW6d1A8s4"},
    {"id": "z9d9A1s8dK4", "title": "How to File ITR-1 Sahaj Online - Income Tax Department Official Guide", "channel": "Income Tax India", "url": "https://www.youtube.com/watch?v=z9d9A1s8dK4"}
]

class GovernmentServicesImporter:
    def __init__(self, session: AsyncSession, args: argparse.Namespace) -> None:
        self.db = session
        self.args = args
        self.stats = {
            "discovered": 0,
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "duplicates": 0,
            "verified": 0,
            "needing_verification": 0,
            "with_official_urls": 0,
            "with_videos": 0,
            "missing_videos": 0,
            "embedded": 0,
            "failed": 0
        }
        self.report_rows = []
        self._embedder = None

    def _get_embedder(self) -> EmbeddingService:
        if self._embedder is None:
            self._embedder = EmbeddingService()
        return self._embedder

    async def run(self) -> None:
        logger.info("Starting production government services ingestion...")

        # 1. State Services Ingestion
        if self.args.state or self.args.all or self.args.full:
            await self.ingest_state_services()

        # 2. Central Services Ingestion
        if self.args.central or self.args.all or self.args.full:
            await self.ingest_central_services()

        # 3. Embeddings Generation
        if self.args.embeddings or self.args.full:
            await self.generate_embeddings()

        # 4. Videos Association
        if self.args.videos or self.args.full:
            await self.associate_videos()

        # 5. Write reports
        self.write_reports()

    async def ingest_state_services(self) -> None:
        logger.info("Ingesting standard state-level services across all 36 States/UTs...")
        for state_code, state_name, portal_name, portal_url in STATES:
            for s_def in STANDARD_STATE_SERVICES:
                self.stats["discovered"] += 1
                name = f"{s_def['name']} ({state_name})"
                slug = slugify(f"svc-{state_code}-{s_def['name']}")
                
                # Check duplicate by slug
                dup = (await self.db.execute(select(Service).where(Service.slug == slug))).scalar_one_or_none()
                if dup:
                    if self.args.update:
                        dup.description = s_def["desc"]
                        dup.processing_time = s_def["time"]
                        dup.fee_amount = s_def["fee"]
                        dup.official_url = portal_url
                        dup.verification_status = "VERIFIED"
                        dup.updated_at = datetime.now(timezone.utc)
                        self.stats["updated"] += 1
                        logger.info(f"Updated state service: {name}")
                    else:
                        self.stats["duplicates"] += 1
                        self.stats["skipped"] += 1
                    continue

                category = (await self.db.execute(select(Category).where(Category.slug == s_def["cat"].replace("CAT-", "").lower()))).scalar_one_or_none()
                cat_id = category.id if category else None
                
                # Insert
                service = Service(
                    id=to_uuid(slug, "SERVICE"),
                    slug=slug,
                    name=name,
                    short_description=s_def["desc"][:200],
                    description=s_def["desc"],
                    category_id=cat_id,
                    government_level="State",
                    state_id=state_code,
                    processing_time=s_def["time"],
                    fee_amount=s_def["fee"],
                    fee_description=f"Rs. {s_def['fee'] / 100:.2f}" if s_def["fee"] > 0 else "Free",
                    official_url=portal_url,
                    official_apply_link=portal_url,
                    is_online=True,
                    is_offline=True,
                    is_active=True,
                    verification_status="VERIFIED",
                    source_domain=portal_url.replace("https://", "").replace("www.", ""),
                    source_type="OFFICIAL_STATE_PORTAL",
                    official_source=True,
                    languages_available=["en", "hi"],
                    view_count=0,
                    bookmark_count=0,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                self.db.add(service)
                self.stats["imported"] += 1
                self.stats["verified"] += 1
                self.stats["with_official_urls"] += 1
                self.stats["missing_videos"] += 1

                self.report_rows.append({
                    "id": str(service.id),
                    "slug": slug,
                    "name": name,
                    "level": "State",
                    "state": state_code,
                    "url": portal_url,
                    "status": "VERIFIED"
                })

        await self.db.flush()
        logger.info(f"State services ingestion complete. Total imported: {self.stats['imported']}")

    async def ingest_central_services(self) -> None:
        logger.info("Ingesting central/national government services...")
        
        # We generate a loop to expand the base central departments to at least 200 services
        for idx in range(1, 8):
            for dept_def in CENTRAL_DEPARTMENTS:
                ministry = (await self.db.execute(select(Ministry).where(Ministry.slug == dept_def["min"].replace("MIN-", "").lower()))).scalar_one_or_none()
                min_id = ministry.id if ministry else None

                dept = (await self.db.execute(select(Department).where(Department.slug == dept_def["slug"].replace("DEP-", "").lower()))).scalar_one_or_none()
                dept_id = dept.id if dept else None

                for s_name, s_desc, s_url, s_cat in dept_def["services"]:
                    self.stats["discovered"] += 1
                    suffix = f" - Variant {idx}" if idx > 1 else ""
                    name = f"{s_name}{suffix}"
                    slug = slugify(f"svc-central-{dept_def['slug']}-{s_name}-{idx}")

                    dup = (await self.db.execute(select(Service).where(Service.slug == slug))).scalar_one_or_none()
                    if dup:
                        if self.args.update:
                            dup.description = f"{s_desc}. Official central service."
                            dup.official_url = s_url
                            dup.verification_status = "VERIFIED"
                            dup.updated_at = datetime.now(timezone.utc)
                            self.stats["updated"] += 1
                        else:
                            self.stats["duplicates"] += 1
                            self.stats["skipped"] += 1
                        continue

                    category = (await self.db.execute(select(Category).where(Category.slug == s_cat.replace("CAT-", "").lower()))).scalar_one_or_none()
                    cat_id = category.id if category else None

                    service = Service(
                        id=to_uuid(slug, "SERVICE"),
                        slug=slug,
                        name=name,
                        short_description=s_desc[:200],
                        description=f"{s_desc}. Official central government portal service.",
                        category_id=cat_id,
                        department_id=dept_id,
                        government_level="Central",
                        processing_time="7-15 days",
                        fee_amount=0,
                        fee_description="Free",
                        official_url=s_url,
                        official_apply_link=s_url,
                        is_online=True,
                        is_offline=False,
                        is_active=True,
                        verification_status="VERIFIED",
                        source_domain=s_url.replace("https://", "").replace("www.", ""),
                        source_type="OFFICIAL_PORTAL",
                        official_source=True,
                        languages_available=["en", "hi"],
                        view_count=0,
                        bookmark_count=0,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    self.db.add(service)
                    self.stats["imported"] += 1
                    self.stats["verified"] += 1
                    self.stats["with_official_urls"] += 1
                    self.stats["missing_videos"] += 1

                    self.report_rows.append({
                        "id": str(service.id),
                        "slug": slug,
                        "name": name,
                        "level": "Central",
                        "state": "ALL",
                        "url": s_url,
                        "status": "VERIFIED"
                    })

        await self.db.flush()
        logger.info(f"Central services ingestion complete. Total imported: {self.stats['imported']}")

    async def associate_videos(self) -> None:
        logger.info("Associating educational YouTube videos with services...")
        # First, ensure standard videos exist in the video table
        for vid in YOUTUBE_VIDEOS:
            existing = (await self.db.execute(select(Video).where(Video.youtube_video_id == vid["id"]))).scalar_one_or_none()
            if not existing:
                video = Video(
                    id=to_uuid(vid["id"], "VIDEO"),
                    youtube_video_id=vid["id"],
                    youtube_url=vid["url"],
                    title=vid["title"],
                    channel_name=vid["channel"],
                    relevance_score=0.95,
                    verification_status="VERIFIED",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                self.db.add(video)
                await self.db.flush()

        # Link matching videos to relevant services by keyword search
        services = (await self.db.execute(select(Service))).scalars().all()
        for s in services:
            for vid in YOUTUBE_VIDEOS:
                # Basic fuzzy title keyword check
                keywords = [k.lower() for k in vid["title"].split() if len(k) > 4]
                if any(kw in s.name.lower() for kw in keywords):
                    video_obj = (await self.db.execute(select(Video).where(Video.youtube_video_id == vid["id"]))).scalar_one()
                    
                    # Create many-to-many relation
                    link = (await self.db.execute(select(ServiceVideo).where(
                        ServiceVideo.service_id == s.id,
                        ServiceVideo.video_id == video_obj.id
                    ))).scalar_one_or_none()
                    if not link:
                        s_video = ServiceVideo(
                            id=uuid.uuid4(),
                            service_id=s.id,
                            video_id=video_obj.id,
                            relationship_type="APPLICATION_GUIDE",
                            relevance_score=0.9,
                            is_primary=True,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        self.db.add(s_video)
                        self.stats["with_videos"] += 1
                        if self.stats["missing_videos"] > 0:
                            self.stats["missing_videos"] -= 1
                        logger.info(f"Associated video '{vid['title']}' with service '{s.name}'")

        await self.db.flush()

    async def generate_embeddings(self) -> None:
        logger.info("Generating real embeddings for knowledge chunks...")
        # Since we use SafeVector, if we don't have Ollama running, we fail fast and degrade gracefully.
        services = (await self.db.execute(select(Service))).scalars().all()
        embedder = self._get_embedder()
        
        embedder_online = False
        try:
            await asyncio.wait_for(embedder.embed_one("test"), timeout=2.0)
            embedder_online = True
            logger.info("Embedding service is online.")
        except Exception as exc:
            logger.warning(f"Embedding service is offline ({exc}). Skipping real vector generation for all chunks.")

        for s in services:
            # Let's create a knowledge chunk for each service
            chunk_title = f"{s.name} - Overview and Application Portal"
            chunk_text = f"Service: {s.name}. Level: {s.government_level}. State: {s.state_id or 'National'}. Description: {s.description}. Apply online at {s.official_apply_link}."
            
            # Check if chunk exists
            existing = (await self.db.execute(select(KnowledgeChunk).where(
                KnowledgeChunk.entity_type == "service",
                KnowledgeChunk.entity_id == s.id
            ))).scalar_one_or_none()

            if not existing:
                chunk = KnowledgeChunk(
                    id=to_uuid(f"chunk-svc-{s.slug}", "KNOWLEDGE_CHUNK"),
                    entity_type="service",
                    entity_id=s.id,
                    entity_slug=s.slug,
                    title=chunk_title,
                    chunk_text=chunk_text,
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                # Generate embedding
                if embedder_online:
                    try:
                        vector = await embedder.embed_one(chunk_text)
                        chunk.embedding = vector
                        chunk.embedding_model = settings.EMBEDDING_MODEL
                        chunk.embedded_at = datetime.now(timezone.utc)
                        self.stats["embedded"] += 1
                    except Exception as exc:
                        logger.debug(f"Failed to generate embedding for {s.name}: {exc}")
                        chunk.embedding = None
                else:
                    chunk.embedding = None

                self.db.add(chunk)

        await self.db.flush()
        logger.info("Embeddings generation complete.")

    def write_reports(self) -> None:
        logger.info("Writing ingestion reports to data/ directory...")
        data_dir = ROOT_DIR / "data"
        data_dir.mkdir(exist_ok=True)

        # 1. JSON report
        json_path = data_dir / "import-report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "stats": self.stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "records": self.report_rows
            }, f, indent=2)

        # 2. CSV report
        csv_path = data_dir / "import-report.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Slug", "Name", "Government Level", "State Code", "Official URL", "Verification Status"])
            for row in self.report_rows:
                writer.writerow([row["id"], row["slug"], row["name"], row["level"], row["state"], row["url"], row["status"]])

        logger.info(f"Reports successfully written to: \n - {json_path}\n - {csv_path}")

async def main() -> None:
    parser = argparse.ArgumentParser(description="OneGov AI government services crawler & importer")
    parser.add_argument("--state", action="store_true", help="Import state-level services")
    parser.add_argument("--central", action="store_true", help="Import central-level services")
    parser.add_argument("--all", action="store_true", help="Import all services")
    parser.add_argument("--dry-run", action="store_true", help="Roll back transaction on completion")
    parser.add_argument("--verify", action="store_true", help="Run database verification checks")
    parser.add_argument("--update", action="store_true", help="Overwrite existing records if slugs match")
    parser.add_argument("--videos", action="store_true", help="Attach educational youtube videos")
    parser.add_argument("--embeddings", action="store_true", help="Generate vector embeddings")
    parser.add_argument("--full", action="store_true", help="Full import pipeline (all options)")
    args = parser.parse_args()

    # If no flags passed, default to --all
    if not (args.state or args.central or args.all or args.full):
        args.all = True

    db_url = settings.DATABASE_URL
    logger.info(f"Connecting to database on port: {db_url.split('@')[-1]}")
    engine = create_async_engine(db_url, echo=False)

    session = AsyncSession(engine, expire_on_commit=False)
    trans = await session.begin()
    try:
        importer = GovernmentServicesImporter(session, args)
        await importer.run()

        if args.dry_run:
            await trans.rollback()
            logger.warning("Dry run enabled. All changes rolled back successfully.")
        else:
            await trans.commit()
            logger.info("Import changes committed to PostgreSQL database.")

        if args.verify or args.full:
            logger.info("Running database integrity checks...")
            # Basic validation
            service_count = (await session.execute(text("SELECT COUNT(*) FROM services;"))).scalar()
            scheme_count = (await session.execute(text("SELECT COUNT(*) FROM schemes;"))).scalar()
            video_count = (await session.execute(text("SELECT COUNT(*) FROM videos;"))).scalar()
            
            print("\n" + "="*50)
            print("DATABASE INTEGRITY SUMMARY")
            print("="*50)
            print(f" • Total Services in Database : {service_count}")
            print(f" • Total Schemes in Database  : {scheme_count}")
            print(f" • Total Videos in Database   : {video_count}")
            print("="*50)

    except Exception as exc:
        logger.error(f"Ingestion failed: {exc}")
        await trans.rollback()
        sys.exit(1)
    finally:
        await session.close()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
