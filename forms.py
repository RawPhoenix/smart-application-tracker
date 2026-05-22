from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    SelectField,
    DateField,
    TextAreaField
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError
)

from utils import (
    strong_password,
)


class MyForm(FlaskForm):
    company = StringField(
        'Company *',
        validators=[DataRequired(), Length(max=250)],
        render_kw={"placeholder": "e.g. Google"}
    )

    role = StringField(
        'Role *',
        validators=[DataRequired(), Length(max=250)],
        render_kw={"placeholder": "e.g. Software Engineer Intern"}
    )

    application_type = SelectField(
        'Application Type *',
        choices=[
            ('Job', 'Job'),
            ('Internship', 'Internship'),
            ('Contract', 'Contract'),
            ('Freelance', 'Freelance'),
            ('Program', 'Program')
        ],
        default='Job',
        validators=[DataRequired()]
    )

    location = StringField(
        'Location *',
        validators=[Length(max=250)],
        render_kw={"placeholder": "e.g. Mumbai"}
    )

    office_address = StringField(
        'Office Address',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Google India Pvt Ltd, BKC, Bandra East, Mumbai..."}
    )

    maps_link = StringField(
        'Maps Link',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "https://maps.google...."}
    )
    work_type = SelectField(
        'Work Type',
        choices=[
            ('', 'Select Work Type'),
            ('Remote', 'Remote'),
            ('Hybrid', 'Hybrid'),
            ('On-site', 'On-site'),
            ('Flexible', 'Flexible')
        ]
    )

    applied_via = SelectField(
        'Applied Via *',
        choices=[
            ('', 'Select Platform'),
            ('LinkedIn', 'LinkedIn'),
            ('Internshala', 'Internshala'),
            ('Naukri', 'Naukri'),
            ('Indeed', 'Indeed'),
            ('Company Portal', 'Company Portal'),
            ('Referral', 'Referral'),
            ('Other', 'Other')
        ],
        validators=[DataRequired()]
    )

    applied_via_custom = StringField(
        'If Other, Specify',
        validators=[Optional(), Length(max=250)]
    )

    status = SelectField(
        'Status *',
        choices=[
            ('Applied', 'Applied'),
            ('Interview', 'Interview'),
            ('Offer', 'Offer'),
            ('Rejected', 'Rejected')
        ],
        validators=[DataRequired()]
    )

    priority = SelectField(
        'Priority',
        choices=[
            ('Low', 'Low'),
            ('Medium', 'Medium'),
            ('High', 'High')
        ],
        default='Medium'
    )

    date_applied = DateField(
        'Date Applied *',
        format='%Y-%m-%d',
        validators=[DataRequired()]
    )

    follow_up_date = DateField(
        'Follow Up Date',
        format='%Y-%m-%d',
        validators=[Optional()]
    )

    salary = StringField(
        'Salary / Stipend / Compensation',
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "e.g. ₹8 LPA / ₹20k stipend"}
    )

    application_link = StringField(
        'Application Link',
        validators=[Optional()],
        render_kw={"placeholder": "https://..."}
    )

    contact_name = StringField(
        'Contact Name',
        validators=[Optional(), Length(max=100)]
    )

    contact_email = StringField(
        'Contact Email',
        validators=[Optional(), Length(max=100)]
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=1000)],
        render_kw={"rows": 3, "placeholder": "Optional notes"}
    )

    submit = SubmitField('Submit')

    def validate_applied_via_custom(self, field):
        if self.applied_via.data == "Other" and not field.data.strip():
            raise ValidationError("Please specify platform.")


class UpdateForm(FlaskForm):
    status = SelectField(
        "Status *",
        choices=[
            ("Applied", "Applied"),
            ("Interview", "Interview"),
            ("Offer", "Offer"),
            ("Rejected", "Rejected")
        ],
        validators=[DataRequired()]
    )

    priority = SelectField(
        "Priority",
        choices=[
            ("Low", "Low"),
            ("Medium", "Medium"),
            ("High", "High")
        ],
        default="Medium"
    )

    follow_up_date = DateField(
        "Follow Up Date",
        format="%Y-%m-%d",
        validators=[Optional()]
    )

    # NEW FIELDS
    work_type = SelectField(
        "Work Type",
        choices=[
            ("Not Specified", "Not Specified"),
            ("Remote", "Remote"),
            ("Hybrid", "Hybrid"),
            ("On-site", "On-site"),
            ("Flexible", "Flexible")
        ],
        validators=[Optional()],
        default="Not Specified"
    )

    location = StringField(
        "Location",
        validators=[Optional(), Length(max=250)]
    )

    office_address = StringField(
        "Office Address",
        validators=[Optional(), Length(max=500)]
    )

    maps_link = StringField(
        "Maps Link",
        validators=[Optional(), Length(max=500)]
    )

    application_link = StringField(
        "Application Link",
        validators=[Optional(), Length(max=500)]
    )

    notes = TextAreaField(
        "Notes",
        validators=[Optional(), Length(max=1000)],
        render_kw={"rows": 4}
    )

    salary = StringField(
        "Salary / Stipend / Compensation",
        validators=[Optional(), Length(max=100)]
    )

    contact_name = StringField(
        "Contact Name",
        validators=[Optional(), Length(max=100)]
    )

    contact_email = StringField(
        "Contact Email",
        validators=[Optional(), Length(max=100)]
    )

    submit = SubmitField("Save Changes")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), strong_password])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match.")
        ]
    )
    agree_terms = BooleanField(
        "I agree to the Terms of Service and Privacy Policy",
        validators=[
            DataRequired(
                message="You must agree before creating an account."
            )
        ]
    )
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8),
            strong_password
        ]
    )

    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match.")
        ]
    )

    submit = SubmitField("Reset Password")
