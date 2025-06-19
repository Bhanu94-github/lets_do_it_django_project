from django import forms

class VoiceResumeUploadForm(forms.Form):
    resume = forms.FileField(label="Upload your resume for voice interview")