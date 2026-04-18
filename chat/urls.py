from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('conversation/<int:conv_id>/', views.conversation_view, name='conversation'),
    path('conversation/start/', views.start_conversation, name='start_conversation'),
    path('api/conversation/<int:conv_id>/send/', views.send_message, name='send_message'),
    path('api/conversation/<int:conv_id>/messages/', views.fetch_messages, name='fetch_messages'),
    path('api/conversation/<int:conv_id>/ai-assist/', views.ai_assist_stream, name='ai_assist'),
]
