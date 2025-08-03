from flask import current_app
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage

from exts import db
from models import Product, ProductImage
from utilities import save_file, delete_file, ALLOWED_IMAGE_EXTENSIONS


product_images_ns = Namespace("Product Images", description="Product images management")


# Product Images serialization model
product_image_model = product_images_ns.model(
    "ProductImage",
    {
        "uuid": fields.String(readOnly=True),
        "image_url": fields.String(required=True),
        "product_id": fields.Integer(readOnly=True),
    },
)

# File Upload Parser
upload_parser = product_images_ns.parser()
upload_parser.add_argument(
    "file", location="files", type=FileStorage, required=True, help="Image file"
)
upload_parser.add_argument("product_id", type=int, required=True, help="Product ID")


@product_images_ns.route("/")
class ImageUploadResourse(Resource):
    @product_images_ns.expect(upload_parser)
    @product_images_ns.marshal_with(product_image_model)
    @product_images_ns.doc("upload_product_image")
    def post(self):
        """Upload a new product image"""
        try:
            args = upload_parser.parse_args()
            file = args["file"]
            product_id = args["product_id"]

            # Check if product exists
            product = Product.query.get(product_id)
            if not product:
                product_images_ns.abort(404, "Product not found")

            # Define upload folder
            upload_folder = current_app.config.get("PRODUCT_IMAGES_FOLDER")

            # Save file
            filename = save_file(file, upload_folder, ALLOWED_IMAGE_EXTENSIONS)
            if not filename:
                product_images_ns.abort(400, "Invalid file or file type not allowed")

            # Create image URL
            image_url = f"{upload_folder}/{filename}"

            # Create new ProductImage record
            product_image = ProductImage(image_url=image_url, product_id=product_id)

            product_image.save()

            return product_image, 201

        except Exception as e:
            db.session.rollback()
            product_images_ns.abort(500, f"Error deleting image: {str(e)}")


@product_images_ns.route("/image/<string:uuid>")
class SingleImageResource(Resource):
    @product_images_ns.marshal_with(product_image_model)
    @product_images_ns.doc("get_image")
    def get(self, uuid):
        """Get a specific image by UUID"""
        image = ProductImage.query.filter_by(uuid=uuid).first()
        if not image:
            product_images_ns.abort(404, "Image not found")
        return image

    @product_images_ns.doc("delete_image")
    def delete(self, uuid):
        """Delete a specific image"""
        image = ProductImage.query.filter_by(uuid=uuid).first()
        image.delete()
        delete_file(image.image_url)
        return {"message": "Image deleted successfully"}, 200


@product_images_ns.route("/product/<string:uuid>")
class ProductImagesResource(Resource):
    @product_images_ns.marshal_list_with(product_image_model)
    @product_images_ns.doc("get_product_images")
    def get(self, uuid):
        """Get all images for a specific product"""
        product = Product.query.get(uuid)
        if not product:
            product_images_ns.abort(404, "Product not found")

        images = ProductImage.query.filter_by(product_id=product.product_id).all()
        return images
