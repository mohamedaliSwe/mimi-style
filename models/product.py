from datetime import datetime
from exts import db


# Product Model
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float)
    in_stock = db.Column(db.Integer, nullable=False)
    product_picture = db.Column(db.String(1000))
    flash_sale = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    carts = db.relationship('Cart', backref='product', lazy=True)
    orders = db.relationship('Order', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.product_name}>'
