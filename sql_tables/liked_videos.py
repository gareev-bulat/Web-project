import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin


class Liked_video(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'liked_videos'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    video_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("videos.id"))
    video = orm.relation('Video')
