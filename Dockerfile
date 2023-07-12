FROM python:3-alpine

# Install FFmpeg
RUN apk add --no-cache ffmpeg

# Create app directory
WORKDIR /app

# Install app dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Bundle app source
COPY . .

# Modify cipher.py
USER root
RUN sed -i '287s/;//' /usr/local/lib/python3.11/site-packages/pytube/cipher.py
RUN cat /usr/local/lib/python3.11/site-packages/pytube/cipher.py

EXPOSE 5000
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]