from django.urls import path
from . import views

app_name = 'voice_assessment'

urlpatterns = [
    path('upload/', views.upload_resume, name='upload_resume'),
    path('select-skill/', views.select_skill, name='select_skill'),
    path('interview/', views.voice_to_voice, name='voice_to_voice'),
    path('result/', views.result, name='result'),
]
