from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def superadmin_required(view_func):
    """Only allow superusers (is_superuser=True) or role='admin'."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
            messages.error(request, "Access Denied. Super Admin privileges required.")
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return wrapper
