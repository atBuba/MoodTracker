from pydantic import BaseModel


class MemeRequest(BaseModel):
    context: str


class MemeData(BaseModel):
    image_url: str


class MemeResponse(BaseModel):
    data: MemeData
