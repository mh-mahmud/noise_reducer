from django import forms
from .models import OriginalVideo

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = OriginalVideo
        fields = ['video_file']