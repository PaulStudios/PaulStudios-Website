# base image  
FROM python:3.12-alpine  
# setup environment variable  
ENV DockerHOME=/home/app/webapp  
# set work directory  
RUN mkdir -p $DockerHOME  

# where your code lives  
WORKDIR $DockerHOME  

# set environment variables  
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1  

# install dependencies  
RUN pip install --upgrade pip  

# copy whole project to your docker home directory. 
COPY . $DockerHOME  
# run this command to install all dependencies  
RUN pip install celery flower django django-environ python-decouple dj_database_url django-crispy-forms crispy-bootstrap5 django_extensions psycopg2-binary ChatbotAPI whitenoise redis[hiredis] gunicorn pytube lyrics_extractor youtube_search pillow django-sesame google-api-python-client pandas



