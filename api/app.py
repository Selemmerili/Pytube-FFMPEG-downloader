from flask import Flask, make_response, request, jsonify
from flask_cors import CORS
from myfuncs import get_video_formats, download_video, get_video_info

app = Flask(__name__)
CORS(
    app,
    methods=["POST"],
    supports_credentials=True,
    expose_headers="Authorization",
)


@app.route("/")
def hello_world():
    """
    Route handler for the root endpoint.
    Returns a simple "Hello, World!" message.
    """
    return "<p>Hello, World!</p>"


@app.route("/api/download", methods=["POST"])
def download():
    """
    Route handler for the "/api/download" endpoint.
    Downloads a video based on the provided URL, itag, and mime_type.
    """
    data = request.get_json()
    print(data)

    if "url" not in data or not data["url"] or not data["itag"]:
        response = {"message": "Url ou itag manquante dans les données"}
        return jsonify(response), 400

    url = data["url"]
    itag = data["itag"]
    mime_type = data["mime_type"]

    try:
        file_buffer = download_video(url, itag)
        file_buffer.seek(0)

        response = make_response(file_buffer.read())
        response.headers[
            "Content-Disposition"
        ] = f"attachment; filename=video.{mime_type}"

        return response

    except Exception as e:
        print("Erreur lors du téléchargement de la vidéo:", e)
        response = {"message": "Erreur lors du téléchargement de la vidéo"}
        return jsonify(response), 500


@app.route("/api/receive_url", methods=["POST"])
def receive_url():
    """
    Route handler for the "/api/receive_url" endpoint.
    Retrieves video formats and information based on the provided URL.
    """
    data = request.get_json()

    if "url" not in data or not data["url"]:
        response = {"message": "URL non fournie"}
        return jsonify(response), 400

    url = data["url"]

    formats = get_video_formats(url)
    infos = get_video_info(url)

    response = {
        "message": "URL reçue avec succès",
        "url": url,
        "video_format": formats,
        "video_infos": infos,
    }
    return jsonify(response), 200


if __name__ == "__main__":
    app.run()
