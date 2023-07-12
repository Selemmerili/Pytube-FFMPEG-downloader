from pytube import YouTube
from io import BytesIO
import ffmpeg
import tempfile


def download_video(url, itag):
    """
    Télécharge une vidéo à partir de l'URL fournie et de l'itag spécifié.

    Args:
        url (str): L'URL de la vidéo à télécharger.
        itag (str): L'itag spécifiant le format de la vidéo à télécharger.

    Returns:
        BytesIO: Le buffer contenant le contenu de la vidéo téléchargée.
    """
    yt = YouTube(url)
    stream = yt.streams.get_by_itag(itag)
    file_buffer = BytesIO()
    stream.stream_to_buffer(file_buffer)
    video_formats = get_video_formats(url)
    video_data = next((video for video in video_formats if video["itag"] == itag), None)
    if not video_data:
        return file_buffer

    mime_type = video_data["mime_type"].split("/")[-1]

    if video_data["progressive"] or video_data["type"] != "video":
        return file_buffer

    audio_formats = get_audio_formats(video_formats, mime_type)
    best_audio_itag = get_best_audio_itag(audio_formats)

    if best_audio_itag:
        audio = yt.streams.get_by_itag(best_audio_itag["itag"])
        file_audio_buffer = BytesIO()
        audio.stream_to_buffer(file_audio_buffer)

        temp_file_path = save_buffer_to_temp_file(file_buffer, mime_type)
        temp_file_audio_path = save_buffer_to_temp_file(file_audio_buffer, mime_type)

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

    return file_buffer


def get_video_info(url):
    """
    Obtient des informations de base sur une vidéo YouTube.

    Args:
        url (str): L'URL de la vidéo YouTube.

    Returns:
        list: Une liste contenant un dictionnaire avec le titre et l'URL de la miniature de la vidéo.
    """
    yt = YouTube(url)
    return [{"Title": yt.title, "ThumbnailUrl": yt.thumbnail_url}]


def get_video_formats(url):
    """
    Obtient les formats disponibles d'une vidéo YouTube.

    Args:
        url (str): L'URL de la vidéo YouTube.

    Returns:
        list: Une liste contenant les informations des différents formats vidéo.
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
            is_duplicate = any(
                existing_info["resolution"] == video_info["resolution"]
                and existing_info["mime_type"] == video_info["mime_type"]
                for existing_info in filtered_data
            )
            if not is_duplicate:
                filtered_data.append(video_info)

    return filtered_data


def get_audio_formats(video_formats, mime_type):
    """
    Obtient les formats audio correspondant au type MIME spécifié.

    Args:
        video_formats (list): Les formats vidéo disponibles.
        mime_type (str): Le type MIME pour lequel les formats audio sont recherchés.

    Returns:
        list: Une liste contenant les informations des différents formats audio.
    """
    return [
        format
        for format in video_formats
        if format["type"] == "audio" and format["mime_type"] == f"audio/{mime_type}"
    ]


def get_best_audio_itag(audio_formats):
    """
    Obtient l'itag du meilleur format audio en fonction de l'abr (bitrate audio moyen).

    Args:
        audio_formats (list): Les formats audio disponibles.

    Returns:
        str: L'itag du meilleur format audio, ou une chaîne vide si aucun format audio n'est trouvé.
    """
    return max(audio_formats, key=lambda x: int(x["abr"][:-4]), default="")["itag"]


def save_buffer_to_temp_file(buffer, file_extension):
    """
    Enregistre le contenu d'un buffer dans un fichier temporaire.

    Args:
        buffer (BytesIO): Le buffer contenant les données à enregistrer.
        file_extension (str): L'extension du fichier temporaire.

    Returns:
        str: Le chemin du fichier temporaire.
    """
    temp_file_path = tempfile.NamedTemporaryFile(suffix=f".{file_extension}").name
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(buffer.getbuffer())
    return temp_file_path
