import logging as lg
import os
import shutil
import queue
import tempfile
import threading
import time
import zipfile

import requests
from celery.utils.log import get_task_logger
from django.core.files import File
from pytube import YouTube
from pytube.exceptions import PytubeError

from PaulStudios import settings
from base.tasks import increase_progress

MAX_SIMULTANEOUS_DOWNLOADS = 12
MAX_RETRIES = 3

download_queue = queue.Queue()
successful_downloads = []
failed_downloads = []
lock = threading.Lock()

# Configure logging
logging = get_task_logger(__name__)
lg.basicConfig(level=lg.INFO)

mode = settings.MODE

def zip_files(file_paths, zip_name, folder):
    logging.info(f"Zipping {zip_name}")
    try:
        zip_path = os.path.join(folder, zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    logging.info(f"Adding {file_path.split('/')[-1]} to {zip_path.split('/')[-1]}")
                    zipf.write(file_path, os.path.basename(file_path))
                    os.remove(file_path)
                else:
                    logging.error(f"File not found, skipping: {file_path.split('/')[-1]}")
        logging.info(f"ZIP file created successfully: {zip_path.split('/')[-1]}")
    except Exception as e:
        logging.error(f"USER : {zip_path.split('/')[2]} \nFailed to create ZIP file {zip_path.split('/')[-1]}: {e}")
        raise

def download_file(url, name, folder, zip_name, task_id, auth=None):
    retries = 0
    error_message = ""
    while retries < MAX_RETRIES:
        try:
            logging.info(f"Starting download: {url}")
            start_time = time.time()

            if "youtube.com" in url or "youtu.be" in url:
                download_youtube_mp3(url, name, os.path.join(folder, zip_name))
                file_path = os.path.join(folder, zip_name, name + ".mp3")
                with open(file_path, "rb") as f:
                    content = f.read()
            else:
                response = requests.get(url, timeout=10, auth=auth)
                response.raise_for_status()
                file_name = name or url.split('/')[-1]
                file_path = os.path.join(folder, file_name)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                content = response.content

            end_time = time.time()
            download_time = end_time - start_time
            file_size = len(content) / (1024 * 1024) if content else 0
            download_speed = file_size / download_time if file_size > 0 else 0
            logging.info(
                f"Download successful: {url}, Size: {file_size:.2f} MB, Time: {download_time:.2f} s, Speed: {download_speed:.2f} MB/s")
            with lock:
                successful_downloads.append(file_path)
            if not retries >= 1:
                increase_progress(task_id)
            return True
        except (requests.RequestException, PytubeError) as e:
            if not retries >= 1:
                increase_progress(task_id)
            retries += 1
            error_message = str(e)
            logging.warning(f"Retrying ({retries}/{MAX_RETRIES}) for {url}: {e}")
            time.sleep(2 ** retries)
        except Exception as e:
            logging.error(f"Unexpected error while downloading {url}: {e}")
            if not retries >= 1:
                increase_progress(task_id)
            break

    logging.error(f"Failed to download after {MAX_RETRIES} attempts: {url}")
    with lock:
        failed_downloads.append({"url": url, 'name': name, "error": error_message})
    return False

def download_youtube_mp3(url, name, folder):
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        out_file = audio_stream.download(output_path=folder, filename=name)
        base, ext = os.path.splitext(out_file)
        new_file = os.path.join(folder, name + '.mp3')
        os.rename(out_file, new_file)
        logging.info(f"Downloaded YouTube MP3: {name}")
    except PytubeError as e:
        logging.error(f"Failed to download YouTube MP3: {url}, Error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while downloading YouTube MP3 {url}: {e}")
        raise

def worker(folder, zip_name, task_id):
    while True:
        task = download_queue.get()
        if task is None:
            download_queue.task_done()
            break
        url = task.get('url')
        auth = task.get('auth')
        name = task.get('name')
        try:
            download_file(url, name, folder, zip_name, task_id, auth)
        except Exception as e:
            logging.error(f"Error in worker thread: {e}")
        finally:
            download_queue.task_done()

def downloader(tasks, zip_name, folder, task_id):
    threads = []

    logging.info(f"Starting downloader with {len(tasks)} tasks for {zip_name}")

    folder = os.path.join("songdownloader", f"media_{mode}", folder)
    if not os.path.exists(folder):
        os.makedirs(folder)

    for _ in range(MAX_SIMULTANEOUS_DOWNLOADS):
        t = threading.Thread(target=worker, args=(folder, zip_name, task_id, ))
        t.start()
        threads.append(t)

    for task in tasks:
        logging.debug(f"Queueing download: {task['url']}")
        download_queue.put(task)

    download_queue.join()

    for _ in range(MAX_SIMULTANEOUS_DOWNLOADS):
        download_queue.put(None)
    for t in threads:
        t.join()
    
    zip_name = "[PaulStudios-SongDownloader] " + zip_name + ".zip"

    if successful_downloads:
        logging.info(f"Creating ZIP file: {zip_name}")
        zip_files(successful_downloads, zip_name, folder)
        logging.info(f"Completed all tasks.")

    download_list = [os.path.basename(i) for i in successful_downloads]
    if failed_downloads:
        logging.error("Failed downloads:")
        for entry in failed_downloads:
            logging.error(f"NAME: {entry['name']} URL: {entry['url']}, Error: {entry['error']}")
        return download_list, failed_downloads, os.path.join(folder, zip_name), folder
    else:
        return download_list, [], os.path.join(folder, zip_name), folder


def process_image(obj, url):
    response = requests.get(url)
    temp_image = tempfile.NamedTemporaryFile(delete=False)
    temp_image.write(response.content)
    temp_image.flush()
    image = temp_image.name
    with open(image, "rb") as image_file:
        django_file = File(image_file)
        obj.image.save(f"{str(obj.id)}.jpg", django_file, save=True)
    os.remove(temp_image.name)


def make_yt_link(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"
