from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('login/', views.login_student, name='login'),
    path('register/', views.register_student, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('login-success/', views.login_success_redirect, name='login_success_redirect'),
    path('start-exam/<str:module>/', views.start_ai_exam, name='start_ai_exam'),
    path('index/', views.index, name='index'),
    path('save-time/', views.save_time, name='save_time'),
    path("get-tokens/", views.get_tokens, name="get_tokens"),
    

]
