from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Restrict a view to the given User.Role values. Always implies login_required."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied('You do not have permission to view this page.')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
