from flask import jsonify, request
from sql_tables.users import User
from flask import session
from flask_restful import reqparse, abort, Api, Resource
from sql_tables import db_session


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    news = session.query(User).get(user_id)
    if not news:
        abort(404, message=f"Sorry... This user {user_id} not found.")

# parser = reqparse.RequestParser()
# parser.add_argument('name', required=True)
# parser.add_argument('about', required=True)
# parser.add_argument('email', required=True)


class UsersResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict(
            only=('name', 'email', 'created_date', "telegram_auth", 'telegram_id', 'css_style'))})

    # def delete(self, user_id):
    #     abort_if_user_not_found(user_id)
    #     session = db_session.create_session()
    #     user = session.query(User).get(user_id)
    #     session.delete(user)
    #     session.commit()
    #     return jsonify({'success': 'OK'})