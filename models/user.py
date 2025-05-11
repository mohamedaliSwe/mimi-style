from datetime import datetime
from exts import db
from .base import Base


# Role Model
class Role(Base):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'


# user Model
class User(Base):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(300))
    telephone = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    cart_items = db.relationship('Cart',
                                 backref='User',
                                 lazy=True,
                                 cascade="all, delete-orphan")
    orders = db.relationship('Order',
                             backref='User',
                             lazy=True,
                             cascade="all, delete-orphan")

    def __repr__(self):
        return f'<user {self.username}>'


# Audit logging
class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<Audit {self.action} by {self.user_id}>'
