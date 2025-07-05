from exts import db
from .base import Base


# Order Model
class Order(Base):
    __tablename__ = "order"
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="pending")
    payment_id = db.Column(db.String(255), nullable=True)
    receipt_url = db.Column(db.String(1000))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey(
        "product.id"), nullable=False)

    def __repr__(self):
        return f"<Order {self.id} - {self.status}>"


# Receipt Model for tracking generated receipts
class Receipt(Base):
    __tablename__ = "receipt"
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)

    order = db.relationship(
        "Order", backref=db.backref("receipt", uselist=False))

    def __repr__(self):
        return f"<Receipt {self.filename}>"
