from django.shortcuts import render,redirect
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView,LogoutView
from .forms import UserRegistrationForm, EmailOTPVerificationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth. models import User
from django.contrib.auth import login
from .utils import generate_otp, verify_otp
from .models import CustomUser
from django.core.mail import send_mail
from django.conf import settings

#Write your views
class PdfCreateView(TemplateView, LoginRequiredMixin):
    template_name = "pdfhomepage.html"
    
    # def get(self, request, *args, **kwargs):
    #     if not request.user.is_authenticated:
    #         return redirect('register')
    #     return super().get(request, *args, **kwargs)
    
# class PdfHomePageView(LoginRequiredMixin, TemplateView):
#     template_name = "pdfhomepage.html" 

class RegisterView(FormView):
    template_name = "register.html"
    form_class = UserRegistrationForm
    #redirect_authenticated_user = True
    success_url = reverse_lazy('base-pdf')
    
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        email = form.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            messages.error(self.request, 'An account with this email already exists. Please login.')
            return redirect('register')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(self.request, 'An account with this username already exists. Please use a different one.')
            return redirect('register')
        
        user = CustomUser.objects.create_user(username=username, email=email, password=password)
        email_otp = generate_otp()
        user.email_otp = email_otp
        user.save()
        
        send_mail(
            'Your OTP for Email Verification',
            f'Your OTP is: {email_otp}',
            settings.EMAIL_HOST_USER,
            [email],
        )
        self.success_url = reverse_lazy('verify_otp', kwargs={'user_id': user.id})
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('base-pdf')
        return super().get(request, *args, **kwargs)

    
class VerifyEmailOTPView(FormView):
    template_name = "verify_otp.html"
    form_class = EmailOTPVerificationForm
    success_url = reverse_lazy('base-pdf')
    
    def form_valid(self, form):
        email_otp = form.cleaned_data.get('email_otp')
        user_id = self.kwargs.get('user_id')

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            messages.error(self.request, "User not found.")
            return redirect('register')
        
        if verify_otp(email_otp, user.email_otp):
            user.is_email_verified = True
            user.email_otp = None
            user.save()
            login(self.request, user)
            messages.success(self.request, "Email verified successfully.")
            return super().form_valid(form)
        else:
            messages.error(self.request, "Invalid OTP. Please try again.")
            return redirect('verify_otp', user_id=user.id)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_id'] = self.kwargs.get('user_id')
        context['message'] = "Please check your email for the OTP."
        return context
        
    
class LoginView(LoginView):
    template_name='login.html'
    # fields = '__all__'
    redirect_authenticated_user= True
    
    def get_success_url(self):
        return reverse_lazy('base-pdf')
    
    def form_invalid(self, form):
        username = self.request.POST.get('username')
        if not User.objects.filter(username=username).exists():
            messages.error(self.request, 'User does not exist. Please register.')
        else:
            messages.error(self.request, 'Incorrect password. Please try again.')
        return super().form_invalid(form)

class LogoutView(LogoutView):
    next_page= reverse_lazy("login") 
    def dispatch(self, request, *args, **kwargs):
        if "_messages" in request.session:
            del request.session["_messages"]
        return super().dispatch(request, *args, **kwargs)