from django.utils.deprecation import MiddlewareMixin

class ReferralMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ref_code = request.GET.get('ref')
        if ref_code and not request.user.is_authenticated:
            # Store in session for up to 30 days
            request.session['ref_code'] = ref_code


from django.shortcuts import redirect
from django.http import JsonResponse
from django.urls import resolve, Resolver404
from django.conf import settings


class TransportistaStoreAccessMiddleware(MiddlewareMixin):
    """
    Restricts transportista users to only their dashboard panel.
    Uses URL namespace resolution instead of fragile path prefix checks.
    Returns JSON 403 for API/AJAX requests instead of HTML redirects.
    """

    # Namespaces that transportistas ARE allowed to access
    ALLOWED_NAMESPACES = {'transportista', 'admin'}

    # URL names (without namespace) that transportistas are allowed to access
    ALLOWED_URL_NAMES = {
        'login', 'logout', 'forgotPassword', 'resetPassword',
        'resetpassword_validate', 'activate',
    }

    # Path prefixes to always skip (static assets, media, Django admin)
    SKIP_PREFIXES = ()

    def __init__(self, get_response):
        super().__init__(get_response)
        # Build skip prefixes once at startup
        self.SKIP_PREFIXES = (
            settings.STATIC_URL,
            settings.MEDIA_URL,
            '/admin/',
        )

    def process_request(self, request):
        # Only applies to authenticated transportista users
        if not request.user.is_authenticated:
            return None

        if not request.user.is_transportista:
            return None

        # Skip static/media/admin paths
        path = request.path_info
        if any(path.startswith(prefix) for prefix in self.SKIP_PREFIXES):
            return None

        # Resolve the URL to get namespace and url_name
        try:
            resolved = resolve(path)
        except Resolver404:
            return None  # Let Django handle 404s normally

        # Allow if namespace is in the whitelist
        if resolved.namespace in self.ALLOWED_NAMESPACES:
            return None

        # Allow specific URL names (login, logout, etc.)
        if resolved.url_name in self.ALLOWED_URL_NAMES:
            return None

        # Block: return JSON 403 for API/AJAX requests
        if (request.headers.get('Accept', '') == 'application/json'
                or request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
            return JsonResponse(
                {'error': 'Acceso denegado para transportistas.'},
                status=403
            )

        # Block: redirect to transportista dashboard for regular requests
        return redirect('transportista:transportista_dashboard')
