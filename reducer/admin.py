from django.contrib import admin

from .models import OriginalVideo, EnhancedVideo #ExtractedAudio, EnhancedAudio, 

admin.site.register(OriginalVideo)
# admin.site.register(ExtractedAudio)
# admin.site.register(EnhancedAudio)
admin.site.register(EnhancedVideo)
