from django import forms


class ConfigurationForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 20, "cols": 40}), required=False
    )
