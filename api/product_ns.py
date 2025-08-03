from flask import current_app
from flask_restx import Resource, Namespace, fields
from werkzeug.datastructures import FileStorage

from exts import db
from models import Category, Product, ProductImage
from utilities import save_file, delete_file, ALLOWED_IMAGE_EXTENSIONS

product_ns = Namespace("products", description="Products Management")

# Categories serialization model
category_model = product_ns.model(
    "Category",
    {
        "uuid": fields.String(readonly=True),
        "name": fields.String(required=True),
    },
)

# Product Images serialization model
product_image_model = product_ns.model(
    "ProductImage",
    {
        "uuid": fields.String(readonly=True),
        "image_url": fields.String(required=True),
        "product_id": fields.Integer(readonly=True),
    },
)

# Product serialization model
product_model = product_ns.model(
    "Product",
    {
        "uuid": fields.String(readonly=True),
        "product_name": fields.String(required=True),
        "description": fields.String(),
        "current_price": fields.Float(required=True),
        "previous_price": fields.Float(),
        "in_stock": fields.Integer(required=True),
        "flash_sale": fields.Boolean(default=False),
        # Fixed: Should be Nested, not List
        "category": fields.Nested(category_model, readonly=True),
        "images": fields.List(fields.Nested(product_image_model), readonly=True),
    },
)

# Product creation model (for input)
product_create_model = product_ns.model(
    "ProductCreate",
    {
        "product_name": fields.String(required=True, min_length=1, max_length=100),
        "description": fields.String(max_length=500),
        "current_price": fields.Float(required=True, min=0),
        "previous_price": fields.Float(min=0),
        "in_stock": fields.Integer(required=True, min=0),
        "flash_sale": fields.Boolean(default=False),
        "category_id": fields.String(required=True),
    },
)

# Parsers for request validation
product_parser = product_ns.parser()
product_parser.add_argument(
    "product_name", type=str, required=True, help="Product name (1-100 characters)"
)
product_parser.add_argument(
    "description", type=str, help="Product description (max 500 characters)"
)
product_parser.add_argument(
    "current_price", type=float, required=True, help="Current price (must be positive)"
)
product_parser.add_argument(
    "previous_price", type=float, help="Previous price (optional)"
)
product_parser.add_argument(
    "in_stock", type=int, required=True, help="Stock quantity (must be non-negative)"
)
product_parser.add_argument(
    "flash_sale", type=bool, default=False, help="Flash sale status"
)
product_parser.add_argument(
    "category_id", type=str, required=True, help="Category UUID"
)

product_update_parser = product_ns.parser()
product_update_parser.add_argument(
    "product_name", type=str, help="Product name (1-100 characters)"
)
product_update_parser.add_argument(
    "description", type=str, help="Product description (max 500 characters)"
)
product_update_parser.add_argument(
    "current_price", type=float, help="Current price (must be positive)"
)
product_update_parser.add_argument(
    "previous_price", type=float, help="Previous price (optional)"
)
product_update_parser.add_argument(
    "in_stock", type=int, help="Stock quantity (must be non-negative)"
)
product_update_parser.add_argument("flash_sale", type=bool, help="Flash sale status")
product_update_parser.add_argument("category_id", type=str, help="Category UUID")


def validate_product_data(args):
    """Validate product data"""
    errors = []

    # Validate product name
    if args.get("product_name"):
        if len(args["product_name"].strip()) < 1:
            errors.append("Product name cannot be empty")
        elif len(args["product_name"]) > 100:
            errors.append("Product name cannot exceed 100 characters")

    # Validate description
    if args.get("description") and len(args["description"]) > 500:
        errors.append("Description cannot exceed 500 characters")

    # Validate prices
    if args.get("current_price") is not None and args["current_price"] < 0:
        errors.append("Current price must be non-negative")

    if args.get("previous_price") is not None and args["previous_price"] < 0:
        errors.append("Previous price must be non-negative")

    # Validate stock
    if args.get("in_stock") is not None and args["in_stock"] < 0:
        errors.append("Stock quantity must be non-negative")

    return errors


@product_ns.route("/")
class ProductsResource(Resource):

    @product_ns.expect(product_parser)
    @product_ns.doc("create_product")
    def post(self):
        """Add a new product"""
        try:
            args = product_parser.parse_args()

            # Validate input data
            validation_errors = validate_product_data(args)
            if validation_errors:
                product_ns.abort(
                    400, f"Validation errors: {', '.join(validation_errors)}"
                )

            # Check if category exists
            category = Category.query.filter_by(uuid=args["category_id"]).first()
            if not category:
                product_ns.abort(404, "Category not found")

            # Check if product name already exists
            existing_product = Product.query.filter_by(
                product_name=args["product_name"]
            ).first()
            if existing_product:
                product_ns.abort(400, "Product with this name already exists")

            # Create new product
            new_product = Product(
                product_name=args["product_name"].strip(),
                description=args.get("description", "").strip(),
                current_price=args["current_price"],
                previous_price=args.get("previous_price"),
                in_stock=args["in_stock"],
                flash_sale=args.get("flash_sale", False),
                category_id=category.id,
            )

            new_product.save()

            return {
                "message": "Product created successfully",
                "data": {
                    "uuid": new_product.uuid,
                    "product_name": new_product.product_name,
                    "description": new_product.description,
                    "current_price": new_product.current_price,
                    "previous_price": new_product.previous_price,
                    "in_stock": new_product.in_stock,
                    "flash_sale": new_product.flash_sale,
                    "category": {"uuid": category.uuid, "name": category.name},
                },
            }, 201

        except Exception as e:
            db.session.rollback()
            product_ns.abort(500, f"Error creating product: {str(e)}")

    @product_ns.marshal_list_with(product_model)
    @product_ns.doc("get_all_products")
    def get(self):
        """Get all products"""
        try:
            products = Product.query.all()
            return products, 200
        except Exception as e:
            product_ns.abort(500, f"Error fetching products: {str(e)}")


@product_ns.route("/<string:uuid>")
class SingleProductResource(Resource):
    """Resource for managing individual products"""

    @product_ns.marshal_with(product_model)
    @product_ns.doc("get_product")
    def get(self, uuid):
        """Get a specific product by UUID"""
        try:
            product = Product.query.filter_by(uuid=uuid).first()
            if not product:
                product_ns.abort(404, "Product not found")
            return product, 200
        except Exception as e:
            product_ns.abort(500, f"Error fetching product: {str(e)}")

    @product_ns.expect(product_update_parser)
    @product_ns.doc("update_product")
    def put(self, uuid):
        """Update a specific product"""
        try:
            product = Product.query.filter_by(uuid=uuid).first()
            if not product:
                product_ns.abort(404, "Product not found")

            args = product_update_parser.parse_args()

            # Validate input data
            validation_errors = validate_product_data(args)
            if validation_errors:
                product_ns.abort(
                    400, f"Validation errors: {', '.join(validation_errors)}"
                )

            # Update fields if provided
            if args.get("product_name"):
                # Check for duplicate name (excluding current product)
                existing = (
                    Product.query.filter_by(product_name=args["product_name"])
                    .filter(Product.uuid != uuid)
                    .first()
                )
                if existing:
                    product_ns.abort(400, "Product with this name already exists")
                product.product_name = args["product_name"].strip()

            if args.get("description") is not None:
                product.description = args["description"].strip()

            if args.get("current_price") is not None:
                product.current_price = args["current_price"]

            if args.get("previous_price") is not None:
                product.previous_price = args["previous_price"]

            if args.get("in_stock") is not None:
                product.in_stock = args["in_stock"]

            if args.get("flash_sale") is not None:
                product.flash_sale = args["flash_sale"]

            if args.get("category_id"):
                category = Category.query.filter_by(uuid=args["category_id"]).first()
                if not category:
                    product_ns.abort(404, "Category not found")
                product.category_id = category.id

            product.save()

            return {"message": "Product updated successfully"}, 200

        except Exception as e:
            db.session.rollback()
            product_ns.abort(500, f"Error updating product: {str(e)}")

    @product_ns.doc("delete_product")
    def delete(self, uuid):
        """Delete a specific product"""
        try:
            product = Product.query.filter_by(uuid=uuid).first()
            if not product:
                product_ns.abort(404, "Product not found")

            # Delete associated images from filesystem
            for image in product.images:
                delete_file(image.image_url)

            # Delete product (cascade should handle images in DB)
            db.session.delete(product)
            db.session.commit()

            return {"message": "Product deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            product_ns.abort(500, f"Error deleting product: {str(e)}")


@product_ns.route("/category/<string:category_uuid>")
class ProductsByCategoryResource(Resource):
    """Resource for getting products by category"""

    @product_ns.marshal_list_with(product_model)
    @product_ns.doc("get_products_by_category")
    def get(self, category_uuid):
        """Get all products in a specific category"""
        try:
            category = Category.query.filter_by(uuid=category_uuid).first()
            if not category:
                product_ns.abort(404, "Category not found")

            products = Product.query.filter_by(category_id=category.id).all()
            return products, 200

        except Exception as e:
            product_ns.abort(500, f"Error fetching products by category: {str(e)}")


@product_ns.route("/flash-sale")
class FlashSaleProductsResource(Resource):
    """Resource for getting flash sale products"""

    @product_ns.marshal_list_with(product_model)
    @product_ns.doc("get_flash_sale_products")
    def get(self):
        """Get all products on flash sale"""
        try:
            products = Product.query.filter_by(flash_sale=True).all()
            return products, 200
        except Exception as e:
            product_ns.abort(500, f"Error fetching flash sale products: {str(e)}")
