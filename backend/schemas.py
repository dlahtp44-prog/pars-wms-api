from pydantic import BaseModel

class ProductCreate(BaseModel):
    sku: str
    name: str
    unit: str

class ProductResponse(ProductCreate):
    id: int

    class Config:
        orm_mode = True
