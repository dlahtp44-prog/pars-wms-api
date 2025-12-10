from sqlalchemy.orm import Session
from models import Product
from schemas import ProductCreate

def create_product(db: Session, product: ProductCreate):
    db_product = Product(
        sku=product.sku,
        name=product.name,
        unit=product.unit,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
