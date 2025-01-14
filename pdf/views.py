from django.shortcuts import render,redirect
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView,LogoutView
from .forms import UserRegistrationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import login

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
    redirect_authenticated_user = True
    success_url = reverse_lazy('base-pdf')
    
    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request,user)
        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('base-pdf')
        return super().get(request, *args, **kwargs)
    
class LoginView(LoginView):
    template_name='login.html'
    # fields = '__all__'
    redirect_authenticated_user= True
    
    def get_success_url(self):
        return reverse_lazy('base-pdf')

class LogoutView(LogoutView):
    next_page= reverse_lazy("login") 