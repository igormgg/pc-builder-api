from http import HTTPStatus

from flask import jsonify, request
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from app.core.database import db
from app.models.category_model import CategoryModel
from app.models.product_model import ProductModel


def create_product():
    session = db.session
    data = request.get_json()

    try:

        if not type(data["model"]) == str:
            return {"Error": "The model must be string!"}, HTTPStatus.BAD_REQUEST
        if not type(data["img"]) == str:
            return {"Error": "The img must be string!"}, HTTPStatus.BAD_REQUEST
        if not type(data["price"]) == float:
            return {"Error": "The price must be float!"}, HTTPStatus.BAD_REQUEST
        if not type(data["description"]) == str:
            return {"Error": "The description must be string!"}, HTTPStatus.BAD_REQUEST
        if not type(data["category"]) == str:
            return {"Error": "The category must be string!"}, HTTPStatus.BAD_REQUEST

        data["category"] = data["category"].title()

        category = data.pop("category")

        category_model: CategoryModel = CategoryModel.query.filter_by(
            name=category
        ).first()

        data["category_id"] = category_model.category_id

        product = ProductModel(**data)

        session.add(product)
        session.commit()

        return jsonify(product), HTTPStatus.CREATED

    except IntegrityError as error:
        if isinstance(error.orig, UniqueViolation):
            return {"Error": "Product already exists!"}, HTTPStatus.CONFLICT

    except KeyError:
        missing_fields = [
            field
            for field in ["model", "img", "price", "description", "category"]
            if field not in data.keys()
        ]
        return {
            "available_fields": ["model", "img", "price", "description", "category"],
            "missing_fields": missing_fields,
        }, HTTPStatus.UNPROCESSABLE_ENTITY

    except TypeError:
        return {"Error": "The valid key is only model!"}, HTTPStatus.CONFLICT
