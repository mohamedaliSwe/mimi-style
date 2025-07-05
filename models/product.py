from exts import db
from .base import Base


# Categories Model
class Category(Base):
    __tablename__ = "categories"
    name = db.Column(db.String(100), unique=True, nullable=False)

    products = db.relationship("Product", backref="category", lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


# Product Images Model
class ProductImage(Base):
    __tablename__ = "product_images"
    image_url = db.Column(db.String(255), nullable=False)

    product_id = db.Column(db.Integer, db.ForeignKey(
        "product.id"), nullable=False)

    def __repr__(self):
        return f"<ProductImage {self.image_url}>"


# Product Model
class Product(Base):
    __tablename__ = "product"
    product_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float)
    in_stock = db.Column(db.Integer, nullable=False)
    flash_sale = db.Column(db.Boolean, default=False)

    category_id = db.Column(db.Integer, db.ForeignKey(
        "categories.id"), nullable=False)

    images = db.relationship(
        "ProductImage", backref="product", lazy=True, cascade="all, delete-orphan"
    )
    carts = db.relationship("Cart", backref="product", lazy=True)
    orders = db.relationship("Order", backref="product", lazy=True)

    def __repr__(self):
        return f"<Product {self.product_name}>"
