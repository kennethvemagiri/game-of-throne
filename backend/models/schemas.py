from pydantic import BaseModel


class ReviewBody(BaseModel):
    status: str


class ClassifyBody(BaseModel):
    subject: str = ""
    body: str = ""
    sender: str = ""


class SyncDemoBody(BaseModel):
    subject: str = ""
    body: str = ""
    sender: str = ""
    email_id: str | None = None


class SuggestedJobSyncBody(BaseModel):
    source: str = "indeed"
    company: str
    role: str
    url: str
    snippet: str = ""
