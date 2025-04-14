from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length

class SystemNotificationForm(FlaskForm):
    title = StringField('Notification Title', validators=[DataRequired(), Length(min=3, max=100)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=500)])
    link = StringField('Link (Optional)', validators=[Length(max=255)])
    all_users = BooleanField('Send to All Users', default=True)
    submit = SubmitField('Send Notification') 