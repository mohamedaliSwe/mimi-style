from flask_restx import fields


def create_pagination_model(api, resource_name, item_model):
    """A reusable pagination model for any resource"""
    return api.model(
        f"{resource_name.capitalize()}Pagination",
        {
            "total": fields.Integer,
            "pages": fields.Integer,
            "page": fields.Integer,
            "per_page": fields.Integer,
            resource_name.lower(): fields.List(fields.Nested(item_model)),
        },
    )
