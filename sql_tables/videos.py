import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin



class Video(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'videos'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    video_id = sqlalchemy.Column(sqlalchemy.Integer)
    video_name = sqlalchemy.Column(sqlalchemy.String)