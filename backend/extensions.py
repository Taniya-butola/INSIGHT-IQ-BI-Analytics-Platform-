"""
Shared Flask extension instances.

Kept in their own module (rather than inside app.py) so blueprints can
import `db`, `bcrypt`, `jwt` without triggering a circular import with
the app factory.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
