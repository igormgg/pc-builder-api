from dataclasses import asdict, dataclass

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import backref, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.database import db


@dataclass
class UserModel(db.Model):

    __tablename__ = "users"

    user_id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=False)
    email: str = Column(String, unique=True, nullable=False)
    confirmed_email = Column(Boolean, nullable=False, default=False)
    password_hash = Column(String, nullable=False)
    cpf: str = Column(String(11), nullable=False, unique=True)

    addresses: list = relationship(
        "AddressModel", secondary="users_addresses", backref=backref("users")
    )

    orders: list = relationship("OrdersModel", backref=backref("user", uselist=False))

    cart = relationship("CartsModel", uselist=False)

    @property
    def password(self):
        raise AttributeError("Password cannot be accessed!")

    @password.setter
    def password(self, password_to_hash):
        self.password_hash = generate_password_hash(password_to_hash, salt_length=14)

    def verify_password(self, password_to_compare):
        return check_password_hash(self.password_hash, password_to_compare)

    def asdict(self):
        return asdict(self)
