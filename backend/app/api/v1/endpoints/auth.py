"""
Authentication API endpoints.
All business logic is delegated to AuthService — endpoints only handle
HTTP concerns: request parsing, response shaping, cookie management.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import OneGovError
from app.dependencies import (
    AuthServiceDep,
    CurrentUser,
    TokenServiceDep,
    OTPServiceDep,
    DbDep,
    get_client_ip,
    get_user_agent,
)
from app.middleware.rate_limit import rate_auth
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    GoogleOAuthRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    PhoneOTPRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResendOTPRequest,
    ResetPasswordRequest,
    VerifyOTPRequest,
    VerifyPhoneOTPRequest,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ───────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=ApiResponse[RegisterResponse],
    status_code=201,
    summary="Register a new account",
    description=(
        "Creates a new user account and sends a 6-digit OTP to the provided email. "
        "The account cannot be used until the email is verified via /auth/verify-otp."
    ),
)
@rate_auth("5/minute")
async def register(
    body: RegisterRequest,
    request: Request,
    auth: AuthServiceDep,
) -> ApiResponse[RegisterResponse]:
    result = await auth.register(
        full_name=body.full_name,
        email=body.email,
        password=body.password,
        phone=body.phone,
    )
    return ApiResponse.ok(
        data=result,
        message=(
            "Account created successfully. "
            f"A verification code has been sent to {body.email}."
        ),
    )


# ── Verify Email OTP ───────────────────────────────────────────────────────────

@router.post(
    "/verify-otp",
    response_model=ApiResponse[None],
    summary="Verify email with OTP",
)
@rate_auth("10/minute")
async def verify_otp(
    body: VerifyOTPRequest,
    request: Request,
    auth: AuthServiceDep,
) -> ApiResponse[None]:
    await auth.verify_email(email=body.email, otp=body.otp)
    return ApiResponse.ok(message="Email verified successfully. You can now log in.")


@router.post(
    "/resend-otp",
    response_model=ApiResponse[None],
    summary="Resend verification OTP",
)
@rate_auth("5/minute")
async def resend_otp(
    body: ResendOTPRequest,
    request: Request,
    auth: AuthServiceDep,
) -> ApiResponse[None]:
    await auth.resend_verification_otp(email=body.email)
    # Always return success — prevents email enumeration
    return ApiResponse.ok(
        message=f"If an account exists for {body.email}, a new code has been sent."
    )


# ── Login ──────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    summary="Login with email and password",
)
@rate_auth("10/minute")
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    auth: AuthServiceDep,
) -> ApiResponse[LoginResponse]:
    result = await auth.login(
        email=body.email,
        password=body.password,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    # Set refresh token in an HttpOnly cookie for XSS protection
    # The access token is returned in the body for the frontend to store in memory
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.refresh_token_expire_seconds,
        path="/api/v1/auth",  # scoped to auth routes only
    )

    return ApiResponse.ok(data=result, message="Login successful.")


# ── Google OAuth ───────────────────────────────────────────────────────────────

@router.post(
    "/google",
    response_model=ApiResponse[LoginResponse],
    summary="Login or register via Google OAuth",
    description=(
        "Pass the Google ID token obtained from the Google Sign-In SDK. "
        "Creates an account automatically if this is the first Google login."
    ),
)
@rate_auth("10/minute")
async def google_login(
    body: GoogleLoginRequest,
    request: Request,
    response: Response,
    auth: AuthServiceDep,
) -> ApiResponse[LoginResponse]:
    result = await auth.google_login(
        id_token=body.id_token,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.refresh_token_expire_seconds,
        path="/api/v1/auth",
    )
    return ApiResponse.ok(data=result, message="Google login successful.")


# ── Token Refresh ──────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=ApiResponse[dict],
    summary="Refresh the access token",
    description=(
        "Supply the refresh token (from the HttpOnly cookie or request body). "
        "Returns a new access token. The refresh token is rotated for security."
    ),
)
@rate_auth("10/minute")
async def refresh_token(
    body: RefreshTokenRequest,
    request: Request,
    response: Response,
    token_service: TokenServiceDep,
    db: DbDep,
) -> ApiResponse[dict]:
    import uuid
    from app.core.exceptions import InvalidTokenError
    from app.core.security import decode_token
    from app.repositories.user_repository import UserRepository

    # Prefer the HttpOnly cookie (XSS-safe); fall back to the body only when provided.
    refresh_token_value = body.refresh_token or request.cookies.get("refresh_token", "")
    if not refresh_token_value:
        raise InvalidTokenError("Missing refresh token. Please log in again.")

    payload = decode_token(refresh_token_value, expected_type="refresh")
    user_id_str: str = payload.get("sub", "")
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_roles(uuid.UUID(user_id_str))
    if user is None or not user.is_active or user.deleted_at is not None:
        raise InvalidTokenError("User account not active or found.")
    primary_role = user.role_names[0] if user.role_names else "user"
    new_access, new_refresh = await token_service.rotate_refresh_token(
        refresh_token=refresh_token_value, role=primary_role
    )

    # Rotate the HttpOnly refresh cookie to stay in sync with token rotation.
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.refresh_token_expire_seconds,
        path="/api/v1/auth",
    )
    return ApiResponse.ok(
        data={
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_seconds,
        },
        message="Token refreshed.",
    )


# ── Logout ─────────────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    response_model=ApiResponse[None],
    summary="Logout and revoke tokens",
)
async def logout(
    body: LogoutRequest,
    request: Request,
    response: Response,
    current_user: CurrentUser,
    auth: AuthServiceDep,
) -> ApiResponse[None]:
    # Extract the raw access token from the Authorization header
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.removeprefix("Bearer ").strip()

    await auth.logout(
        access_token=access_token,
        refresh_token=body.refresh_token,
        user_id=str(current_user.id),
    )

    # Clear the HttpOnly refresh token cookie
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")

    return ApiResponse.ok(message="Logged out successfully.")


# ── Password Management ────────────────────────────────────────────────────────

@router.post(
    "/forgot-password",
    response_model=ApiResponse[None],
    summary="Request a password reset OTP",
)
@rate_auth("5/minute")
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    auth: AuthServiceDep,
) -> ApiResponse[None]:
    await auth.forgot_password(email=body.email)
    return ApiResponse.ok(
        message=(
            f"If an account with {body.email} exists, "
            "a password reset code has been sent."
        )
    )


@router.post(
    "/reset-password",
    response_model=ApiResponse[None],
    summary="Reset password using OTP",
)
@rate_auth("10/minute")
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    auth: AuthServiceDep,
) -> ApiResponse[None]:
    await auth.reset_password(
        email=body.email, otp=body.otp, new_password=body.new_password
    )
    return ApiResponse.ok(
        message="Password reset successful. Please log in with your new password."
    )


@router.post(
    "/change-password",
    response_model=ApiResponse[None],
    summary="Change password (authenticated)",
)
@rate_auth("10/minute")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: CurrentUser,
    auth: AuthServiceDep,
) -> ApiResponse[None]:
    await auth.change_password(
        user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return ApiResponse.ok(
        message="Password changed. All other sessions have been signed out."
    )


# ── Phone Verification (Twilio) ───────────────────────────────────────────────

@router.post(
    "/phone/send-otp",
    response_model=ApiResponse[None],
    summary="Send SMS OTP to phone number via Twilio",
)
@rate_auth("10/minute")
async def send_phone_otp(
    body: PhoneOTPRequest,
    request: Request,
    otp_service: OTPServiceDep,
) -> ApiResponse[None]:
    await otp_service.generate_phone_verification_otp(body.phone)
    return ApiResponse.ok(
        message=f"Verification code sent to {body.phone} via SMS."
    )


@router.post(
    "/phone/verify-otp",
    response_model=ApiResponse[None],
    summary="Verify SMS OTP",
)
@rate_auth("10/minute")
async def verify_phone_otp(
    body: VerifyPhoneOTPRequest,
    request: Request,
    otp_service: OTPServiceDep,
) -> ApiResponse[None]:
    await otp_service.verify_phone_verification_otp(body.phone, body.otp)
    return ApiResponse.ok(message="Phone number verified successfully.")

