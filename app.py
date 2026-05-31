# =========================
# STANDARD LIBRARY
# =========================
import csv
import os
from collections import Counter
from datetime import date, timedelta
from io import StringIO

# =========================
# ENVIRONMENT
# =========================
from dotenv import load_dotenv
# =========================
# FLASK
# =========================
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    jsonify,
    Response
)
# =========================
# FLASK LOGIN
# =========================
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
# =========================
# DATABASE / SQLALCHEMY
# =========================
from sqlalchemy import func
# =========================
# SECURITY
# =========================
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# =========================
# EXTENSIONS
# =========================
from extensions import (
    db,
    mail,
    login_manager,
)
# =========================
# FORMS
# =========================
from forms import (
    MyForm,
    UpdateForm,
    RegisterForm,
    LoginForm,
    ForgotPasswordForm,
    ResetPasswordForm
)
from models.job_application import JobApplication
# =========================
# MODELS
# =========================
from models.user import User
# =========================
# OAUTH
# =========================
from oauth import init_oauth, oauth
# =========================
# SERVICES / STORAGE
# =========================
from services.application_manager import ApplicationManager
# =========================
# UTILITIES
# =========================
from utils import (
    verify_reset_token,
    send_reset_email,
    is_strong_password
)

manager = ApplicationManager()

# =========================
# APP SETUP
# =========================
load_dotenv()

app = Flask(__name__)

# =========================
# CONFIGURATION
# =========================
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///applications.db"
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True
}

app.config["REMEMBER_COOKIE_DURATION"] = (
    timedelta(days=30)
)

# Mail Configuration
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")

app.config["MAIL_PORT"] = int(
    os.getenv("MAIL_PORT", 587)
)

app.config["MAIL_USE_TLS"] = (
        os.getenv("MAIL_USE_TLS", "True") == "True"
)

app.config["MAIL_USERNAME"] = os.getenv(
    "MAIL_USERNAME"
)

app.config["MAIL_PASSWORD"] = os.getenv(
    "MAIL_PASSWORD"
)

app.config["MAIL_DEFAULT_SENDER"] = os.getenv(
    "MAIL_DEFAULT_SENDER"
)

app.config["MAIL_TIMEOUT"] = 10

# =========================
# EXTENSIONS
# =========================
db.init_app(app)

mail.init_app(app)

login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

init_oauth(app)

# =========================
# STORAGE / MANAGER
# =========================


# =========================
# DATABASE SETUP
# =========================
with app.app_context():
    db.create_all()


# =========================
# LOGIN MANAGER
# =========================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    status_filter = request.args.get("status")
    search_query = request.args.get("search")

    query = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        JobApplication.is_archived == False
    )

    # Status Filter
    if status_filter:
        query = query.filter(JobApplication.status == status_filter)

    # Search
    if search_query and search_query.strip():
        search = f"%{search_query.strip()}%"
        query = query.filter(
            JobApplication.company_name.ilike(search) |
            JobApplication.role.ilike(search)
        )

    # Main Table Data
    applications = query.order_by(
        JobApplication.date_applied.desc(),
        JobApplication.application_id.desc()
    ).all()

    today = date.today()

    # Follow Up Alerts
    followups_due = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        JobApplication.is_archived == False,
        JobApplication.follow_up_date == today,
        JobApplication.status.in_(["Applied", "Interview"])
    ).count()

    overdue_followups = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        JobApplication.is_archived == False,
        JobApplication.follow_up_date < today,
        JobApplication.status.in_(["Applied", "Interview"])
    ).count()

    # Summary Stats
    total_apps = len(applications)

    applied = sum(1 for app in applications if app.status == "Applied")
    interviews = sum(1 for app in applications if app.status == "Interview")
    offers = sum(1 for app in applications if app.status == "Offer")
    rejected = sum(1 for app in applications if app.status == "Rejected")
    withdrawn = sum(1 for app in applications if app.status == "Withdrawn")

    # New Stats
    jobs = sum(1 for app in applications if app.application_type == "Job")
    internships = sum(1 for app in applications if app.application_type == "Internship")

    high_priority = sum(1 for app in applications if app.priority == "High")
    remote_roles = sum(1 for app in applications if app.work_type == "Remote")

    return render_template(
        "index.html",
        applications=applications,
        today=today,

        current_filter=status_filter,

        total_apps=total_apps,
        applied=applied,
        interviews=interviews,
        offers=offers,
        rejected=rejected,
        withdrawn=withdrawn,

        followups_due=followups_due,
        overdue_followups=overdue_followups,

        jobs=jobs,
        internships=internships,
        high_priority=high_priority,
        remote_roles=remote_roles
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = MyForm()

    if not form.date_applied.data:
        form.date_applied.data = date.today()

    if form.validate_on_submit():

        # Work Type Default
        if not form.work_type.data:
            form.work_type.data = "Not Specified"

        # Location Logic
        if not form.location.data.strip():

            if form.work_type.data == "Remote":
                form.location.data = "Remote"

            elif form.work_type.data == "Not Specified":
                form.location.data = "Not Specified"

        # Require Location for On-site / Hybrid
        if form.work_type.data in ["On-site", "Hybrid"] and not form.location.data.strip():
            flash("Location is required for On-site / Hybrid jobs.", "danger")
            return render_template("add.html", form=form)

        # Applied Via Logic
        if form.applied_via.data == "Other":

            if form.applied_via_custom.data:
                applied_via_value = form.applied_via_custom.data.strip().title()

            else:
                form.applied_via_custom.errors.append(
                    "Please specify platform."
                )

                return render_template(
                    "add.html",
                    form=form,
                    current_user=current_user
                )

        else:
            applied_via_value = form.applied_via.data

        # Follow Up Logic
        if form.status.data in ["Offer", "Rejected", "Withdrawn"]:
            follow_up = None
        else:
            follow_up = (
                    form.follow_up_date.data
                    or form.date_applied.data + timedelta(days=7)
            )

        # Application Link Cleanup
        link = form.application_link.data

        if link:
            link = link.strip()

            if not link.startswith(("http://", "https://")):
                link = "https://" + link

        # Maps Link Cleanup
        maps_link = form.maps_link.data

        if maps_link:
            maps_link = maps_link.strip()

            if not maps_link.startswith(("http://", "https://")):
                maps_link = "https://" + maps_link

        # Office Address
        office_address = form.office_address.data.strip() if form.office_address.data else ""

        manager.add_application(
            company_name=form.company.data,
            role=form.role.data,
            location=form.location.data,

            applied_via=applied_via_value,
            status=form.status.data,

            date_applied=form.date_applied.data,
            follow_up_date=follow_up,

            user_id=current_user.id,

            application_type=form.application_type.data,
            work_type=form.work_type.data,
            priority=form.priority.data,

            application_link=link,
            notes=form.notes.data,

            salary=form.salary.data,
            contact_name=form.contact_name.data,
            contact_email=form.contact_email.data,

            office_address=office_address,
            maps_link=maps_link,

            last_checked=date.today()
        )

        return redirect(url_for("home"))

    return render_template(
        "add.html",
        form=form,
        current_user=current_user
    )


@app.route("/update/<int:application_id>", methods=["GET", "POST"])
@login_required
def update(application_id):
    application = manager.find_by_id(application_id, current_user.id)

    if application.status == "Withdrawn":
        flash("Withdrawn applications cannot be edited.", "warning")
        return redirect(url_for("home"))

    form = UpdateForm(obj=application)

    if form.validate_on_submit():

        # Main Fields
        application.status = form.status.data
        application.priority = form.priority.data
        application.work_type = form.work_type.data

        # Location Logic
        if not form.location.data.strip():

            if form.work_type.data == "Remote":
                application.location = "Remote"

            else:
                application.location = ""

        else:
            application.location = form.location.data.strip()

        # Require location for On-site / Hybrid
        if form.work_type.data in ["On-site", "Hybrid"] and not application.location:
            flash("Location is required for On-site / Hybrid jobs.", "danger")
            return render_template(
                "update.html",
                form=form,
                application=application
            )

        # Follow Up Logic
        if form.status.data in ["Offer", "Rejected", "Withdrawn"]:
            application.follow_up_date = None

        elif form.follow_up_date.data:
            application.follow_up_date = form.follow_up_date.data

        else:
            application.follow_up_date = date.today() + timedelta(days=7)

        # Application Link Cleanup
        link = form.application_link.data.strip() if form.application_link.data else ""

        if link and not link.startswith(("http://", "https://")):
            link = "https://" + link

        application.application_link = link

        # Maps Link Cleanup
        # Office Address / Maps Logic

        if form.work_type.data == "Remote":

            application.office_address = None
            application.maps_link = None

        else:

            application.office_address = (
                form.office_address.data.strip()
                if form.office_address.data
                else ""
            )

            maps = (
                form.maps_link.data.strip()
                if form.maps_link.data
                else ""
            )

            if maps and not maps.startswith(("http://", "https://")):
                maps = "https://" + maps

            application.maps_link = maps
        application.notes = form.notes.data
        application.salary = form.salary.data
        application.contact_name = form.contact_name.data
        application.contact_email = (
            form.contact_email.data.strip()
            if form.contact_email.data
            else ""
        )

        # Last Activity
        application.last_checked = date.today()

        db.session.commit()

        flash("Application updated successfully.", "success")

        return redirect(
            url_for(
                "application_details",
                id=application.application_id
            )
        )

    return render_template(
        "update.html",
        form=form,
        application=application,
        current_user=current_user
    )


@app.route("/withdraw/<int:application_id>", methods=["POST", "GET"])
@login_required
def withdraw(application_id):
    manager.withdraw_application(application_id)
    return redirect(url_for('home'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            send_reset_email(user)

        flash(
            'If an account with that email exists, a password reset link has been sent.',
            'info'
        )
        return redirect(url_for('login'))

    return render_template('forgot_password.html', form=form)


from flask_mail import Message


@app.route("/test-mail")
def test_mail():
    msg = Message(
        subject="SMTP Test",
        recipients=["shettyjithesh41@gmail.com"]
    )

    msg.body = "Testing email from Render"

    mail.send(msg)

    return "Mail sent"


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)

    if not email:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.password_hash = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        db.session.commit()

        flash('Your password has been reset successfully.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)


# =========================
# GOOGLE OAUTH ROUTES
# =========================

@app.route("/auth/google")
def google_login():
    redirect_uri = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token["userinfo"]

    email = user_info["email"]
    google_id = user_info["sub"]
    picture = user_info.get("picture")

    # 1. Check if this Google account already exists
    user = User.query.filter_by(google_id=google_id).first()

    # 2. If not, check if a local account exists with same email
    if not user:
        user = User.query.filter_by(email=email).first()

        if user:
            # Link Google account to existing local account
            user.google_id = google_id
            user.auth_provider = "google"
            user.profile_picture = picture

    # 3. If still no user, create new Google user
    if not user:
        base_username = email.split("@")[0].lower()
        username = base_username
        counter = 1

        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1

        user = User(
            username=username,
            email=email,
            password_hash=None,
            google_id=google_id,
            auth_provider="google",
            profile_picture=picture
        )
        db.session.add(user)

    db.session.commit()

    login_user(user)
    flash(f"Welcome, {user.username} 👋", "success")

    return redirect(url_for("home"))


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():

        # Check existing email
        existing_email = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()

        # Check existing username
        existing_username = db.session.execute(
            db.select(User).where(User.username == form.username.data)
        ).scalar_one_or_none()

        if existing_email:
            flash("You've already signed up with that email. Please log in.", "warning")
            return redirect(url_for("login"))

        if existing_username:
            flash("Username already taken.", "warning")
            return render_template(
                "register.html",
                form=form,
                current_user=current_user
            )
        if not is_strong_password(form.password.data):
            flash(
                "Password must contain at least 8 characters, including uppercase, lowercase, number, and special character.",
                "danger"
            )
            return render_template("register.html", form=form)
        # Hash password
        hashed_password = generate_password_hash(
            form.password.data,
            method="pbkdf2:sha256",
            salt_length=8
        )

        # Create user
        new_user = User(
            email=form.email.data,
            username=form.username.data,
            password_hash=hashed_password,
            auth_provider="local"
        )

        db.session.add(new_user)
        db.session.commit()

        # Automatically log in after registration
        login_user(new_user)

        flash(f"Welcome, {new_user.username}! 🎉", "success")
        return redirect(url_for("home"))

    return render_template(
        "register.html",
        form=form,
        current_user=current_user
    )


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        user = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()

        password = form.password.data

        # User not found
        if not user:
            flash("No account found with that email address.", "danger")
            return redirect(url_for("register"))

        # Google-only account trying to login with password
        if not user.password_hash:
            flash(
                "This account was created with Google. Please use 'Continue with Google'.",
                "warning"
            )
            return redirect(url_for("login"))

        # Incorrect password
        if not check_password_hash(user.password_hash, password):
            flash("Incorrect password.", "danger")
            return redirect(url_for("login"))

        # Successful login
        login_user(user, remember=form.remember.data)
        flash(f"Welcome back, {user.username} 👋", "success")

        return redirect(url_for("home"))

    return render_template(
        "login.html",
        form=form,
        current_user=current_user
    )


@app.route("/analytics")
@login_required
def analytics():
    # ACTIVE APPLICATIONS ONLY
    apps = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        JobApplication.is_archived == False
    ).all()

    # ALL APPLICATIONS (timeline includes archived)
    all_apps = JobApplication.query.filter(
        JobApplication.user_id == current_user.id
    ).all()

    today = date.today()

    days = [
        today - timedelta(days=i)
        for i in range(29, -1, -1)
    ]

    labels = [day.strftime("%b %d") for day in days]

    date_counts = Counter(
        app.date_applied.strftime("%b %d")
        for app in all_apps
    )

    counts = [date_counts.get(label, 0) for label in labels]

    total = len(apps)

    interviews = sum(
        1 for a in apps if a.status == "Interview"
    )

    offers = sum(
        1 for a in apps if a.status == "Offer"
    )

    rejected = sum(
        1 for a in apps if a.status == "Rejected"
    )

    withdrawn = sum(
        1 for a in apps if a.status == "Withdrawn"
    )

    applied = sum(
        1 for a in apps if a.status == "Applied"
    )

    # ---------------- RATES ----------------
    interview_rate = round(
        (interviews / total) * 100, 1
    ) if total else 0

    offer_rate = round(
        (offers / total) * 100, 1
    ) if total else 0

    responded = (
            interviews +
            offers +
            rejected +
            withdrawn
    )

    response_rate = round(
        (responded / total) * 100, 1
    ) if total else 0

    pending_total = applied + interviews

    if total:
        avg_days_open = round(
            sum(
                (today - a.date_applied.date()).days
                for a in apps
            ) / total
        )
    else:
        avg_days_open = 0

    # ==============================
    # PLATFORM ANALYTICS
    # ==============================

    platform_data = (
        db.session.query(
            JobApplication.applied_via,
            func.count(JobApplication.application_id)
        )
        .filter(
            JobApplication.user_id == current_user.id,
            JobApplication.is_archived == False,
            JobApplication.applied_via != None
        )
        .group_by(JobApplication.applied_via)
        .all()
    )

    # Standard platforms to display individually
    standard_platforms = {
        "LinkedIn",
        "Indeed",
        "Internshala",
        "Naukri",
        "Company Portal"
    }

    platform_counter = {}

    for platform, count in platform_data:

        # Group custom entries into "Other"
        if platform not in standard_platforms:
            platform = "Other"

        # Merge counts
        platform_counter[platform] = (
                platform_counter.get(platform, 0) + count
        )

    # Final labels and counts
    platform_labels = list(platform_counter.keys())
    platform_counts = list(platform_counter.values())

    # Top platform
    top_platform = None
    top_platform_count = 0

    if platform_counter:
        top_platform = max(
            platform_counter,
            key=platform_counter.get
        )

        top_platform_count = platform_counter[top_platform]

    work_data = (
        db.session.query(
            JobApplication.work_type,
            func.count(JobApplication.application_id)
        )
        .filter(
            JobApplication.user_id == current_user.id,
            JobApplication.is_archived == False
        )
        .group_by(JobApplication.work_type)
        .all()
    )

    work_labels = [
        x[0] if x[0] else "Unknown"
        for x in work_data
    ]

    work_counts = [
        x[1] for x in work_data
    ]

    type_data = (
        db.session.query(
            JobApplication.application_type,
            func.count(JobApplication.application_id)
        )
        .filter(
            JobApplication.user_id == current_user.id,
            JobApplication.is_archived == False
        )
        .group_by(JobApplication.application_type)
        .all()
    )

    type_labels = [
        x[0] if x[0] else "Other"
        for x in type_data
    ]

    type_counts = [
        x[1] for x in type_data
    ]

    return render_template(
        "analytics.html",

        active_total=total,

        applied=applied,
        interviews=interviews,
        offers=offers,
        rejected=rejected,
        withdrawn=withdrawn,

        interview_rate=interview_rate,
        offer_rate=offer_rate,
        response_rate=response_rate,

        pending_total=pending_total,
        avg_days_open=avg_days_open,

        platform_labels=platform_labels,
        platform_counts=platform_counts,
        top_platform=top_platform,
        top_platform_count=top_platform_count,

        work_labels=work_labels,
        work_counts=work_counts,

        type_labels=type_labels,
        type_counts=type_counts,

        months=labels,
        counts=counts
    )


@app.route("/application/<int:id>")
@login_required
def application_details(id):
    application = JobApplication.query.get_or_404(id)
    today = date.today()
    return render_template("details.html", app=application, today=today)


@app.route("/archive/<int:application_id>")
@login_required
def archive(application_id):
    app = JobApplication.query.get_or_404(application_id)

    app.is_archived = True
    db.session.commit()

    flash("Application archived successfully", "info")

    return redirect(url_for("home"))


@app.route("/archived")
@login_required
def archived():
    status_filter = request.args.get("status")

    query = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        JobApplication.is_archived == True
    )
    total_archived = query.count()
    if status_filter:
        query = query.filter(
            JobApplication.status == status_filter
        )

    applications = query.order_by(
        JobApplication.date_applied.desc()
    ).all()

    today = date.today()

    return render_template(
        "archived.html",
        applications=applications,
        today=today,
        current_filter=status_filter,
        total_archived=total_archived
    )


@app.route("/restore/<int:application_id>")
@login_required
def restore(application_id):
    app = JobApplication.query.get_or_404(application_id)

    app.is_archived = False
    db.session.commit()

    flash("Application restored", "success")

    return redirect(url_for("archived"))


@app.route("/reopen/<int:application_id>")
@login_required
def reopen(application_id):
    application = manager.find_by_id(application_id, current_user.id)

    if application.status == "Withdrawn":
        application.status = "Applied"

        if not application.follow_up_date:
            application.follow_up_date = date.today() + timedelta(days=7)

        db.session.commit()
        flash("Application reopened.", "success")

    return redirect(url_for("home"))


@app.route("/ajax-update-status/<int:application_id>", methods=["POST"])
@login_required
def ajax_update_status(application_id):
    application = manager.find_by_id(application_id, current_user.id)

    data = request.get_json()
    new_status = data.get("status")

    application.status = new_status

    # Follow-up logic
    if new_status in ["Offer", "Rejected", "Withdrawn"]:
        application.follow_up_date = None

    elif not application.follow_up_date:
        application.follow_up_date = date.today() + timedelta(days=7)

    # Last activity
    application.last_checked = date.today()

    db.session.commit()

    # Prepare response values
    if application.follow_up_date:

        followup = application.follow_up_date.strftime("%d %b %Y")

        diff = (application.follow_up_date - date.today()).days

        if diff < 0:
            days_left = "Overdue"

        elif diff == 0:
            days_left = "Today"

        else:
            days_left = f"{diff} day{'s' if diff > 1 else ''}"

    else:
        followup = "-"
        days_left = "-"

    return jsonify({
        "success": True,
        "status": new_status,
        "followup": followup,
        "days_left": days_left
    })


@app.route("/ajax-update-priority/<int:application_id>", methods=["POST"])
@login_required
def ajax_update_priority(application_id):
    application = manager.find_by_id(application_id, current_user.id)

    data = request.get_json()
    new_priority = data.get("priority")

    application.priority = new_priority
    application.last_checked = date.today()

    db.session.commit()

    return jsonify({
        "success": True,
        "priority": new_priority
    })


@app.route("/pipeline")
@login_required
def pipeline():
    apps = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        JobApplication.is_archived == False
    ).order_by(
        JobApplication.priority.desc(),
        JobApplication.date_applied.desc()
    ).all()

    applied_apps = [a for a in apps if a.status == "Applied"]
    interview_apps = [a for a in apps if a.status == "Interview"]
    offer_apps = [a for a in apps if a.status == "Offer"]
    rejected_apps = [a for a in apps if a.status == "Rejected"]
    withdrawn_apps = [a for a in apps if a.status == "Withdrawn"]

    return render_template(
        "pipeline.html",
        applied_apps=applied_apps,
        interview_apps=interview_apps,
        offer_apps=offer_apps,
        rejected_apps=rejected_apps,
        withdrawn_apps=withdrawn_apps
    )


@app.route("/quick-status/<int:application_id>/<status>")
@login_required
def quick_status(application_id, status):
    app = manager.find_by_id(application_id, current_user.id)

    if not app:
        return redirect(url_for("pipeline"))

    app.status = status
    app.last_checked = date.today()

    if status in ["Offer", "Rejected", "Withdrawn"]:
        app.follow_up_date = None

    db.session.commit()

    return redirect(url_for("pipeline"))


@app.route("/drag-update/<int:application_id>/<status>", methods=["POST"])
@login_required
def drag_update(application_id, status):
    app = manager.find_by_id(application_id, current_user.id)

    if app:
        app.status = status
        app.last_checked = date.today()

        if status in ["Offer", "Rejected", "Withdrawn"]:
            app.follow_up_date = None

        db.session.commit()

    return "", 204


@app.route("/export-csv")
@login_required
def export_csv():
    apps = JobApplication.query.filter(
        JobApplication.user_id == current_user.id,
        JobApplication.is_archived == False
    ).order_by(JobApplication.date_applied.desc()).all()

    output = StringIO()
    writer = csv.writer(output)

    # Header Row
    writer.writerow([
        "ID",
        "Company",
        "Role",
        "Application Type",
        "Work Type",
        "Location",
        "Status",
        "Priority",
        "Applied Via",
        "Date Applied",
        "Follow Up Date",
        "Salary",
        "Contact Name",
        "Contact Email"
    ])

    # Data Rows
    for app in apps:
        writer.writerow([
            app.application_id,
            app.company_name,
            app.role,
            app.application_type,
            app.work_type,
            app.location,
            app.status,
            app.priority,
            app.applied_via,
            app.date_applied,
            app.follow_up_date,
            app.salary,
            app.contact_name,
            app.contact_email
        ])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=job_applications.csv"
        }
    )


@app.context_processor
def inject_year():
    from datetime import datetime
    return {"current_year": datetime.now().year}


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
