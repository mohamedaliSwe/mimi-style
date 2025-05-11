from flask import request, make_response, jsonify
from werkzeug.security import generate_password_hash
from flask_restx import fields, Namespace, Resource
from exts import db
from models import User

auth_ns = Namespace("auth", description="User Authentication")

registration_model = auth_ns.model(
    "User registration", {
        "username": fields.String(required=True),
        "email": fields.String(required=True),
        "telephone": fields.String(required=True),
        "password": fields.String(required=True),
        "password_confirmation": fields.String(required=True)
    })

login_model = auth_ns.model(
    "User Login", {
        "email": fields.String(required=True),
        "password": fields.String(required=True)
    })

password_reset = auth_ns.model(
    "Password Reset", {
        "old_password": fields.String(required=True),
        "new_password": fields.String(required=True),
        "password_confirmation": fields.String(required=True)
    })


@auth_ns.route("/signup")
class UserResource(Resource):

    @auth_ns.expect(registration_model)
    def post(self):
        """Register New User"""
        try:
            response = request.get_json()

            # Check for required fields
            required_fields = [
                "username", "email", "telephone", "password",
                "password_confirmation"
            ]
            for field in required_fields:
                if not response.get(field):
                    return make_response(
                        jsonify({"message": f"{field} is required"}), 400)

            # Check if user exists
            if User.query.filter_by(email=response.get("email")).first():
                return make_response(
                    jsonify({"message": "Email already registered"}), 400)

            if User.query.filter_by(username=response.get("username")).first():
                return make_response(jsonify({"message": "User exists"}), 400)

            if User.query.filter_by(
                    telephone=response.get("telephone")).first():
                return make_response(
                    jsonify({"message": "Number already registered"}), 400)

            # check if password and confirmation match
            if response["password"] != response["password_confirmation"]:
                return make_response(
                    jsonify({"message": "Passwords do not match"}), 400)

            # Hash the passowrd
            password_hash = generate_password_hash(response["password"])

            # Register the user
            new_user = User(username=response["username"],
                            email=response["email"],
                            telephone=response["telephone"],
                            password_hash=password_hash)

            new_user.save()
            return make_response(
                jsonify({"message": "User registered Successfully"}))

        except Exception as e:
            db.session.rollback()
            return make_response(
                jsonify({"message": f"Error creating user {str(e)}"}), 500)
