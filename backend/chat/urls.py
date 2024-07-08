from chat import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path, include


urlpatterns = [
    path('chats/', views.ChatListView.as_view()),
    path('chat/<int:pk>/', views.ChatDetailView.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
