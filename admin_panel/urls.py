from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path('', views.admin_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.admin_logout, name='logout'),
    path('approve-student/<str:student_id>/', views.approve_student, name='approve_student'),
    path('reject-student/<str:student_id>/', views.reject_student, name='reject_student'),
    path('update-student/<str:student_id>/', views.update_student, name='update_student'),
    path('approve-course/<str:course_id>/', views.approve_course, name='approve_course'),
    path('reject-course/<str:course_id>/', views.reject_course, name='reject_course'),
    path('download-approved/', views.download_approved_students, name='download_approved'),
]
