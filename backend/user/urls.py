from user import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path, include


urlpatterns = [
    path('users/', views.UserList.as_view()),
    path('users/<int:pk>/', views.UserDetail.as_view()),
    path('users/<int:pk>/block', views.UserBlockView.as_view()),
    path('users/<int:pk>/unblock', views.UserUnblockView.as_view()),
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('friend-requests/<int:pk>/accept/', views.FriendRequestAcceptView.as_view(), name='friend-request-accept'),
    path('friend-requests/', views.FriendRequestListCreate.as_view(), name='friend-request-accept'),
    path('game-invites/create/', views.GameInviteCreateView.as_view(), name='game-invite-create'),

]

urlpatterns = format_suffix_patterns(urlpatterns)
