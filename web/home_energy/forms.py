from django import forms
from django.core.exceptions import ValidationError

class AddPriceForm(forms.Form):
    starttime = forms.DateField(required=True,   widget=forms.TextInput(attrs={'type': 'date'}))
    down_high = forms.FloatField(required=False, widget=forms.TextInput(attrs={'step': ''}))
    down_low  = forms.FloatField(required=False, widget=forms.TextInput(attrs={'step': ''}))
    up_high   = forms.FloatField(required=False, widget=forms.TextInput(attrs={'step': ''}))
    up_low    = forms.FloatField(required=False, widget=forms.TextInput(attrs={'step': ''}))
    peak_down = forms.FloatField(required=False, widget=forms.TextInput(attrs={'step': ''}))
    gas       = forms.FloatField(required=False, widget=forms.TextInput(attrs={'step': ''}))

    def clean(self):
        cleaned_data = super().clean()
        down_high = cleaned_data.get("down_high")
        down_low  = cleaned_data.get("down_low")
        up_high   = cleaned_data.get("up_high")
        up_low    = cleaned_data.get("up_low")
        peak_down = cleaned_data.get("peak_down")
        gas       = cleaned_data.get("gas")

        if (not down_high and
            not down_low and
            not up_high and
            not up_low and
            not peak_down and
            not gas):
            # All price fields are empty
            raise ValidationError("At least one price should be filled in.")

class ModifyPriceForm(AddPriceForm):
    id = forms.CharField(required=True, widget=forms.HiddenInput())

class RemovePriceForm(forms.Form):
    id = forms.CharField(required=True, widget=forms.HiddenInput())

class GetTotalCostsForm(forms.Form):
    starttime = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date'}))
    stoptime  = forms.DateField(required=True, widget=forms.TextInput(attrs={'type': 'date'}))

    def clean(self):
        cleaned_data = super().clean()
        starttime = cleaned_data.get("starttime")
        stoptime  = cleaned_data.get("stoptime")

        if (stoptime < starttime):
            raise ValidationError("Starttime must be before stoptime.")
