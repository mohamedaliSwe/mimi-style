from flask import current_app, request, make_response, jsonify
from flask_restx import Resource, Namespace, fields

from exts import db
from models import Category, Product, ProductImage
from utilities import save_file, ALLOWED_IMAGE_EXTENSIONS

product_ns = Namespace("products", description="Products Management")

# Product Images serialization model
product_image_model = product_ns.model(
    "ProductImage",
    {
        "uuid": fields.String(readOnly=True),
        "image_url": fields.String(required=True),
    },
)

# Categories serialization model
category_model = product_ns.model(
    "Category",
    {
        "id": fields.Integer(readOnly=True),
        "name": fields.String(required=True),
    },
)

# Product serialization model
product_model = product_ns.model(
    "Product",
    {
        "uuid": fields.String(readOnly=True),
        "product_name": fields.String(required=True),
        "description": fields.String(),
        "current_price": fields.Float(required=True),
        "previous_price": fields.Float(),
        "in_stock": fields.Integer(required=True),
        "flash_sale": fields.Boolean(default=False),
        "category_id": fields.Integer(required=True),
        "images": fields.List(fields.Nested(product_image_model)),
    },
)


@product_ns.route("/")
class PrductsResource(Resource):

    @product_ns.expect(product_model)
    def post(self):
        """ "Add a new product"""
        try:
            data = request.get_json()

            product_name = data.get("product_name")
            description = data.get("description")
            current_price = data.get("current_price")
            previous_price = data.get("previous_price")
            in_stock = data.get("in_stock")
            flash_sale = data.get("flash_sale", "false").lower() == "true"
            category_id = data.get("category_id")
            file = data.get("image")

            # Upload the file
            filename = save_file(file, UPLOAD_FOLDER, ALLOWED_IMAGE_EXTENSIONS)
            if not filename:
                return make_response(jsonify({"message": "Invalid file format"}), 400)

        except Exception as e:
            db.session.rollback()
            return make_response(
                jsonify({"message": f"Error creating user {str(e)}"}), 500
            )
