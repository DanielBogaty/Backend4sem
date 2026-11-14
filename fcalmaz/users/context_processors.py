from core.utils import menu
from rest_framework_simplejwt.tokens import RefreshToken


def get_menu_context(request):
    return {'menu': menu}

def jwt_token_context(request):
    if getattr(request, 'user', None) and request.user.is_authenticated:
        refresh = RefreshToken.for_user(request.user)
        return {'jwt_access_token': str(refresh.access_token)}
    return {'jwt_access_token': ''}