from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, Email



class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit_login = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    agree_terms = BooleanField("I agree to the Terms of Services and Privacy policy", validators=[DataRequired()])
    submit_register = SubmitField('Create Account')