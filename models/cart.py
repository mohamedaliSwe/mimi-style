from exts import db
from .base import Base


# Cart Model
class Cart(Base):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer,
                           db.ForeignKey('product.id'),
                           nullable=False)

    def __repr__(self):
        return f'<Cart {self.id}>'
