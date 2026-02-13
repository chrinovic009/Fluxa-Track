from flask import request
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.utils.authentication.models import SystemErrorLog
import traceback


def register_error_handlers(app):

    #@app.errorhandler(Exception)
    def handle_exception(e):

        company_id = None

        if hasattr(request, "view_args") and request.view_args:
            company_id = request.view_args.get("company_id")

        error_class = type(e).__name__
        message = str(e)
        trace = traceback.format_exc()

        if isinstance(e, SQLAlchemyError):
            category = "database"
        elif "Timeout" in message:
            category = "timeout"
        elif "Connection" in message:
            category = "external_api"
        else:
            category = "application"

        try:
            error_log = SystemErrorLog(
                company_id=company_id,
                error_type=category,
                message=f"{error_class}: {message}\n{trace}"
            )

            db.session.add(error_log)
            db.session.commit()

        except Exception:
            pass

        return "Une erreur interne est survenue.", 500


    @app.after_request
    def log_http_errors(response):

        if response.status_code >= 400:
            try:
                error_log = SystemErrorLog(
                    error_type="application",
                    message=f"HTTP {response.status_code} | PATH={request.full_path}"
                )
                db.session.add(error_log)
                db.session.commit()
            except Exception:
                pass

        return response
