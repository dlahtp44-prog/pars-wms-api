from pydantic import BaseModel

class ProductCreate(BaseModel):
    sku: str
    name: str
    unit: str

class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    unit: str

    class Config:
        orm_mode = True
