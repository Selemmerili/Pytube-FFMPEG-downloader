from pytube import YouTube
from io import BytesIO
import ffmpeg
import tempfile


def download_video(url, itag):
    """
    Downloads a video from YouTube given its URL and the desired video format.

    Args:
        url (str): The URL of the YouTube video.
        itag (str): The itag value representing the desired video format.

    Returns:
        BytesIO: A buffer containing the downloaded video in the specified format.
    """
    yt = YouTube(url)
    stream = yt.streams.get_by_itag(itag)
    file_buffer = BytesIO()
    stream.stream_to_buffer(file_buffer)
    video_formats = get_video_formats(url)
    video_data = [video for video in video_formats if video["itag"] == itag]
    mime_type = video_data[0]["mime_type"].split("/")[-1]

    if not video_data[0]["progressive"] and video_data[0]["type"] == "video":
        audio_formats = []
        for format in video_formats:
            if (
                format["type"] == "audio"
                and format["mime_type"] == f"audio/{mime_type}"
            ):
                audio_formats.append(format)

        best_audio = None
        for audio_format in audio_formats:
            if not best_audio or int(audio_format["abr"][:-4]) > int(
                best_audio["abr"][:-4]
            ):
                best_audio = audio_format

        if best_audio:
            best_audio_itag = best_audio["itag"]

        audio = yt.streams.get_by_itag(best_audio_itag)
        file_audio_buffer = BytesIO()
        audio.stream_to_buffer(file_audio_buffer)

        temp_file_path = tempfile.NamedTemporaryFile(suffix=f".{mime_type}").name
        temp_file_audio_path = tempfile.NamedTemporaryFile(suffix=f".{mime_type}").name
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_buffer.getbuffer())
        with open(temp_file_audio_path, "wb") as temp_file:
            temp_file.write(file_audio_buffer.getbuffer())

        output_file_path = tempfile.NamedTemporaryFile(suffix=f".{mime_type}").name

        input_video = ffmpeg.input(temp_file_path)
        input_audio = ffmpeg.input(temp_file_audio_path)
        if mime_type == "webm":
            output = ffmpeg.output(
                input_video, input_audio, output_file_path, vcodec="copy"
            )
        else:
            output = ffmpeg.output(
                input_video, input_audio, output_file_path, vcodec="copy", acodec="aac"
            )
        output.run()

        with open(output_file_path, "rb") as output_file:
            file_buffer = BytesIO(output_file.read())

        return file_buffer, mime_type
    else:
        return file_buffer, mime_type


def get_video_info(url):
    """
    Get basic information about a YouTube video.

    Args:
        url (str): The URL of the YouTube video.

    Returns:
        list: A list containing a dictionary with the title and thumbnail URL of the video.
    """
    yt = YouTube(url)
    return {"Title": yt.title, "ThumbnailUrl": yt.thumbnail_url}


def get_video_formats(url):
    """
    Get available formats of a YouTube video.

    Args:
        url (str): The URL of the YouTube video.

    Returns:
        list: A list containing the information of different video formats.
    """
    yt = YouTube(url)
    videodata = []
    for format in yt.streams:
        data = {
            "itag": format.itag,
            "mime_type": format.mime_type,
            "resolution": format.resolution,
            "fps": format.fps if "audio" not in format.type else None,
            "progressive": format.is_progressive,
            "type": format.type,
            "codecs": format.codecs,
            "abr": format.abr,
        }
        videodata.append(data)

    filtered_data = []
    for video_info in videodata:
        if video_info["type"] != "video" or video_info["progressive"]:
            filtered_data.append(video_info)
        else:
            is_duplicate = False
            for existing_info in filtered_data:
                if (
                    existing_info["resolution"] == video_info["resolution"]
                    and existing_info["mime_type"] == video_info["mime_type"]
                ):
                    is_duplicate = True
            if not is_duplicate:
                filtered_data.append(video_info)

    return filtered_data
