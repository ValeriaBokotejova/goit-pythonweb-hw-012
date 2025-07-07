from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.roles import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    avatar = Column(String, nullable=True)

    role = Column(
        SQLAEnum(UserRole, name="role", create_constraint=True, native_enum=False),
        default=UserRole.USER,
        nullable=False,
    )
    contacts = relationship("Contact", back_populates="owner", cascade="all, delete")
