from django.urls import path
from . import views

app_name = "instructor_panel"

urlpatterns = [
    path("", views.login_instructor, name="login"),  # 👈 Add this for /instructors/
    path("login/", views.login_instructor, name="login"),
    path("logout/", views.logout_instructor, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("update-token/", views.update_token, name="update_token"),
]
