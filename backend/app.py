from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db import get_db
import crud
import schemas

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "pars-wms backend ok"}

@app.post("/products", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, product)
