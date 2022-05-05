from flask import Flask
from flask import render_template, redirect, request, abort
from flask_login import LoginManager
from flask_login.utils import login_user, login_required, current_user, logout_user

import os

from sql_tables import db_session
from sql_tables.users import User
from sql_tables.videos import Video
from sql_tables.liked_videos import Liked_video
from forms.user import RegisterForm, LoginForm
from forms.video import VideoDownloadForm
import json
import requests


# API_TRANSLATER = 'http://translate.google.ru/translate_a/t?client=x&text={Привет}&sl={ru}&tl={en}'

#info = requests.get(API_TRANSLATER)
#answer = info.json()
#print(answer)
#print(response)
#{textToTranslate}, собственно и есть то, что нам надо перевести (с предложениями справлялось)
#Ответ приходит в виде строки json, который нужно распарсить и получить translatedText = myJSON.sentences[0].trans;

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        if request.form['like']:
            line = request.form["like"]
            line = line.split("//")
            creator = line[3]
            vd_ch = line[4].split("/")[1]

            db_sess = db_session.create_session()

            a = db_sess.query(Video).filter(Video.video_id == vd_ch and Video.user_id == creator).first()
            vd_id = a.id

            br = Liked_video(user_id = current_user.id, video_id = vd_id)
            db_sess.add(br)
            db_sess.commit()


        if request.form['dislike']:
            line = request.form["like"]
            line = line.split("//")
            creator = line[3]
            vd_ch = line[4].split("/")[1]

            db_sess = db_session.create_session()

            a = db_sess.query(Video).filter(Video.video_id == vd_ch and Video.user_id == creator).first()
            vd_id = a.id

            br = Liked_video(user_id = current_user.id, video_id = vd_id)
            db_sess.add(br)
            db_sess.commit()


    db_sess = db_session.create_session()
    channels = [user.id for user in db_sess.query(User).all()]
    temp = []
    for channel in channels:
        count_of_videos = len(os.listdir(f"static//data//channels//{channel}//videos"))
        for video in range(count_of_videos - 1, -1, -1):
            path = f"static//data//channels//{channel}//videos//{video}//photo.png"
            title = db_sess.query(Video).filter(Video.user_id == channel, Video.video_id == video).first()
            video_path = f"static//data//channels//{str(channel)}//videos/{str(video)}//videotitle.mp4"

            a = db_sess.query(Video).filter(Video.video_id == video and Video.user_id == channel).first()
            vd_id = a.id
            a = db_sess.query(Liked_video).filter(Liked_video.video_id == vd_id and Liked_video.user_id == current_user.id).first()
            if a:
                is_liked = True
            else:
                is_liked = False

            temp.append({"video_path": video_path, "video": video, "channel": channel, "path": path, "name": title.video_name, "is_liked": is_liked})
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
            videos = db_sess.query(Video).filter(Video.video_id == user_id)
            video_path = f"static//data//channels//{str(user)}//videos/{str(videos)}//videotitle.mp4"
            return render_template('profile.html', form=user, media=video_path)
        else:
            return f"Профиль человека под id {user_id}"


@app.route("/video/<int:video_id>")
def video(video_id):
    pass


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
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        os.makedirs(f"static\\data\\channels\\{user.id}")
        os.makedirs(f"static\\data\\channels\\{user.id}\\videos")
        f = form.photo.data
        f.save(os.path.join(f"static\\data\\channels\\{user.id}\\mini_image.png"))
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    pass


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
