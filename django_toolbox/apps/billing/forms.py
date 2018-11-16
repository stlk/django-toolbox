from django import forms


class DiscountTokenForm(forms.Form):
    shop = forms.CharField(max_length=250)
    price = forms.IntegerField()
    trial_days = forms.IntegerField()
