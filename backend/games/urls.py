from games import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path, include


urlpatterns = [
    path('games/', views.GameList.as_view()),
    path('games/<int:pk>/', views.GameDetail.as_view()),
    path('tournaments/', views.TournamentCreateView.as_view(), name='tournament-create'),
    path('tournaments/register/<int:pk>/', views.TournamentRegisterView.as_view(), name='tournament-register'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
