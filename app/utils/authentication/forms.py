# formulaire de l'application

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, FileField
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms.validators import DataRequired, Length, ValidationError, Regexp
from .models import User

# formulaire d'enregistrement
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Regexp(r'^(?=.*[A-Z])(?=.*\d).{8,}$',
                                message="Le mot de passe doit contenir au moins 8 caractères, une majuscule et un chiffre.")
                            ])
    submit = SubmitField('Register')
        
    def validate_email(self, email): # verifier si l'email existe
        user = User.query.filter_by(email=email.data).first()

        if user:
            raise ValidationError('That email is already registered. Please choose a different one.')
        
# formulaire de connexion 
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField("Connexion")

# formulaire d'entréprise
class EntrepriseForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    docs = FileField('Document', validators=[FileAllowed(['pdf']), FileSize(max_size=10 * 1024 * 1024) ])
    password = PasswordField('Password', validators=[DataRequired(), Regexp(r'^(?=.*[A-Z])(?=.*\d).{8,}$',
                                message="Le mot de passe doit contenir au moins 8 caractères, une majuscule et un chiffre.")
                            ])
    image = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'])])
    submit = SubmitField("Ajouter")

# formulaire de mise a jour du nom d'appelation
class CallingForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField("Connexion")

# formulaire de mise a jour du nom d'appelation de l'administrateur
class Calling2Form(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    docs = FileField('Document', validators=[FileAllowed(['pdf'])])
    submit = SubmitField("Connexion")

class AskForm(FlaskForm):
    question = StringField('Votre question', validators=[DataRequired()])
    submit = SubmitField('Envoyer')