"""
OneGov AI — Contact Form Endpoint
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, EmailStr

from app.dependencies import DbDep, OptionalCurrentUser, get_client_ip
from app.models.activity import ContactMessage
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/contact", tags=["Contact"])


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    subject: str
    message: str


@router.post("", response_model=ApiResponse[dict])
async def submit_contact(
    body: ContactRequest,
    request: Request,
    db: DbDep,
    current_user: OptionalCurrentUser = None,
) -> ApiResponse[dict]:
    """Submit a citizen inquiry, feedback, or grievance."""
    msg = ContactMessage(
        name=body.name,
        email=body.email,
        phone=body.phone,
        subject=body.subject,
        message=body.message,
        user_id=current_user.id if current_user else None,
        ip_address=get_client_ip(request),
        status="new",
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return ApiResponse.ok(
        data={"id": str(msg.id), "status": msg.status},
        message="Thank you! Your message has been received. Our support team will get back to you shortly.",
    )
