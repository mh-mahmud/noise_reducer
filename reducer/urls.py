
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload, name='upload'),
    path('video/<int:video_id>/', views.show_video, name='show_video'),
    path('process_video/<int:video_id>/', views.process_video, name="process_video"),
    path('download_video/', views.download_video, name='download_video'),
]



# urlpatterns = [
#     path('', views.home, name='home'),
#     path('upload/', views.upload, name='upload'),
#     path('audio/<int:audio_id>/', views.show_audio, name='show_audio'),
#     path('video/<int:video_id>/', views.show_video, name='show_video'),
#     path('process_audio/<int:audio_id>/', views.process_audio, name="process_audio"),
#     # path('process_video/<int:video_id>/', views.process_video, name="process_video"),
# ]