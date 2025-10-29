from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, PasswordField, SelectField, 
                    EmailField, TextAreaField, DateField, HiddenField, BooleanField)
from wtforms.validators import (DataRequired, Length, Regexp, ValidationError, 
                               Optional, EqualTo, Email)
from wtforms.widgets import TextArea
from werkzeug.security import check_password_hash
from flask_login import current_user
from database import User, db
from country_data import COUNTRY_CHOICES


class LimitedTextAreaWidget(TextArea):
    """Character-limited textarea widget"""
    def __call__(self, field, **kwargs):
        kwargs.setdefault('maxlength', 2000)
        kwargs.setdefault('data-char-limit', 2000)
        return super().__call__(field, **kwargs)


class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=1, max=15, message="Username must be between 1 and 15 characters."),
        Regexp(r'^[A-Za-z0-9]+$', 
               message="Username can only contain letters (A-Z, a-z) and numbers (0-9). No spaces or special characters allowed.")
    ])
    email = EmailField('Email Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long."),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@$!%*?&()_\-+=]{8,}$', 
               message="Password must contain at least one lowercase letter, one uppercase letter, and one digit (minimum 8 characters). Special characters (@$!%*?&()_-+=) are allowed.")
    ])
    student = SelectField('Are you a student?', 
                         validators=[DataRequired()], 
                         choices=[(0, "No"), (1, 'Yes')])
    agreement = SelectField('Do you agree Terms of Use?', 
                           validators=[DataRequired()], 
                           choices=[(1, 'Agree'), (0, "Disagree")])
    submit = SubmitField('Create New Account', render_kw={'class': 'btn btn-dark'})

    def validate_username(self, username):
        # Check for @ symbol (prevents @handle names)
        if '@' in username.data:
            raise ValidationError('Username cannot contain @ symbol.')
        
        # Check if username already exists
        user = db.session.execute(db.select(User).where(User.username == username.data)).scalar()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = db.session.execute(db.select(User).where(User.email == email.data)).scalar()
        if user:
            raise ValidationError('This email address is already registered.')

    def validate_agreement(self, agreement):
        if int(agreement.data) != 1:
            raise ValidationError('You must agree to the Terms of Use.')


class LoginForm(FlaskForm):
    """Login form"""
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login', render_kw={'class': 'btn btn-dark'})


class PersonalInformationForm(FlaskForm):
    """Personal information update form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=1, max=15, message="Username must be between 1 and 15 characters."),
        Regexp(r'^[A-Za-z0-9]+$', 
               message="Username can only contain letters (A-Z, a-z) and numbers (0-9). No spaces or special characters allowed.")
    ])
    email = EmailField('Email Address', validators=[DataRequired()])
    student = SelectField('Are you a student?', 
                         choices=[(0, 'No'), (1, 'Yes')],
                         validators=[DataRequired()],
                         coerce=int)
    birthday = DateField('Birthday', validators=[Optional()])
    pronouns = SelectField('Pronouns',
                          choices=[
                              ('', '---'),
                              ('he/him', 'He/Him'),
                              ('she/her', 'She/Her'),
                              ('they/them', 'They/Them'),
                              ('other', 'Other/Prefer not to say')
                          ],
                          validators=[Optional()])
    location = SelectField(
        'Location',
        choices=[('', 'Select your country or region')] + COUNTRY_CHOICES,
        validators=[Optional()],
        default=''
    )
    submit = SubmitField('Save', render_kw={'class': 'btn btn-dark'})

    def validate_username(self, username):
        # Check for @ symbol (prevents @handle names)
        if '@' in username.data:
            raise ValidationError('Username cannot contain @ symbol.')
        
        # Check if username is different from current username and already taken
        if username.data != current_user.username:
            user = db.session.execute(db.select(User).where(User.username == username.data)).scalar()
            if user:
                raise ValidationError('This username is already taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data and email.data != current_user.email:
            user = db.session.execute(db.select(User).where(User.email == email.data)).scalar()
            if user:
                raise ValidationError('This email address is already registered.')


class ChangePasswordForm(FlaskForm):
    """Password change form"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long."),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@$!%*?&()_\-+=]{8,}$', 
               message="Password must contain at least one lowercase letter, one uppercase letter, and one digit (minimum 8 characters). Special characters (@$!%*?&()_-+=) are allowed.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), 
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change', render_kw={'class': 'btn btn-dark'})

    def validate_current_password(self, current_password):
        # Check both regular password and temporary password
        password_valid = check_password_hash(current_user.password, current_password.data)
        
        # Also check temporary password if it exists and hasn't expired
        temp_password_valid = False
        if current_user.temp_password:
            temp_password_valid = check_password_hash(current_user.temp_password, current_password.data)
            # Check if temp password hasn't expired
            if temp_password_valid and current_user.temp_password_expires:
                try:
                    import datetime as dt
                    expires = dt.datetime.strptime(current_user.temp_password_expires, '%Y-%m-%d %H:%M:%S')
                    if expires < dt.datetime.now():
                        temp_password_valid = False
                except:
                    temp_password_valid = False
        
        if not password_valid and not temp_password_valid:
            raise ValidationError('Current password is incorrect.')


class PasswordResetRequestForm(FlaskForm):
    """Password reset request form"""
    email = EmailField('Email Address', validators=[DataRequired()])
    submit = SubmitField('Send Reset Email', render_kw={'class': 'btn btn-dark'})

    def validate_email(self, email):
        user = db.session.execute(db.select(User).where(User.email == email.data)).scalar()
        if not user:
            raise ValidationError('No account found with this email address.')


class ContactForm(FlaskForm):
    """Contact form"""
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email Address', validators=[DataRequired()])
    category = SelectField('Category', 
                          choices=[
                              ("General Inquiries", "General Inquiries"), 
                              ("Technical Issues", "Technical Issues"), 
                              ("Feature Requests", "Feature Requests"), 
                              ("Account Deletion", "Account Deletion"), 
                              ("Others", "Others")
                          ], 
                          validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()], widget=LimitedTextAreaWidget())
    submit = SubmitField('Submit', render_kw={'class': 'btn btn-dark'})


class ContactConfirmForm(FlaskForm):
    """Contact confirmation form"""
    name = HiddenField()
    email = HiddenField()
    category = HiddenField()
    message = HiddenField()
    confirm = SubmitField('Send Message', render_kw={'class': 'btn btn-dark'})
    edit = SubmitField('Edit Message', render_kw={'class': 'btn btn-outline-secondary'})


class AccountDeletionForm(FlaskForm):
    """Account deletion form"""
    submit = SubmitField('Delete My Account', render_kw={'class': 'btn btn-danger'})


class AnswerForm(FlaskForm):
    """Answer form with character limit"""
    answer = TextAreaField('Your Answer', 
                          validators=[
                              DataRequired(),
                              Length(max=2000, message="Answer must be less than 2000 characters.")
                          ],
                          widget=LimitedTextAreaWidget(),
                          render_kw={'placeholder': 'Tell me about yourself'})
    is_public = BooleanField('Make this answer public', default=True)
    submit = SubmitField('Submit Answer')


class ReportForm(FlaskForm):
    """Report form"""
    reason = SelectField('Reason for reporting',
                        choices=[
                            ('spam', 'Spam or promotional content'),
                            ('harassment', 'Harassment or bullying'),
                            ('inappropriate', 'Inappropriate content'),
                            ('offensive', 'Offensive language'),
                            ('misinformation', 'False or misleading information'),
                            ('other', 'Other')
                        ],
                        validators=[DataRequired()])
    additional_info = TextAreaField('Additional Information (Optional)',
                                   render_kw={'placeholder': 'Provide additional details if needed'})
    submit = SubmitField('Submit', render_kw={'class': 'btn btn-dark'})


class DeleteAnswerForm(FlaskForm):
    """CSRF-protected delete form"""
    pass


class AdminAddForm(FlaskForm):
    """Form to add administrator"""
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Add Admin', render_kw={'class': 'btn btn-dark'})


class AdminRemoveForm(FlaskForm):
    """Form to remove administrator"""
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Remove Admin', render_kw={'class': 'btn btn-danger'})
