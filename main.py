from flask import Flask, make_response, jsonify
from flask_restx import Api, Resource

from exts import db, jwt, migrate, mail
from api import auth_ns, product_ns, categories_ns
from models import (
    Role,
    User,
    AuditLog,
    Order,
    Receipt,
    Cart,
    Product,
    Category,
    ProductImage,
)


def create_app(config):
    """
    Create and configure the Flask application.

    Args:
        config (object): Configuration object containing Flask settings.

    Returns:
        Flask: Configured Flask application instance.
    """

    app = Flask(__name__)
    app.config.from_object(config)
    api = Api(
        app,
        title="Mimi Super Style",
        version="1.0",
        description="Welcome to Mimi Super Style online store.",
        doc="/docs",
    )
    api.add_namespace(auth_ns, path="/api/auth")
    api.add_namespace(product_ns, path="/api/product")
    api.add_namespace(categories_ns, path="/api/categories")

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    @api.route("/welcome")
    class Welcome(Resource):

        def get(self):
            return make_response(
                jsonify({"message": "Welcome to Mimi Super Style!"}), 200
            )

    @app.shell_context_processor
    def make_shell_context():
        return {
            "db": db,
            "Role": Role,
            "User": User,
            "AuditLog": AuditLog,
            "Order": Order,
            "Receipt": Receipt,
            "Cart": Cart,
            "Product": Product,
            "Category": Category,
            "ProductImage": ProductImage,
        }

    return app
