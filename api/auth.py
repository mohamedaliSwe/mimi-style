from flask import request, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
    jwt_required,
)
from flask_restx import fields, Namespace, Resource
from exts import db
from models import User

auth_ns = Namespace("auth", description="User Authentication")

jwt_blocklist = set()

registration_model = auth_ns.model(
    "User registration",
    {
        "username": fields.String(required=True),
        "email": fields.String(required=True),
        "telephone": fields.String(required=True),
        "password": fields.String(required=True),
        "password_confirmation": fields.String(required=True),
    },
)

login_model = auth_ns.model(
    "User Login",
    {"email": fields.String(required=True), "password": fields.String(required=True)},
)

password_reset = auth_ns.model(
    "Password Reset",
    {
        "old_password": fields.String(required=True),
        "new_password": fields.String(required=True),
        "password_confirmation": fields.String(required=True),
    },
)


@auth_ns.route("/signup")
class UserResource(Resource):

    @auth_ns.expect(registration_model)
    def post(self):
        """Register New User"""
        try:
            response = request.get_json()

            # Check for required fields
            required_fields = [
                "username",
                "email",
                "telephone",
                "password",
                "password_confirmation",
            ]
            for field in required_fields:
                if not response.get(field):
                    return make_response(
                        jsonify({"message": f"{field} is required"}), 400
                    )

            # Check if user exists
            if User.query.filter_by(email=response.get("email")).first():
                return make_response(
                    jsonify({"message": "Email already registered"}), 400
                )

            if User.query.filter_by(username=response.get("username")).first():
                return make_response(jsonify({"message": "User exists"}), 400)

            if User.query.filter_by(telephone=response.get("telephone")).first():
                return make_response(
                    jsonify({"message": "Number already registered"}), 400
                )

            # check if password and confirmation match
            if response.get("password") != response.get("password_confirmation"):
                return make_response(
                    jsonify({"message": "Passwords do not match"}), 400
                )

            # Hash the passowrd
            password_hash = generate_password_hash(response.get("password"))

            # Register the user
            new_user = User(
                username=response.get("username"),
                email=response.get("email"),
                telephone=response.get("telephone"),
                password_hash=password_hash,
            )

            new_user.save()
            return make_response(jsonify({"message": "User registered Successfully"}))

        except Exception as e:
            db.session.rollback()
            return make_response(
                jsonify({"message": f"Error creating user {str(e)}"}), 500
            )


@auth_ns.route("/login")
class UserLogin(Resource):

    @auth_ns.expect(login_model)
    def post(self):
        """Logs in user"""
        try:
            response = request.get_json()

            # Check if both all fields are provide
            if not response.get("email") or not response.get("password"):
                return make_response(
                    jsonify({"message": "Both fields are required"}), 400
                )

            # Check if user is registered
            user = User.query.filter_by(email=response.get("email")).first()
            if not user:
                return make_response(
                    jsonify({"message": "User is not registered"}), 400
                )

            # Check if password and email is correct
            if not check_password_hash(user.password_hash, response["password"]):
                return make_response(jsonify({"message": "Incorrect password"}), 400)

            # Create identity with additional claims
            identity = str(user.id)
            additional_claims = {"username": user.username}

            # Generate token
            access_token = create_access_token(
                identity=identity, additional_claims=additional_claims
            )

            refresh_token = create_refresh_token(
                identity=identity, additional_claims=additional_claims
            )

            return make_response(
                jsonify(
                    {
                        "message": "Login successful",
                        "data": {
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                        },
                    }
                ),
                200,
            )

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error loggin in user {str(e)}"}), 500
            )


@auth_ns.route("/logout")
class LogoutUser(Resource):

    @jwt_required()
    def post(self):
        """Logout User"""
        jti = get_jwt()["jti"]
        jwt_blocklist.add(jti)
        return make_response(jsonify({"message": "Logged out successfully"}))


@auth_ns.route("/refresh")
class RefreshToken(Resource):

    @jwt_required(refresh=True)
    def post(self):
        """Generate a new access token from a refresh token"""
        try:
            # Get current user identity and claims
            current_user = get_jwt_identity()
            current_claims = get_jwt()

            # Extract claims to carry into new access token
            additional_claims = {
                "username": current_claims.get("username"),
            }

            # Generate new access token
            new_access_token = create_access_token(
                identity=current_user, additional_claims=additional_claims
            )

            return make_response(jsonify({"access_token": new_access_token}), 200)

        except Exception as e:
            return make_response(
                jsonify(
                    {"status": "error", "message": f"Error refreshing token: {str(e)}"}
                ),
                500,
            )
