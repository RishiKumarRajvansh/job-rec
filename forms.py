from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class WorkExperienceForm(FlaskForm):
    company = StringField('Company Name', validators=[DataRequired()])
    title = StringField('Job Title', validators=[DataRequired()])
    start_date = StringField('Start Date (MM/YYYY)', validators=[DataRequired()])
    end_date = StringField('End Date (MM/YYYY or "Present")')
    description = TextAreaField('Job Description')
    current_job = BooleanField('Current Job')
    submit = SubmitField('Add Work Experience')

class EducationForm(FlaskForm):
    institution = StringField('Institution Name', validators=[DataRequired()])
    degree = StringField('Degree', validators=[DataRequired()])
    field_of_study = StringField('Field of Study')
    start_date = StringField('Start Date (MM/YYYY)')
    end_date = StringField('End Date (MM/YYYY or "Present")')
    gpa = StringField('GPA (optional)')
    description = TextAreaField('Additional Information')
    submit = SubmitField('Add Education')

class ProfileForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    location = StringField('Location', 
                        description='City, State or Remote')
    skills = TextAreaField('Skills (comma separated)')
    certifications = TextAreaField('Certifications (comma separated)')
    summary = TextAreaField('Professional Summary')
    submit = SubmitField('Update Profile')

class JobSearchForm(FlaskForm):
    query = StringField('Job Title or Keywords', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    submit = SubmitField('Search Jobs')

class ResumeUploadForm(FlaskForm):
    resume = FileField('Resume', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'docx', 'txt'], 'Only PDF, DOCX, and TXT files are allowed!')
    ])
    submit = SubmitField('Upload and Analyze')
