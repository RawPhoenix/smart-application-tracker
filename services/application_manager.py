from flask_login import current_user

from extensions import db
from models.job_application import JobApplication


class ApplicationManager:

    # =========================================================
    # CREATE APPLICATION
    # =========================================================
    def add_application(
            self,
            company_name,
            role,
            location,
            applied_via,
            status,
            date_applied,
            user_id,

            application_type="Job",
            work_type="Unknown",
            priority="Medium",

            follow_up_date=None,
            application_link="",

            office_address="",
            maps_link="",

            notes="",
            salary="",
            contact_name="",
            contact_email="",
            contact_phone="",
            last_checked=None
    ):

        # Auto-fix URLs
        if application_link and not application_link.startswith(
                ("http://", "https://")
        ):
            application_link = (
                    "https://" + application_link
            )

        if maps_link and not maps_link.startswith(
                ("http://", "https://")
        ):
            maps_link = (
                    "https://" + maps_link
            )

        new_application = JobApplication(
            company_name=company_name,
            role=role,
            location=location,
            applied_via=applied_via,
            status=status,
            date_applied=date_applied,
            user_id=user_id,

            application_type=application_type,
            work_type=work_type,
            priority=priority,

            follow_up_date=follow_up_date,
            application_link=application_link,

            office_address=office_address,
            maps_link=maps_link,

            notes=notes,
            salary=salary,

            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,

            last_checked=last_checked
        )

        db.session.add(new_application)
        db.session.commit()

        return new_application

    # =========================================================
    # UPDATE STATUS
    # =========================================================
    def update_status(
            self,
            application_id,
            new_status
    ):

        if new_status not in JobApplication.VALID_STATUSES:
            raise ValueError(
                "Invalid application status"
            )

        application = JobApplication.query.get(
            application_id
        )

        if not application:
            raise ValueError(
                "Application not found"
            )

        application.status = new_status

        db.session.commit()

        return application

    # =========================================================
    # WITHDRAW APPLICATION
    # =========================================================
    def withdraw_application(
            self,
            application_id
    ):
        return self.update_status(
            application_id,
            "Withdrawn"
        )

    # =========================================================
    # GET ALL APPLICATIONS
    # =========================================================
    def get_all_applications(self):

        return JobApplication.query.filter_by(
            user_id=current_user.id
        ).all()

    # =========================================================
    # FIND BY ID
    # =========================================================
    def find_by_id(
            self,
            application_id,
            user_id
    ):

        application = JobApplication.query.filter_by(
            application_id=application_id,
            user_id=user_id
        ).first()

        if not application:
            raise ValueError(
                "Application not found"
            )

        return application

    # =========================================================
    # FILTER BY STATUS
    # =========================================================
    def filter_by_status(self, status):

        if status not in JobApplication.VALID_STATUSES:
            raise ValueError(
                "Invalid application status"
            )

        return JobApplication.query.filter_by(
            user_id=current_user.id,
            status=status
        ).all()
