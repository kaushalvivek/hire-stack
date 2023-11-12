from pydantic import BaseModel, Field
from typing import List

class AttributeScores(BaseModel):
    attribute: str = Field(...)
    score: int = Field(..., ge=0, le=100)

class CandidateEvaluation(BaseModel):
    email: str = Field(description="candidate's email")
    name: str = Field(description="candidate's name")
    attribute_scores: List[AttributeScores] = []