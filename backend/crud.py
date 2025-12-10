from .models import Product

def create_product(db, product):
    db_product = Product(
        sku=product.sku,
        name=product.name,
        unit=product.unit
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

