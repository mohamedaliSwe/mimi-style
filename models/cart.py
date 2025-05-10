from datetime import datetime
from exts import db


# Cart Model
class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    customer_id = db.Column(db.Integer,
                            db.ForeignKey('customer.id'),
                            nullable=False)
    product_id = db.Column(db.Integer,
                           db.ForeignKey('product.id'),
                           nullable=False)

    def __repr__(self):
        return f'<Cart {self.id}>'
