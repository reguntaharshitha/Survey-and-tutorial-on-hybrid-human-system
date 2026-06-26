from django import forms
from django.contrib.auth import authenticate
from users.models import CustomUser


class AdminLoginForm(forms.Form):
    """Custom admin login form that validates superuser/staff credentials"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid username or password.",
                    code='invalid_login'
                )
            
            # Check if user is an admin (superuser or staff)
            if not (self.user_cache.is_superuser or self.user_cache.is_staff):
                raise forms.ValidationError(
                    "This account does not have admin permissions.",
                    code='admin_required'
                )
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache if hasattr(self, 'user_cache') else None
