from flask import Flask, make_response, request, jsonify
from flask_cors import CORS
from myfuncs import get_video_formats, download_video, get_video_info

app = Flask(__name__)
CORS(
    app,
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
    Downloads a video based on the provided URL and itag.
    """
    data = request.get_json()
    print(data)

    if "url" not in data or not data["url"] or not data["itag"]:
        response = {"message": "Url or itag missing in data"}
        return jsonify(response), 400

    url = data["url"]
    itag = data["itag"]

    try:
        file_buffer, mime_type = download_video(url, itag)
        file_buffer.seek(0)

        video_info = get_video_info(url)
        title = video_info["Title"].replace(" ", "-")

        response = make_response(file_buffer.read())
        response.headers[
            "Content-Disposition"
        ] = f"attachment; filename={title}.{mime_type}"

        return response

    except Exception as e:
        print("Error downloading video:", e)
        response = {"message": "Error downloading video:"}
        return jsonify(response), 500


@app.route("/api/receive_url", methods=["POST"])
def receive_url():
    """
    Route handler for the "/api/receive_url" endpoint.
    Retrieves video formats and information based on the provided URL.
    """
    data = request.get_json()

    if "url" not in data or not data["url"]:
        response = {"message": "URL not provided"}
        return jsonify(response), 400

    url = data["url"]

    try:
        formats = get_video_formats(url)
        infos = get_video_info(url)

        response = {
            "message": "URL successfully received",
            "url": url,
            "video_format": formats,
            "video_infos": infos,
        }
        return jsonify(response), 200

    except Exception as e:
        print("Error retrieving video formats and info:", e)
        response = {"message": f"Error retrieving video formats and info: {e}"}
        return jsonify(response), 500


if __name__ == "__main__":
    app.run()
