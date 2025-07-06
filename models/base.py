import uuid
from datetime import datetime
from exts import db


class Base(db.Model):
    """Defines a base model"""

    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow
    )

    # Save method
    def save(self):
        db.session.add(self)
        db.session.commit()

    # Update method
    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.session.commit()

    # Delete method
    def delete(self):
        db.session.delete(self)
        db.session.commit()
