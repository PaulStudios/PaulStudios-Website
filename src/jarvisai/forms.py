from django.forms import forms, CharField, Textarea


class ChatForm(forms.Form):
    message = CharField(widget=Textarea, label='Enter your message')