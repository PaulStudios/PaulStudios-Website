import redis
from celery.utils.log import get_task_logger

from django.contrib.auth import get_user_model
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode

from PaulStudios import settings
from PaulStudios.celery import app
from base.tasks import delete_key
from .utilities import code_generator

logger = get_task_logger(__name__)
USER = get_user_model()
redis_db = redis.from_url(settings.REDIS_URL, decode_responses=True)


@app.task(bind=True)
def send_activation_email(self, request_scheme, host, user_id):
    user = USER.objects.get(pk=user_id)
    if not user.activated:
        if user.activation_key:
            delete_key(user.activation_key)
        user.activation_key = code_generator()  # generate key
        user.save()
        code = urlsafe_base64_encode(user.activation_key.encode('utf-8'))
        redis_db.set(user.activation_key, 1)
        delete_key.apply_async((user.activation_key,), countdown=2*60*60)
        path_ = reverse('profiles:activate', kwargs={"code": code})
        full_path = request_scheme + "://" + host + path_
        subject = '[PaulStudios] Activate Account'
        from_email = settings.EMAIL_HOST_USER
        html_content = render_to_string('profiles/activation_email.html', {'user': user, 'activation_link': full_path})
        text_content = strip_tags(html_content)
        to_email = user.email
        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        email.send()
        logger.info("Sent activation email to {} for user {}".format(to_email, user.username))
        return True
    return False
