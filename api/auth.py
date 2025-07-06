import os
import secrets
from datetime import datetime, timedelta
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
from utilities import EmailService

auth_ns = Namespace("auth", description="User Authentication")

jwt_blocklist = set()
HOST_URL = os.environ.get("HOST_URL", "http://localhost:5000")

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

password_reset_model = auth_ns.model(
    "Password Reset",
    {
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

            # Hash the password
            password_hash = generate_password_hash(response.get("password"))

            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            verification_token_expires = datetime.utcnow() + timedelta(hours=1)

            # Register the user
            new_user = User(
                username=response.get("username"),
                email=response.get("email"),
                telephone=response.get("telephone"),
                password_hash=password_hash,
                verification_token=verification_token,
                verification_token_expires=verification_token_expires,
            )

            # Send verification email
            EmailService.send_mail(
                subject="Verify your account",
                recipients=new_user.email,
                body=f"""

                Hi {new_user.username},
                Please verify your account by clicking the link below:
                {HOST_URL}/api/auth/verify/{verification_token}
                This link will expire in 1 hour.
                """,
            )

            new_user.save()

            return make_response(
                jsonify(
                    {
                        "message": "User registered Successfully",
                        "info": f"A verification email has been sent to {new_user.email}",
                    }
                ),
                201,
            )

        except Exception as e:
            db.session.rollback()
            return make_response(
                jsonify({"message": f"Error creating user {str(e)}"}), 500
            )


@auth_ns.route("/verify/<string:token>")
class VerifyUser(Resource):

    def get(self, token):
        """Verify User Account"""
        try:
            # Get user by token
            user = User.query.filter_by(verification_token=token).first()

            # Check if the token is valid
            if not user:
                return make_response(
                    jsonify({"message": "Invalid verification token"}), 400
                )

            # Check if the token has expired
            if user.verification_token_expires < datetime.utcnow():
                # Generate new token
                new_token = secrets.token_urlsafe(32)
                new_token_expires = datetime.utcnow() + timedelta(hours=1)
                user.verification_token = new_token
                user.verification_token_expires = new_token_expires
                user.save()

                # Send the verification token
                EmailService.send_mail(
                    subject="Verify your account",
                    recipients=user.email,
                    body=f"""
                Hi {user.username},
                Please verify your account by clicking the link below:
                {HOST_URL}/api/auth/verify/{new_token}
                This link will expire in 1 hour.
                """,
                )
                return make_response(
                    jsonify(
                        {
                            "message": f"Verification token expired! A new verification email has been sent to {user.email}"
                        }
                    ),
                    400,
                )

            # Verify the user
            user.is_verified = True
            user.verification_token = None
            user.verification_token_expires = None
            user.save()

            return make_response(
                jsonify({"message": "User verified successfully!."}),
                200,
            )

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error verifying user: {str(e)}"}), 500
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

            # Check if user is verified
            if not user.is_verified:
                return make_response(
                    jsonify({"message": "Please verify your email address"}), 400
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


@auth_ns.route("/profile")
class UserProfile(Resource):

    @jwt_required()
    def get(self):
        """Get User Profile"""
        try:
            # Get current user identity
            current_user_id = get_jwt_identity()

            # Fetch user from database
            user = User.query.get(current_user_id)

            if not user:
                return make_response(jsonify({"message": "User not found"}), 404)

            # Prepare user profile data
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "telephone": user.telephone,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat(),
                "address": user.address,
            }

            return make_response(jsonify({"user": user_data}), 200)

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error fetching profile: {str(e)}"}), 500
            )

    @jwt_required()
    def put(self):
        """Update User Profile"""
        try:
            # Get current user identity
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            # Check if user exists
            if not user:
                return make_response(jsonify({"message": "User not found"}), 404)

            data = request.get_json()

            # Update the provided fields
            if "username" in data:
                existing_user = User.query.filter_by(username=data["username"]).first()
                if existing_user and existing_user.id != user.id:
                    return make_response(
                        jsonify({"message": "Username already exists"}), 400
                    )
                user.username = data["username"]

            if "email" in data:
                existing_email = User.query.filter_by(email=data["email"]).first()
                if existing_email and existing_email.id != user.id:
                    return make_response(
                        jsonify({"message": "Email already exists"}), 400
                    )
                user.email = data["email"]

            if "telephone" in data:
                existing_telephone = User.query.filter_by(
                    telephone=data["telephone"]
                ).first()
                if existing_telephone and existing_telephone.id != user.id:
                    return make_response(
                        jsonify({"message": "Telephone already exists"}), 400
                    )
                user.telephone = data["telephone"]

            if "address" in data:
                user.address = data["address"]

            user.save()

            return make_response(
                jsonify({"message": "Profile updated successfully"}), 200
            )

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error updating profile: {str(e)}"}), 500
            )

    @jwt_required()
    def delete(self):
        """Delete User Account"""
        try:
            # Get current user identity
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            # Check if user exists
            if not user:
                return make_response(jsonify({"message": "User not found"}), 404)

            # Delete user account
            user.delete()

            return make_response(
                jsonify({"message": "User account deleted successfully"}), 200
            )

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error deleting account: {str(e)}"}), 500
            )


@auth_ns.route("/password/forget")
class ForgetPassword(Resource):

    def post(self):
        """ "Send password reset token"""
        try:
            data = request.get_json()
            email = data.get("email")

            # Retrieve user and check if valid
            user = User.query.filter_by(email=email).first()
            if not user:
                return make_response(
                    jsonify(
                        {"message": "If this email exists, a reset link has been sent."}
                    ),
                    200,
                )

            # Generate a reset token
            token = secrets.token_urlsafe(32)
            token_expires = datetime.utcnow() + timedelta(hours=1)
            user.reset_token = token
            user.reset_token_expires = token_expires
            user.save()

            reset_link = f"{HOST_URL}/api/auth/password/reset/{token}"

            # Send Reset Email
            EmailService.send_mail(
                subject="Password Reset",
                recipients=user.email,
                body=f"""
                Hi {user.username},
                To reset your password, click the link below:
                {reset_link}
                This link will expire in 1 hour.
                """,
            )
            return make_response(
                jsonify({"message": f"A reset link has been sent to {user.email}"}), 200
            )

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error resetting password: {str(e)}"}), 500
            )


@auth_ns.route("/password/reset/<string:token>")
class PasswordReset(Resource):

    @auth_ns.expect(password_reset_model)
    def post(self, token):
        """Reset User Password using token"""
        try:
            # Get the user
            user = User.query.filter_by(reset_token=token).first()

            # Check if the token is valid
            if not user:
                return make_response(
                    jsonify({"message": "Invalid or expired reset token"}), 404
                )

            # Check is if the token has expired
            if user.reset_token_expires < datetime.utcnow():
                return make_response(
                    jsonify({"message": "Reset token has expired"}), 400
                )

            data = request.get_json()
            new_password = data.get("new_password")
            confirmation_password = data.get("password_confirmation")

            # Check if both passwords have been provided
            if not new_password or not confirmation_password:
                return make_response(
                    jsonify({"message": "Both password fields are required"}), 400
                )

            # Check if new password and confirmation match
            if new_password != confirmation_password:
                return make_response(
                    jsonify({"message": "Passwords do not match"}), 400
                )

            # Update user information
            user.password_hash = generate_password_hash(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            user.save()

            return make_response(
                jsonify({"message": "Password reset successfully"}), 200
            )

        except Exception as e:
            return make_response(
                jsonify({"message": f"Error resetting password: {str(e)}"}), 500
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
