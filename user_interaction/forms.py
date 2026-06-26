from django import forms
from .models import UserInput

class TextInputForm(forms.Form):
    text_input = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your text here...',
            'rows': 4
        }),
        label='Text Input'
    )
    emotional_state = forms.ChoiceField(
        choices=[
            ('happy', 'Happy'),
            ('sad', 'Sad'),
            ('neutral', 'Neutral'),
            ('excited', 'Excited'),
            ('frustrated', 'Frustrated'),
            ('curious', 'Curious'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

class ImageInputForm(forms.Form):
    image_input = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='Upload Image'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Optional description...',
            'rows': 2
        }),
        required=False
    )