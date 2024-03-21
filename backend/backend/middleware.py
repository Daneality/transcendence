from django.utils import timezone
from user.models import Profile
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import TokenAuthentication

class LastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token_auth = TokenAuthentication()
        try:
            token_key = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
            token = token_auth.get_model().objects.get(key=token_key)
            request.user = token.user
            Profile.objects.filter(user=request.user).update(last_activity=timezone.now())
            print("called")
        except (AttributeError, TypeError, ValueError, OverflowError, token_auth.get_model().DoesNotExist):
            raise AuthenticationFailed('Invalid token')

        response = self.get_response(request)
        return response