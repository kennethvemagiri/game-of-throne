import os

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from backend.services.gmail_service import SCOPES, save_credentials_from_flow

router = APIRouter()


def _build_flow(state: str | None = None) -> Flow:
    client_config = {
        "web": {
            "client_id": os.getenv("GMAIL_CLIENT_ID", ""),
            "client_secret": os.getenv("GMAIL_CLIENT_SECRET", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.getenv("GMAIL_REDIRECT_URI", "")],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=os.getenv("GMAIL_REDIRECT_URI", ""),
    )
    if state:
        flow.state = state
    return flow


@router.get("/auth/google/login")
def gmail_auth_start():
    flow = _build_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(url=authorization_url)


@router.get("/auth/google/callback")
def gmail_auth_callback(request: Request):
    code = request.query_params.get("code", "")
    flow = _build_flow()

    if os.getenv("VERCEL") != "1":
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow.fetch_token(code=code)

    save_credentials_from_flow(flow.credentials)
    return RedirectResponse(url="/?gmail=connected")
