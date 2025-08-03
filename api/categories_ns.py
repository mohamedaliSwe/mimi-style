from flask import jsonify, request, make_response
from flask_restx import Namespace, Resource, fields

from exts import db
from models import Category
from utilities import create_pagination_model
from .product_ns import product_model

categories_ns = Namespace("categories", description="Categories Management")

# Category Serialization model
category_model = categories_ns.model(
    "Category",
    {"uuid": fields.String(read_only=True), "name": fields.String(required=True)},
)


# Category product pagination model
category_product_pagination_model = create_pagination_model(
    categories_ns, "products", product_model
)

#


@categories_ns.route("/")
class CategoryList(Resource):

    @categories_ns.marshal_list_with(category_model)
    def get(self):
        """List all categories"""
        return Category.query.all()

    @categories_ns.expect(category_model)
    def post(self):
        """Create a new category"""
        try:
            data = request.get_json()
            category_name = data.get("name").strip().lower()

            # Check if category name is empty
            if not category_name:
                return make_response(
                    jsonify({"message": "Category name is required"}), 400
                )

            # Check if category exists
            existing_category = Category.query.filter_by(name=category_name).first()
            if existing_category:
                return make_response(
                    jsonify({"message": "Category already exists"}), 400
                )

            # Save the category
            new_category = Category(name=category_name)
            new_category.save()
            return make_response(
                jsonify({"message": "Category created successfully"}), 201
            )

        except Exception as e:
            db.session.rollback()
            return make_response(
                jsonify({"message": f"Error creating category {str(e)}"}), 500
            )


@categories_ns.route("/<string:uuid>")
class CategoryResource(Resource):

    def get(self, uuid):
        """Get category by uuid"""
        try:
            # Check if category is valid
            category = Category.query.filter_by(uuid=uuid).first()
            if not category:
                return make_response(jsonify({"message": "Invalid category"}), 400)

            return make_response(jsonify({"name": category.name}), 200)

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error retrieving category {str(e)}"}), 500
            )

    def put(self, uuid):
        """Update category name"""
        try:
            data = request.get_json()
            category_name = data.get("name").strip().lower()

            # Check if category is valid
            category = Category.query.filter_by(uuid=uuid).first()
            if not category:
                return make_response(jsonify({"message": "Invalid category"}), 400)

            # Check if new category name already exist
            existing_category = Category.query.filter_by(name=category_name).first()
            if existing_category:
                return make_response(
                    jsonify({"message": "Category already exists"}), 400
                )

            # Update Category
            category.update(name=category_name)
            return make_response(
                jsonify({"message": "Category name updated successfully"}), 200
            )

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error updating category {str(e)}"}), 500
            )

    def delete(self, uuid):
        """Delete a category"""
        try:
            # Check if category is valid
            category = Category.query.filter_by(uuid=uuid).first()
            if not category:
                return make_response(jsonify({"message": "Invalid category"}), 400)

            # Delete category
            category.delete()
            return make_response(
                jsonify({"message": "Category deleted successfully"}), 200
            )

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error deleting category {str(e)}"}), 500
            )


@categories_ns.doc(params={"page": "Page number", "per_page": "Items per page"})
@categories_ns.route("/<string:uuid>/products")
class CategoryProducts(Resource):

    @categories_ns.marshal_with(category_product_pagination_model)
    def get(self, uuid):
        """ "List all products in a category"""
        try:
            # Check if category is valid
            category = Category.query.filter_by(uuid=uuid).first()
            if not category:
                return make_response(jsonify({"message": "Invalid category"}), 400)

            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))

            pagination = category.products(
                page=page, per_page=per_page, error_out=False
            )

            return {
                "total": pagination.total,
                "pages": pagination.pages,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "products": pagination.items,
            }

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error loading products {str(e)}"}), 500
            )
