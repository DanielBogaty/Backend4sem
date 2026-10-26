from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.generic import CreateView, UpdateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer

from .forms import LoginUserForm, RegisterUserForm, ProfileUserForm, UserPasswordChangeForm
import fcalmaz.settings as settings
from forum.models import Post


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': 'Регистрация'}
    success_url = reverse_lazy('users:login')


class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {
        'title': 'Профиль пользователя',
        'default_image': settings.DEFAULT_USER_IMAGE,
    }

    def get_success_url(self):
        return reverse_lazy('users:profile')
    
    def get_object(self, queryset = None):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['posts'] = Post.objects.filter(author=self.request.user)
        return context
    

class UserPasswordChange(PasswordChangeView):
    form_class = UserPasswordChangeForm
    template_name = 'users/password_change_form.html'
    success_url = reverse_lazy('users:password_change_done')


User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': user.role
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Неверные учетные данные'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'error': 'Неверные учетные данные'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': user.role
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })