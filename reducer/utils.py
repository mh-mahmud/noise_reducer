import subprocess
import os
import uuid
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress warnings from torchaudio
warnings.filterwarnings("ignore", category=UserWarning, message=".*AudioMetaData.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*sinc_interpolation.*")

import torch

print('Importing DeepFilterNet...')
from df.enhance import enhance, init_df, load_audio, save_audio
print('DeepFilterNet imported.')

print('Importing done')

def delete_directory(directory_path):
    import shutil
    # Delete the directory and its contents
    try:
        shutil.rmtree(directory_path)
        print(f"Directory \"{directory_path}\" and its contents deleted successfully")
    except OSError as e:
        print(f"Error: {e}")


def get_names(video_file_path):
    directory, video_filename = os.path.split(video_file_path)

    audio_file_extension = '.wav'
    audio_filename = os.path.splitext(video_filename)[0] + audio_file_extension

    enhanced_audio_filename = 'enhanced_' + audio_filename
    enhanced_video_filename = 'enhanced_' + video_filename

    temp_dir_name = 'temp_dir_for_' + os.path.splitext(video_filename)[0]
    return audio_filename, enhanced_audio_filename, enhanced_video_filename, temp_dir_name


# Extract audio from video
def extract_audio_from_video(input_video_path, output_audio_path):
    '''Extract audio using ffmpeg and save it as a separate file'''
    print('Separating Audio')
    # ffmpeg command to extract audio
    command = ['ffmpeg', '-i', input_video_path, '-vn', output_audio_path]
    
    try:
        # Run the ffmpeg command
        subprocess.run(command, check=True)
        print(f"Audio extracted and saved as {output_audio_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during audio extraction: {e}")


# Enhance extracted audio

# split audio into chunks using ffmpeg
def split_audio(input_audio_path, temp_dir, chunk_duration=30):
    """Splits the audio into chunks of specified duration and saves them to a temporary directory using ffmpeg."""
    # Create the temporary directory if it does not exist
    os.makedirs(temp_dir, exist_ok=True)
    
    command = [
        'ffmpeg',
        '-i', input_audio_path,
        '-f', 'segment',
        '-segment_time', str(chunk_duration),
        '-c', 'copy',
        os.path.join(temp_dir, 'chunk_%03d.wav')  # Naming format for chunks
    ]
    
    subprocess.run(command, check=True)
    
    # List all generated chunk files
    chunk_paths = sorted(os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.wav'))
    return chunk_paths


def enhance_audio_chunk(input_audio_path, enhanced_audio_path, model, df_state):
    """Loads and enhances the audio."""
    audio, _ = load_audio(input_audio_path, sr=df_state.sr())
    print(f"Audio loaded from {input_audio_path}")
    
    with torch.no_grad():
        enhanced = enhance(model, df_state, audio)
    
    save_audio(enhanced_audio_path, enhanced, df_state.sr())
    print(f"Enhanced audio saved to {enhanced_audio_path}")


def process_chunk(chunk_path, temp_dir, model, df_state):
    """Processes a single chunk of audio."""
    processed_chunk_name = f"processed_{os.path.basename(chunk_path)}"
    processed_chunk_path = os.path.join(temp_dir, processed_chunk_name)
    enhance_audio_chunk(chunk_path, processed_chunk_path, model, df_state)

    return processed_chunk_path

def get_processed_chunks(chunk_paths, temp_dir, model, df_state, max_workers=2):
    """Processes the audio chunks in parallel using threading."""
    processed_chunk_paths = []

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_chunk, chunk_path, temp_dir, model, df_state) for chunk_path in chunk_paths]

        for future in as_completed(futures):
            processed_chunk_path = future.result()
            processed_chunk_paths.append(processed_chunk_path)
            print(f"Processed chunk saved: {processed_chunk_path}")

    return processed_chunk_paths


def merge_audio_chunks(processed_chunk_paths, output_audio_path):
    """Merges the processed audio chunks back together into a single audio file using ffmpeg."""
    
    # Sort the processed chunk paths to ensure correct order
    processed_chunk_paths = sorted(processed_chunk_paths)
    
    # Create a temporary text file to list all chunks (required by ffmpeg)
    list_file = os.path.join(os.path.dirname(output_audio_path), 'chunks_list.txt')
    with open(list_file, 'w') as f:
        for chunk in processed_chunk_paths:
            f.write(f"file '{chunk}'\n")
    
    # Use ffmpeg to concatenate the chunks
    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file,
        '-c', 'copy',
        output_audio_path
    ]
    
    subprocess.run(command, check=True)
    print(f"Processed audio chunks merged into {output_audio_path}")

    # Clean up the temporary list file
    os.remove(list_file)


def enhance_audio(input_audio_path, enhanced_audio_path, audio_video_temp_dir):
    # Create a unique temporary directory for each audio file
    temp_dir_name = f"temp_chunks_{uuid.uuid4().hex}"
    temp_dir = os.path.join(audio_video_temp_dir, temp_dir_name)
    os.makedirs(temp_dir, exist_ok=True)
    print(f"{temp_dir} created")

    chunk_paths = split_audio(input_audio_path, temp_dir)

    # Initialize the model and df_state
    print('Initializing model')
    start = time.time() 
    model, df_state, _ = init_df()
    end = time.time()
    time_required = end - start
    print(f"Model and df_state initialized. Took{time_required:.2f} seconds")
    print('=================================================')
    

    # Process chunks in parallel, passing the model and df_state
    print('start audio processing')
    start = time.time() 
    processed_chunk_paths = get_processed_chunks(chunk_paths, temp_dir, model, df_state, max_workers=2)
    end = time.time()
    time_required = end - start
    print(f'Audio chunks enhancing done. Took {time_required:.2f}')
    print('=================================================')

    # Merge enhanced chunks
    print('start merging audio chunks')
    start = time.time() 
    merge_audio_chunks(processed_chunk_paths, enhanced_audio_path)
    end = time.time()
    time_required = end - start
    print(f'Audio chunks merging done. Took {time_required:.2f}')
    print('=================================================')

    delete_directory(temp_dir)

    print('Done')


def merge_audio_with_video(original_video_path, enhanced_audio_path, enhanced_video_path):
    # ffmpeg command to merge MP4 video with WAV audio
    command = [
        'ffmpeg', '-y', '-i', original_video_path, '-i', enhanced_audio_path,
        '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', '-shortest', enhanced_video_path
    ]
    
    try:
        # Run the ffmpeg command
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"Successfully merged audio and video. Output saved at {enhanced_video_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during merging: {e}")
        print(f"ffmpeg output:\n{e.stderr}")

 

