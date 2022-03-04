from datetime import timedelta
from http import HTTPStatus

from flask import jsonify, request, session
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from psycopg2.errors import UniqueViolation
import sqlalchemy
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Query, Session

from app.core.database import db
from app.models.carts_model import CartsModel
from app.models.user_model import UserModel


def create_user():
    data = request.get_json()

    try:
        user = UserModel(
            name=data["name"].lower().title(),
            email=data["email"].lower(),
            password=data["password"],
            cpf=data["cpf"],
        )

        db.session.add(user)
        db.session.commit()

        user_query: Query = (
            db.session.query(UserModel.user_id)
            .filter(UserModel.cpf.like(data["cpf"]))
            .one()
        )

        cart_user_id = user_query.user_id

        cart = CartsModel(user_id=cart_user_id)

        db.session.add(cart)
        db.session.commit()

    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            return {"error": "'email' or 'cpf' already exists!"}, HTTPStatus.CONFLICT
    except DataError:
        return {
            "error": "'cpf' field must contain only 11 characters!"
        }, HTTPStatus.BAD_REQUEST
    except KeyError:
        missing_fields = [
            field
            for field in ["name", "email", "password", "cpf"]
            if field not in data.keys()
        ]
        return {
            "available_fields": ["name", "email", "password", "cpf"],
            "missing_fields": missing_fields,
        }, HTTPStatus.UNPROCESSABLE_ENTITY

    return jsonify(user), HTTPStatus.CREATED


def login():

    data = request.get_json()
    data = {key: val for key, val in data.items() if key in ["email", "password"]}

    missing_fields = [x for x in ["email", "password"] if x not in data.keys()]

    if missing_fields:
        return {"missing fields": missing_fields}, HTTPStatus.BAD_REQUEST

    for key, val in data.items():
        if type(val) is not str:
            return {"error": f"{{{key}}} value must be string"}, HTTPStatus.BAD_REQUEST

    email = data.get("email")
    password = data.get("password")

    user: UserModel = UserModel.query.filter_by(email=email.lower()).first()

    if not user:
        return {"error": "email not found"}, HTTPStatus.NOT_FOUND

    if user.verify_password(password):
        access_token = create_access_token(
            identity=user, expires_delta=timedelta(days=1)
        )
        return {"access_token": access_token}
    else:
        return {"error": "invalid password"}, HTTPStatus.FORBIDDEN


@jwt_required()
def get_user():
    current_user_token = request.headers.get("Authorization")
    current_user = get_jwt_identity()
    user = UserModel.query.get(current_user.get("user_id")).asdict()
    user.pop("password_hash")
    return jsonify(user)


@jwt_required()
def update_user():

    data = request.get_json()

    current_user = get_jwt_identity()
    user = UserModel.query.get(current_user["user_id"])

    data = {
        key: val
        for key, val in data.items()
        if key in ["email", "password", "cpf", "name"]
    }

    user.name = data.get("name") or user.name
    user.cpf = data.get("cpf") or user.cpf
    user.email = data.get("email") or user.email

    if data.get("password"):
        user.password = data.get("password")

    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        db.session.close()
        if isinstance(e.orig, UniqueViolation):
            return (
                jsonify({"error": e.args[0][e.args[0].find("Key") : -2]}),
                HTTPStatus.CONFLICT,
            )

    user_dict = {
        key: val
        for key, val in user.asdict().items()
        if key not in ["password_hash", "addresses", "orders"]
    }

    return jsonify(user_dict)
