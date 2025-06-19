from django.urls import path
from . import views

app_name = 'resumeupload'

urlpatterns = [
    path('resume/analyze/', views.upload_resume, name='upload_resume'),
    path('resume/download/', views.download_feedback, name='download_feedback'),  # ✅ for PDF
]
