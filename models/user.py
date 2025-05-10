from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from exts import db


# Role Model
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    customers = db.relationship('Customer', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'


# Customer Model
class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    cart_items = db.relationship('Cart',
                                 backref='customer',
                                 lazy=True,
                                 cascade="all, delete-orphan")
    orders = db.relationship('Order',
                             backref='customer',
                             lazy=True,
                             cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Customer {self.username}>'


# Audit logging
class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('Customer', backref='audit_logs')

    def __repr__(self):
        return f'<Audit {self.action} by {self.user_id}>'
