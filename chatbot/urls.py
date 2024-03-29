from django.urls import path
from . import views

urlpatterns = [
    #path('', views.home, name='home'),
    path('assessment', views.assessment, name='assessment'),
    path('', views.chatbot, name='chatbot'),
    path('chat', views.chat, name='chat'),
    path('signin', views.signin, name='signin'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('activation_failed', views.activation_failed, name='activation_failed'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('interface/', views.interface, name='interface'),
    path('one_line_interface/', views.one_line_interface, name='one_line_interface'),
    path('true_n_false_interface/', views.true_n_false_interface, name='true_n_false_interface'),
    path('assessment_history/', views.assessment_history, name='assessment_history'),
]
