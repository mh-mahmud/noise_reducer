from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files import File
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site

from .forms import VideoUploadForm
from .models import OriginalVideo, EnhancedVideo #ExtractedAudio, EnhancedAudio, 

from .forms import VideoUploadForm
from .models import OriginalVideo

# Video length in seconds (10 minutes = 600 seconds)
MAX_VIDEO_LENGTH = 10 * 60  # 600 seconds

import os
import mimetypes
import time

from .utils import get_names, extract_audio_from_video, enhance_audio, merge_audio_with_video, delete_directory

from moviepy.editor import VideoFileClip

# Video length in seconds (10 minutes = 600 seconds)
MAX_VIDEO_LENGTH = 10 * 60  # 600 seconds


def home(request):

    return render(request, 'reducer/home.html')


@login_required
def upload(request):

    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)

        if form.is_valid():
            video_upload = form.save(commit=False)
            file_type, _ = mimetypes.guess_type(video_upload.video_file.name)

            if file_type and file_type.startswith('video'):
                # video = OriginalVideo(video_file=video_upload.video_file)
                video = OriginalVideo(video_file=video_upload.video_file, user=request.user)
                video.save()
                return redirect('show_video', video_id=video.id)
            else:
                return render(request, 'reducer/upload.html', {'form': form, 'error': 'Unsupported file type(must upload a video)'})

    else:
        form = VideoUploadForm()

    return render(request, 'reducer/upload.html', {'form':form})  



# @login_required
# def upload(request):
#     if request.method == 'POST':
#         form = VideoUploadForm(request.POST, request.FILES)

#         if form.is_valid():
#             video_upload = form.save(commit=False)
#             file_type, _ = mimetypes.guess_type(video_upload.video_file.name)

#             if file_type and file_type.startswith('video'):
#                 # Get the uploaded video file
#                 video_file = video_upload.video_file

#                 # Generate a unique temporary file name using user ID
#                 temp_file_name = f"user_{request.user.id}_temp_video.mp4"
                
#                 # Save the video temporarily to a path, without reading it fully into memory
#                 temp_file_path = default_storage.save(temp_file_name, video_file)

#                 try:
#                     # Open the video file and get its duration using VideoFileClip
#                     with VideoFileClip(temp_file_path) as video:
#                         video_duration = video.duration  # duration in seconds
                        
#                         # Check if the video duration exceeds the max allowed duration
#                         if video_duration > MAX_VIDEO_LENGTH:
#                             # Delete the temporary file if the video is too long
#                             default_storage.delete(temp_file_path)
#                             return render(request, 'reducer/upload.html', {
#                                 'form': form,
#                                 'error': 'The video is too long. Please upload a video that is not longer than 10 minutes.'
#                             })
#                 except Exception as e:
#                     # Delete the temporary file if there is an error processing the video
#                     default_storage.delete(temp_file_path)
#                     return render(request, 'reducer/upload.html', {
#                         'form': form,
#                         'error': f'Error processing video file: {str(e)}'
#                     })

#                 # Now that the video is valid, save it to the database
#                 # Make sure to reset the file name to its original name
#                 video_upload.video_file.name = video_file.name  # Ensure the filename is preserved
#                 video = OriginalVideo(video_file=video_upload.video_file, user=request.user)
#                 video.save()

#                 # Delete the temporary file after successful upload
#                 default_storage.delete(temp_file_path)

#                 return redirect('show_video', video_id=video.id)
#             else:
#                 return render(request, 'reducer/upload.html', {
#                     'form': form,
#                     'error': 'Unsupported file type (must upload a video)'
#                 })

#     else:
#         form = VideoUploadForm()

#     return render(request, 'reducer/upload.html', {'form': form})





 


@login_required
def show_video(request, video_id):

    # video = OriginalVideo.objects.get(id=video_id)
    video = get_object_or_404(OriginalVideo, id=video_id, user=request.user)
    file_type, _ = mimetypes.guess_type(video.video_file.name)

    context = {
        'video':video,
        'file_type':file_type,
    }
    return render(request, 'reducer/show_video.html', context)


@login_required
def process_video(request, video_id):

    if request.method == 'POST':
        print('request accepted')
        print('Using ffmpeg for extarction and merging with chunking')
        beginning = time.time()
        # original_video = get_object_or_404(OriginalVideo, id=video_id)

        original_video = get_object_or_404(OriginalVideo, id=video_id, user=request.user)
        # Extract audio from the video
        video_file_path = original_video.video_file.path
        print('video_file_path: ', video_file_path)
        print()
        
        audio_filename, enhanced_audio_filename, enhanced_video_filename, temp_dir_name = get_names(video_file_path)

        audio_video_temp_dir = os.path.abspath(os.path.join('media', temp_dir_name))
        os.makedirs(audio_video_temp_dir, exist_ok=True)

        temp_audio_path = os.path.join(audio_video_temp_dir, audio_filename)
        temp_enhanced_audio_path = os.path.join(audio_video_temp_dir, enhanced_audio_filename)
        temp_enhanced_video_path = os.path.join(audio_video_temp_dir, enhanced_video_filename)

        print('====================================================')
        print('Start extraction')
        start = time.time()
        extract_audio_from_video(video_file_path, temp_audio_path)
        end = time.time()
        print('Extraction done.')
        print(f"Time needed: {end - start:.2f} seconds")
        print('====================================================')

        print('====================================================')
        print('Start enhancing')
        start = time.time()
        enhance_audio(temp_audio_path, temp_enhanced_audio_path, audio_video_temp_dir)
        end = time.time()
        print('Enhancing done.')
        print(f'Time needed: {end - start:.2f} seconds')
        print('====================================================')

        print('====================================================')
        print('Start merging audio with video')
        start = time.time()
        merge_audio_with_video(video_file_path, temp_enhanced_audio_path, temp_enhanced_video_path)
        end = time.time()
        print('Audio video Merging done.')
        print(f'Time needed: {end - start:.2f} seconds')
        print('====================================================')

        # Saving to models with Django's File object
        # with open(temp_audio_path, 'rb') as audio_file:
        #     # Use just the base filename for saving in the model
        #     extracted_audio = ExtractedAudio(
        #         audio_file=File(audio_file, name=os.path.basename(temp_audio_path)), 
        #         original_video=original_video
        #     )
        #     extracted_audio.save()

        # with open(temp_enhanced_audio_path, 'rb') as enhanced_audio_file:
        #     enhanced_audio = EnhancedAudio(
        #         audio_file=File(enhanced_audio_file, name=os.path.basename(temp_enhanced_audio_path)), 
        #         extracted_audio=extracted_audio
        #     )
        #     enhanced_audio.save()
        with open(temp_enhanced_video_path, 'rb') as enhanced_video_file:
            enhanced_video = EnhancedVideo(
                video_file=File(enhanced_video_file, name=os.path.basename(temp_enhanced_video_path)),
                original_video=original_video,
                user=request.user
            )
            enhanced_video.save()

        # with open(temp_enhanced_video_path, 'rb') as enhanced_video_file:
        #     enhanced_video = EnhancedVideo(
        #         video_file=File(enhanced_video_file, name=os.path.basename(temp_enhanced_video_path)), 
        #         original_video=original_video
        #     )
        #     enhanced_video.save()

        print('objects saved')

        # Clean up the temporary directory and all its contents
        delete_directory(audio_video_temp_dir)
        print('temp dir removed')
        ending = time.time()
        print(f'Total time needed: {ending-beginning:.2f} seconds.')

        return JsonResponse({"status": "completed", "video_id": video_id})

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
    
    # return render(request, 'reducer/success.html')


# @login_required
# def download_video(request):
#     video_id = request.GET.get("video_id")
#     # enhanced_video = get_object_or_404(EnhancedVideo, original_video_id=video_id)
#     enhanced_video = get_object_or_404(EnhancedVideo, original_video_id=video_id, user=request.user)
#     context = {
#         "enhanced_video": enhanced_video,
#     }
#     return render(request, "reducer/download_video.html", context)



@login_required
def download_video(request):
    video_id = request.GET.get("video_id")
    enhanced_video = get_object_or_404(EnhancedVideo, original_video_id=video_id, user=request.user)

    if not request.user.is_active:
        return JsonResponse({"status": "error", "message": "Your email is not verified."}, status=403)

    # Generate the download page URL
    current_site = get_current_site(request)
    download_url = reverse("download_video") + f"?video_id={video_id}"
    full_download_url = f"http://{current_site.domain}{download_url}"

    # Send the email with the download link
    subject = "Your Video Download Link"
    message = f"Dear user,\n\nYour video processing is complete! You can download your video from the following link:\n\n{full_download_url}\n\nThank you for using our service!"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [request.user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

    # Render the download page
    context = {
        "enhanced_video": enhanced_video,
    }
    return render(request, "reducer/download_video.html", context)




