"""Database seed script."""
import asyncio
import sys
import os

# Support both direct run and docker exec
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# When run inside Docker container at /app
if os.path.isdir("/app"):
    sys.path.insert(0, "/app")

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionFactory
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.models.government import Ministry, Department, Category, Service, Scheme

ROLES = [
    {"name": "admin",     "description": "Platform administrator",    "is_system": True},
    {"name": "user",      "description": "Standard citizen user",     "is_system": True},
    {"name": "moderator", "description": "Content moderator",         "is_system": True},
]

USERS = [
    {"email": "admin@onegov.ai", "full_name": "Admin User", "password": "Admin@1234!", "role": "admin", "is_email_verified": True},
    {"email": "user@onegov.ai",  "full_name": "Aarav Sharma","password": "User@1234!", "role": "user",  "is_email_verified": True},
]

MINISTRIES = [
    {"name": "Ministry of External Affairs", "slug": "mea", "short_name": "MEA", "ministry_type": "central", "website": "https://mea.gov.in"},
    {"name": "Ministry of Road Transport and Highways", "slug": "morth", "short_name": "MoRTH", "ministry_type": "central", "website": "https://morth.nic.in"},
    {"name": "Unique Identification Authority of India", "slug": "uidai", "short_name": "UIDAI", "ministry_type": "central", "website": "https://uidai.gov.in"},
    {"name": "Ministry of Finance", "slug": "mof", "short_name": "MoF", "ministry_type": "central", "website": "https://finmin.nic.in"},
    {"name": "Ministry of Agriculture and Farmers Welfare", "slug": "moafw", "short_name": "MoAFW", "ministry_type": "central", "website": "https://agricoop.nic.in"},
    {"name": "Ministry of Health and Family Welfare", "slug": "mohfw", "short_name": "MoHFW", "ministry_type": "central", "website": "https://mohfw.gov.in"},
]

CATEGORIES = [
    {"name": "Identity & Documents", "slug": "identity",    "icon": "id-card",        "display_order": 1},
    {"name": "Travel & Visa",        "slug": "travel",      "icon": "plane",           "display_order": 2},
    {"name": "Finance & Tax",        "slug": "finance",     "icon": "banknote",        "display_order": 3},
    {"name": "Agriculture",          "slug": "agriculture", "icon": "wheat",           "display_order": 4},
    {"name": "Health",               "slug": "health",      "icon": "heart-pulse",     "display_order": 5},
    {"name": "Education",            "slug": "education",   "icon": "graduation-cap",  "display_order": 6},
    {"name": "Housing",              "slug": "housing",     "icon": "house",           "display_order": 7},
    {"name": "Employment",           "slug": "employment",  "icon": "briefcase",       "display_order": 8},
]

SERVICES = [
    {"name": "Passport Application (Fresh)", "slug": "passport-fresh", "short_description": "Apply for a new Indian passport.", "fee_amount": 150000, "processing_time": "15-30 working days", "official_url": "https://passportindia.gov.in", "is_online": True, "is_offline": True, "is_featured": True, "tags": ["passport","travel","mea"], "category_slug": "travel", "ministry_slug": "mea"},
    {"name": "Aadhaar Card Update", "slug": "aadhaar-update", "short_description": "Update your Aadhaar card details.", "fee_amount": 5000, "processing_time": "90 days", "official_url": "https://myaadhaar.uidai.gov.in", "is_online": True, "is_offline": True, "is_featured": True, "tags": ["aadhaar","uid","identity"], "category_slug": "identity", "ministry_slug": "uidai"},
    {"name": "Driving Licence (Fresh)", "slug": "driving-licence-fresh", "short_description": "Apply for a fresh driving licence.", "fee_amount": 60000, "processing_time": "7-30 days", "official_url": "https://sarathi.parivahan.gov.in", "is_online": True, "is_offline": True, "is_featured": True, "tags": ["driving","licence","vehicle"], "category_slug": "identity", "ministry_slug": "morth"},
    {"name": "PAN Card Application", "slug": "pan-card", "short_description": "Apply for a Permanent Account Number card.", "fee_amount": 10700, "processing_time": "15-20 working days", "official_url": "https://tin.tin.nsdl.com/pan", "is_online": True, "is_offline": True, "is_featured": True, "tags": ["pan","tax","finance"], "category_slug": "finance", "ministry_slug": "mof"},
    {"name": "Income Tax Return Filing", "slug": "itr-filing", "short_description": "File your annual income tax return.", "fee_amount": 0, "processing_time": "30-45 days for refund", "official_url": "https://eportal.incometax.gov.in", "is_online": True, "is_offline": False, "is_featured": True, "tags": ["itr","tax","income"], "category_slug": "finance", "ministry_slug": "mof"},
    {"name": "Ration Card Application", "slug": "ration-card", "short_description": "Apply for a ration card under PDS.", "fee_amount": 4500, "processing_time": "15-30 working days", "official_url": "https://nfsa.gov.in", "is_online": True, "is_offline": True, "is_featured": False, "tags": ["ration","pds","food"], "category_slug": "housing", "ministry_slug": "mof"},
]

SCHEMES = [
    {"name": "PM Kisan Samman Nidhi", "slug": "pm-kisan", "short_description": "Direct income support of ₹6,000/year to farmer families.", "scheme_type": "central", "target_beneficiary": "Farmers", "benefit_amount": "₹6,000 per year", "official_url": "https://pmkisan.gov.in", "is_featured": True, "tags": ["farmer","agriculture"], "ministry_slug": "moafw"},
    {"name": "Ayushman Bharat PM-JAY", "slug": "ayushman-bharat", "short_description": "Health insurance cover of ₹5 lakh per family per year.", "scheme_type": "central", "target_beneficiary": "BPL Families", "benefit_amount": "₹5 lakh per year", "official_url": "https://pmjay.gov.in", "is_featured": True, "tags": ["health","insurance","hospital"], "ministry_slug": "mohfw"},
    {"name": "PM Awas Yojana (Urban)", "slug": "pmay-urban", "short_description": "Credit-linked subsidy for urban housing.", "scheme_type": "central", "target_beneficiary": "Urban Poor", "benefit_amount": "Up to ₹2.67 lakh subsidy", "official_url": "https://pmaymis.gov.in", "is_featured": True, "tags": ["housing","home loan"], "ministry_slug": "mof"},
    {"name": "Sukanya Samriddhi Yojana", "slug": "sukanya-samriddhi", "short_description": "Savings scheme for girl child with 8.2% interest.", "scheme_type": "central", "target_beneficiary": "Girl Child", "benefit_amount": "8.2% p.a. interest", "official_url": "https://www.indiapost.gov.in", "is_featured": True, "tags": ["girl","savings","education"], "ministry_slug": "mof"},
    {"name": "PM Fasal Bima Yojana", "slug": "pmfby", "short_description": "Crop insurance for farmers against natural calamities.", "scheme_type": "central", "target_beneficiary": "Farmers", "benefit_amount": "Full insured crop value", "official_url": "https://pmfby.gov.in", "is_featured": False, "tags": ["crop","insurance","farmer"], "ministry_slug": "moafw"},
]


async def _get_or_create(session, model, **kwargs):
    slug = kwargs.get("slug") or kwargs.get("name")
    field = "slug" if "slug" in kwargs else "name"
    stmt = select(model).where(getattr(model, field) == slug)
    obj = (await session.execute(stmt)).scalar_one_or_none()
    if not obj:
        obj = model(**kwargs, is_active=True)
        session.add(obj)
        await session.flush()
        logger.info(f"  Created {model.__name__}: {slug}")
    return obj


async def main() -> None:
    logger.info("Starting database seed...")
    async with AsyncSessionFactory() as session:
        # Roles
        role_map = {}
        for r in ROLES:
            existing = (await session.execute(select(Role).where(Role.name == r["name"]))).scalar_one_or_none()
            if not existing:
                existing = Role(**r)
                session.add(existing)
                await session.flush()
            role_map[r["name"]] = existing

        # Users
        for u in USERS:
            if not (await session.execute(select(User).where(User.email == u["email"]))).scalar_one_or_none():
                role = role_map.get(u.pop("role", "user"))
                pwd = u.pop("password")
                user = User(**u, password_hash=hash_password(pwd), is_active=True)
                if role:
                    user.roles.append(role)
                session.add(user)
                await session.flush()
                logger.info(f"  Created user: {u['email']}")

        # Ministries
        min_map = {}
        for m in MINISTRIES:
            obj = await _get_or_create(session, Ministry, **m)
            min_map[m["slug"]] = obj

        # Categories
        cat_map = {}
        for c in CATEGORIES:
            obj = await _get_or_create(session, Category, **c)
            cat_map[c["slug"]] = obj

        # Services
        for s in SERVICES:
            existing = (await session.execute(select(Service).where(Service.slug == s["slug"]))).scalar_one_or_none()
            if not existing:
                cat = cat_map.get(s.pop("category_slug", ""))
                min_ = min_map.get(s.pop("ministry_slug", ""))
                service = Service(**s, category_id=cat.id if cat else None, is_active=True)
                session.add(service)
                await session.flush()
                logger.info(f"  Created service: {s['name']}")
            else:
                s.pop("category_slug", None); s.pop("ministry_slug", None)

        # Schemes
        for s in SCHEMES:
            existing = (await session.execute(select(Scheme).where(Scheme.slug == s["slug"]))).scalar_one_or_none()
            if not existing:
                min_ = min_map.get(s.pop("ministry_slug", ""))
                scheme = Scheme(**s, ministry_id=min_.id if min_ else None, is_active=True)
                session.add(scheme)
                await session.flush()
                logger.info(f"  Created scheme: {s['name']}")
            else:
                s.pop("ministry_slug", None)

        await session.commit()

    logger.info("\n✅ Seed complete!")
    logger.info("  Admin:  admin@onegov.ai  /  Admin@1234!")
    logger.info("  User:   user@onegov.ai   /  User@1234!")


if __name__ == "__main__":
    asyncio.run(main())
