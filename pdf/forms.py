from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

#Content for forms.py
class UserRegistrationForm(forms.Form):
    username= forms.CharField(max_length=100,label="Username")
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput,label="Password")
    confirmPassword= forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("confirmPassword")
        if(password1 and password2 and password1 != password2):
            raise ValidationError("Password do not match")
        return password2
    
    def save(self, commit= True):
        user =User(
            username = self.cleaned_data['username'],
            email = self.cleaned_data['email']
        )
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    
class EmailOTPVerificationForm(forms.Form):
    email_otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'placeholder': 'Enter Email OTP'})
    )
    
