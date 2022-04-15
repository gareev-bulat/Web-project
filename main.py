from flask import Flask
from flask import render_template, redirect, request, abort
from flask_login import LoginManager
from flask_login.utils import login_user, login_required, current_user, logout_user

import os

from sql_tables import db_session
from sql_tables.users import User
from sql_tables.videos import Video
from forms.user import RegisterForm, LoginForm
from forms.video import VideoDownloadForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
   db_sess = db_session.create_session()
   last_id = os.listdir("static//data//channels")
   for channel in range(int(last_id[-1]), 0, -1):
       count_of_videos = len(os.listdir(f"static//data//channels//{channel}//videos"))
       temp = []
       for video in range(count_of_videos - 1, -1, -1):
           path = f"static//data//channels//{channel}//videos//{video}//photo.png"
           title = db_sess.query(Video).filter(Video.user_id == channel and Video.video_id == count_of_videos).first()
           temp.append({"video": video, "channel": channel, "path": path, "name": title.video_name})
   return render_template('index.html', videos=temp)

@app.route("/profile")
def my_profile():
    if current_user.is_authenticated:
        return redirect(f"/profile/{current_user.id}")
    else:
        return redirect("/")


@app.route("/profile/<int:user_id>")
def profile(user_id):
    if current_user.is_authenticated:
        if current_user.id == user_id:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == user_id).first()
            return render_template('profile.html', form=user)
        else:
            return f"Профиль человека под id {user_id}"


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        os.makedirs(f"static\\data\\channels\\{user.id}")
        os.makedirs(f"static\\data\\channels\\{user.id}\\videos")
        f = form.photo.data
        f.save(os.path.join(f"static\\data\\channels\\{user.id}\\mini_image.png"))
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/upload_video", methods=['GET', 'POST'])
@login_required
def video_uploading():
    form = VideoDownloadForm()
    if form.validate_on_submit():
        f_video = form.video.data
        f_photo = form.photo.data
        count_of_videos = len(os.listdir(f"static//data//channels//{current_user.id}//videos"))
        os.mkdir(f"static\\data\\channels\\{current_user.id}\\videos\\{count_of_videos}")
        f_video.save(f"static\\data\\channels\\{current_user.id}\\videos\\{count_of_videos}\\videotitle.mp4")
        f_photo.save(f"static\\data\\channels\\{current_user.id}\\videos\\{count_of_videos}\\photo.png")
        db_sess = db_session.create_session()
        video = Video(
            user_id=current_user.id,
            video_id=count_of_videos,
            video_name=form.title.data
        )
        db_sess.add(video)
        db_sess.commit()
        return redirect('/profile')
    return render_template('upload_video.html', title='Загрузка видео', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.db")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()