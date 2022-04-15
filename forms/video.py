from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField, IntegerField, FileField
from wtforms.validators import DataRequired


class VideoDownloadForm(FlaskForm):
    title = StringField('Название видео', validators=[DataRequired()])
    photo = FileField('Превью', validators=[FileRequired(), FileAllowed(['jpg', 'png'], '.jpg or .png')])
    video = FileField('Видео', validators=[FileRequired(), FileAllowed(['WMV', 'mp4', "MPEG-4", "MP4"], '.wmv or .mp4 or .mpeg-4')])
    submit = SubmitField('Загрузить')