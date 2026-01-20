from pydantic import BaseModel
from typing import List

class StyleConfig(BaseModel):
    name: str
    prompt_payload: str
    negative_payload: str
    loras: List[str]

class GenerationResult(BaseModel):
    positive: str
    negative: str