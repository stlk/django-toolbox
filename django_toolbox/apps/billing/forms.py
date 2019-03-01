from django import forms


class RecurringApplicationChargeForm(forms.Form):
    shop = forms.CharField(max_length=250)
    name = forms.CharField(max_length=250)
    price = forms.DecimalField()
    trial_days = forms.IntegerField()
