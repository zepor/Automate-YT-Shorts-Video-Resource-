"""
This module provides functionality for automating the creation of YouTube
Shorts videos.
It includes utilities for fetching Twitch videos, downloading and processing
video files,
generating subtitles, combining video clips, and adding text-to-speech audio.
"""

import os
from typing import List

import assemblyai as aai  # type: ignore

# Ensure the requests library is installed and properly imported
import requests
import srt_equalizer  # type: ignore
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import TextClip
# SubtitlesClip is not available in latest MoviePy; subtitle overlay will need a custom implementation or alternative library.
from termcolor import colored
import yt_dlp  # type: ignore

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
TWITCH_CHANNEL_ID = "zepor1"


def fetch_twitch_videos(
    client_id: str, access_token: str, channel_id: str
) -> List[str]:
    """
    Fetches all video URLs from a Twitch channel.

    Args:
        client_id (str): Twitch client ID.
        access_token (str): Twitch access token.
        channel_id (str): Twitch channel ID.

    Returns:
        List[str]: List of video URLs.
    """
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}",
    }
    url = (
        f"https://api.twitch.tv/helix/videos?"
        f"user_id={channel_id}&sort=time&type=all"
    )
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print(colored(f"Failed to fetch videos: {response.status_code}", "red"))
        return []  # Return an empty list in case of failure

    data = response.json()
    return [video["url"] for video in data.get("data", [])]


def fetch_twitch_video_titles(
    client_id: str, access_token: str, channel_id: str
) -> List[str]:
    """
    Fetches all video titles from a Twitch channel.

    Args:
        client_id (str): Twitch client ID.
        access_token (str): Twitch access token.
        channel_id (str): Twitch channel ID.

    Returns:
        List[str]: List of video titles.
    """
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}",
    }
    url = (
        f"https://api.twitch.tv/helix/videos?"
        f"user_id={channel_id}&sort=time&type=all"
    )
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print(colored(f"Failed to fetch video titles: {response.status_code}", "red"))
        return []  # Ensure a list is returned even in error cases

    data = response.json()
    return [video["title"] for video in data.get("data", [])]


def save_video(urls: List[str]) -> List[str]:
    """
    Downloads videos from the provided URLs and saves them to the local
    filesystem.

    Args:
        urls (List[str]): A list of video URLs to download.

    Returns:
        List[str]: A list of file paths where the videos are saved.
    """
    saved_paths = []
    for idx, url in enumerate(urls, 1):
        # Fetch video info using yt_dlp to get title and upload date
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                # Use upload_date and title for filename
                if info:
                    upload_date = info.get("upload_date", "unknown_date")
                    title = info.get("title", f"video_{idx}")
                else:
                    upload_date = "unknown_date"
                    title = f"video_{idx}"
                # Clean title for filesystem
                safe_title = "".join(
                    c for c in title if c.isalnum() or c in (" ", "_", "-")
                ).rstrip()
                filename = f"{upload_date}_{safe_title}.mp4"
            except yt_dlp.utils.DownloadError as e:
                print(colored(f"Failed to get info for {url}: {e}", "red"))
                filename = f"video_{idx}.mp4"

        output_path = f"./temp/{filename}"
        ydl_opts = {
            "outtmpl": output_path,
            "format": "best",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(colored(f"Downloading video: {url}", "blue"))
            ydl.download([url])
        print(colored(f"Saved video to: {output_path}", "green"))
        saved_paths.append(output_path)
    return saved_paths


# Define a function to speak text using edge-tts
def text_to_speech(text: str, output_path_location: str = "output.mp3") -> str:
    """
    Converts the given text to speech and saves it as an audio file.

    Args:
        text (str): The text to be converted into speech.
        output_path_location (str, optional): The file path where the generated
            audio file will be saved. Defaults to "output.mp3".

    Returns:
        str: The file path where the audio file is saved.
    """
    # Choose the voice for the speech (professional Canadian accent)
    voice = "en-CA-LiamNeural"

    # Build the edge-tts command string, including voice, text,
    # and output media
    command = (
        f'edge-tts --voice "{voice}" '
        f'--text "{text}" '
        f'--write-media "{output_path_location}"'
    )

    # Execute the edge-tts command using the system shell
    os.system(command)

    return output_path_location


def generate_subtitles(
    audio_path: str, assembly_ai_api_key: str, directory: str = "./subtitles"
) -> str:
    """
    Generates subtitles from a given audio file and
    returns the path to the subtitles.

    Args:
        audio_path (str): The path to the audio file to generate subtitles
            from.

    Returns:
        str: The path to the generated subtitles.
    """

    def equalize_subtitles(srt_path: str, max_chars: int = 10) -> None:
        # Equalize subtitles
        srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)

    print(assembly_ai_api_key)

    aai.settings.api_key = assembly_ai_api_key

    transcriber = aai.Transcriber()

    transcript = transcriber.transcribe(audio_path)

    os.makedirs(directory, exist_ok=True)
    # Save subtitles
    subtitles_path = f"{directory}/audio.srt"

    subtitles = transcript.export_subtitles_srt()

    with open(subtitles_path, "w", encoding="utf-8") as subtitle_file:
        subtitle_file.write(subtitles)

    # Equalize subtitles
    equalize_subtitles(subtitles_path)

    print(colored("[+] Subtitles generated.", "green"))

    return subtitles_path


def concatenate_clips_sequentially(clips: list[VideoFileClip]) -> CompositeVideoClip:
    """
    Concatenate a list of VideoFileClip objects sequentially into a single CompositeVideoClip.
    Args:
        clips (list[VideoFileClip]): List of video clips to concatenate.
    Returns:
        CompositeVideoClip: The concatenated video clip.
    """
    t = 0
    new_clips = []
    for clip in clips:
        clip = clip.set_start(t)
        t += clip.duration
        new_clips.append(clip)
    return CompositeVideoClip(new_clips)


def combine_videos(video_paths: List[str], max_duration: int) -> str:
    """
    Combines a list of videos into one video and
    returns the path to the combined video.

    Args:
        video_paths (list): A list of paths to the videos to combine.
        max_duration (int): The maximum duration of the combined video.

    Returns:
        str: The path to the combined video.
    """
    combined_video_path = "./temp/combined_video.mp4"

    print(colored("[+] Combining videos...", "blue"))
    print(
        colored(
            f"[+] Each video will be "
            f"{max_duration / len(video_paths)} seconds long.",
            "blue",
        )
    )

    clips = []
    for video_path in video_paths:
        clip = VideoFileClip(video_path)
        clip = clip.without_audio()
        clip = clip.subclip(0, max_duration / len(video_path))
        clip = clip.set_fps(30)

        # Not all videos are same size,
        # so we need to resize them
        clip = mp.crop(
            clip, width=1080, height=1920, x_center=clip.w / 2, y_center=clip.h / 2
        )
        clip = clip.resize((1080, 1920))

        clips.append(clip)

    final_clip = concatenate_clips_sequentially(clips)
    final_clip = final_clip.set_fps(30)
    final_clip.write_videofile(combined_video_path, threads=3)

    return combined_video_path


def generate_video(
    combined_video_path: str,
    tts_path: str,
    subtitles_path: str,
    output_file_name: str = "main_output.mp4",
) -> str:
    """
    This function creates the final video, with subtitles and audio.

    Args:
        combined_video_path (str): The path to the combined video.
        tts_path (str): The path to the text-to-speech audio.
        subtitles_path (str): The path to the subtitles.

    Returns:
        str: The path to the final video.
    """

    # Make a generator that returns a TextClip when called with consecutive
    def generator(txt):
        return TextClip(
            txt,
            font=r"MoneyPrinter\fonts\bold_font.ttf",
            fontsize=100,
            color="#FFFF00",
            stroke_color="black",
            stroke_width=5,
        )

    # Burn the subtitles into the video
    subtitles = mp.SubtitlesClip(subtitles_path, generator)
    result = CompositeVideoClip(
        [
            VideoFileClip(combined_video_path),
            subtitles.set_position(("center", "center")),
        ]
    )

    # Add the audio
    audio = AudioFileClip(tts_path)
    result = result.set_audio(audio)

    result.write_videofile("./temp/output.mp4", threads=3)

    return output_file_name


def list_files_in_directory(directory):
    """
    List all files in the specified directory.
    Args:
        directory (str): The path to the directory to list files from.
    Returns:
        list: A list of filenames in the specified directory. If the directory
        is not found, an empty list is returned.
    Raises:
        FileNotFoundError: If the specified directory does not exist.
    """
    try:
        # Get a list of all files in the specified directory
        files = [
            file_name
            for file_name in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, file_name))
        ]
        return files

    except FileNotFoundError:
        print("Directory not found: " + str(directory))
        return []


if __name__ == "__main__":

    # path = text_to_speech(
    # '''Discover diverse online income avenues with this
    # guide! Freelancing offers a platform for writers, designers, programmers,
    # and marketers to showcase skills and secure clients. Dive into lucrative
    # affiliate marketing by promoting products for commissions. Consider
    # starting an e-commerce business to tap into the global market. Content
    # creation, whether through blogging, vlogging, or online courses,
    # monetizes expertise. Emphasizing diversification, explore multiple
    # income streams for financial stability. Making money online demands
    # dedication, perseverance, and learning. It's not a quick fix, but with
    # the right mindset, you can build a sustainable online income. For more
    # insights or questions, leave a comment below. Happy money-making''')
    # print(path)
    if TWITCH_CLIENT_ID and TWITCH_ACCESS_TOKEN:
        video_urls = fetch_twitch_videos(
            TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN, TWITCH_CHANNEL_ID
        )
    else:
        print(colored("Error: Missing Twitch credentials.", "red"))
        video_urls = []
    if video_urls:
        save_video(video_urls)
    # links = [
    #     (
    #         'https://player.vimeo.com/external/493894149.sd.mp4'
    #         '?s=c882caa9e51f67e259185992e97340c902c65624'
    #         '&profile_id=164&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/504027534.hd.mp4'
    #         '?s=3dcefc44fde76f92996332f9aff164453815ee99'
    #         '&profile_id=174&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/507877197.hd.mp4'
    #         '?s=e6047c0fde051a074dc4cf1a9c99ec1a6c9080e1'
    #         '&profile_id=170&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/533386598.hd.mp4'
    #         '?s=f37c8671c211b59b0aa6b24108ce752b18081aa8'
    #         '&profile_id=174&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/539033394.sd.mp4'
    #         '?s=8813ecbaf896b6ea024b4fff6eab1246e81758ac'
    #         '&profile_id=164&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/493894149.sd.mp4'
    #         '?s=c882caa9e51f67e259185992e97340c902c65624'
    #         '&profile_id=164&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/441945918.hd.mp4'
    #         '?s=39454433911b7835677a3925b93b0593ee3bf3ad'
    #         '&profile_id=175&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/507878934.hd.mp4'
    #         '?s=349c086fb23a938b6ca97bad042f044e04e0487d'
    #         '&profile_id=172&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/533386598.hd.mp4'
    #         '?s=f37c8671c211b59b0aa6b24108ce752b18081aa8'
    #         '&profile_id=174&oauth2_token_id=57447761'
    #     ),
    #     (
    #         'https://player.vimeo.com/external/436375789.hd.mp4'
    #         '?s=ea9af22125a91895ef74ae54ba2ad033a686ccf1'
    #         '&profile_id=170&oauth2_token_id=57447761'
    #     )
    # ]

    # temp_audio = AudioFileClip("output.mp3")
    # print(temp_audio.duration)

    # video_paths = save_video(links)
    # print(video_paths)

    # speech_file_path = text_to_speech("TOPIC")
    # subtitle_path = generate_subtitles(
    #     r"output.mp3"
    #     'fd937dda8dbf4258b7ec098b7c419bfe'
    # )

    # combined_video_path = combine_videos(video_paths, temp_audio.duration)
    # combined_video_path = f"./temp/combined_video.mp4"
    # generate_video(combined_video_path, "output.mp3", r"subtitles\audio.srt")
