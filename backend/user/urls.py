from user import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path, include


urlpatterns = [
    path('users/', views.UserList.as_view()),
    path('users/<int:pk>/', views.UserDetail.as_view()),
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
