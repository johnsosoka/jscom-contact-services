from enum import Enum
from pydantic import BaseModel, Field

class ContactCategory(str, Enum):
    GENERAL_INQUIRY = "general_inquiry"
    TECHNICAL_INQUIRY = "tech_inquiry"
    CORRECTION_REQUEST = "correction_request"
    PROJECT_COLLABORATION = "project_collaboration"
    CONSULTING_REQUEST = "consulting_request"
    SPEAKING_INVITATION = "speaking_invitation"
    JOB_OPPORTUNITY = "job_opportunity"
    PERSONAL_CONNECTION = "personal_connection"
    FEEDBACK = "feedback"
    SPAM = "spam"
    OTHER = "other"

class ContactPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ContactClassification(BaseModel):
    contact_category: ContactCategory = Field(..., description="The contact category of the contact.")
    contact_priority: ContactPriority = Field(..., description="The priority of the contact.")
    confidence_score: float = Field(..., description="The confidence score of the classification.", ge=0.0, le=1.0)
