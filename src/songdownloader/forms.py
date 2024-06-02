from django import forms
from django.forms import Form


class BaseForm(Form):
    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)
        for bound_field in self:
            if hasattr(bound_field, "field") and bound_field.field.required:
                bound_field.field.widget.attrs["required"] = "required"

class DataForm(BaseForm):
    service = forms.ChoiceField(choices=(
        ("NONE", 'Choose a Service'),
        ('Spotify', 'Spotify'),
        ('Youtube', 'Youtube')), required=True
    )
    mode = forms.ChoiceField(choices=(
        ("NONE", 'Choose a Service'),
        ('Track', 'Track'),
        ('Playlist', 'Playlist')), required=True
    )
    url = forms.URLField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)

    required_css_class = 'required'

    def clean(self):
        cleaned_data = super().clean()
        if not super().is_valid():
            raise forms.ValidationError("Please enter a Valid URL.")
        service = cleaned_data.get("service")
        mode = cleaned_data.get("mode")
        url = cleaned_data.get("url")
        if service == "NONE":
            raise forms.ValidationError("Service must be selected")
        if mode == "NONE":
            raise forms.ValidationError("Mode must be selected")
        if service == "Spotify":
            if mode == "Track" and "track" not in url:
                raise forms.ValidationError(f"Invalid URL for MODE: {mode}")
            if mode == "Playlist" and "playlist" not in url:
                raise forms.ValidationError(f"Invalid URL for MODE: {mode}")
