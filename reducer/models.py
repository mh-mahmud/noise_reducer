from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class OriginalVideo(models.Model):
    video_file = models.FileField(upload_to='videos/', max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='original_videos')
    # FK user

    def __str__(self):
        return self.video_file.name
    

class EnhancedVideo(models.Model):
    video_file = models.FileField(upload_to='enhanced_videos/', max_length=255)
    original_video = models.ForeignKey(OriginalVideo, on_delete=models.CASCADE, related_name='enhanced_videos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enhanced_videos')
    # FK user

    def __str__(self):
        return self.video_file.name



#class ExtractedAudio(models.Model):
#     audio_file = models.FileField(upload_to='extracted_audios/', max_length=255)
#     original_video = models.ForeignKey(OriginalVideo, on_delete=models.SET_NULL, null=True)
#     # FK user

#     def __str__(self):
#         return self.audio_file.name
    

# class EnhancedAudio(models.Model):
#     audio_file = models.FileField(upload_to='enhanced_audios/', max_length=255)
#     extracted_audio = models.ForeignKey(ExtractedAudio, on_delete=models.CASCADE)
#     # FK user

#     def __str__(self):
#         return self.audio_file.name