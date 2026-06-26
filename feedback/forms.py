from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('feedback_type', 'rating', 'comment', 'emotional_response')
        widgets = {
            'feedback_type': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'type': 'range'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Additional comments...',
                'rows': 3
            }),
            'emotional_response': forms.Select(attrs={'class': 'form-control'}),
        }