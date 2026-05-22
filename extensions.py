from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

# Database
db = SQLAlchemy()

# Login manager
login_manager = LoginManager()

# Mail
mail = Mail()
