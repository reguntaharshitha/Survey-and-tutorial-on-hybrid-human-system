from django import forms
from .models import Recommendation

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['recommendation_type', 'content', 'confidence', 'context']
        widgets = {
            'recommendation_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'confidence': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 1, 'step': 0.01}),
            'context': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }