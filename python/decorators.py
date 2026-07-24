from functools import wraps

from flask import render_template
from flask_login import current_user


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            return render_template("error_403.html"), 403
        return view_func(*args, **kwargs)

    return wrapper
