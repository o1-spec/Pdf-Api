from django.shortcuts import render,redirect
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView,LogoutView
from .forms import UserRegistrationForm, EmailOTPVerificationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .utils import convert_images_to_pdf,convert_pdf_to_images
from django.contrib.auth. models import User
from django.contrib.auth import login
from .utils import generate_otp, verify_otp
from .models import CustomUser
from django.http import FileResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from .models import  FileConversion
import os
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
import urllib

#Write your views
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
            return redirect('base-homepage')
        return super().get(request, *args, **kwargs)

    
class VerifyEmailOTPView(FormView):
    template_name = "verify_otp.html"
    form_class = EmailOTPVerificationForm
    success_url = reverse_lazy('base-homepage')
    
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
        return reverse_lazy('base-homepage')
    
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
    
class ConvertPdfView(TemplateView):
    template_name = 'homepage.html'

    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        uploaded_files = request.FILES.getlist("file")
        conversion_type = request.POST.get("conversion_type")

        if not uploaded_files:
            messages.error(request, "Please upload a file.")
            return redirect("base-homepage")

        output_folder = os.path.join(settings.MEDIA_ROOT, "conversions")
        os.makedirs(output_folder, exist_ok=True)
        
        saved_file_paths = []
        for uploaded_file in uploaded_files:
            file_path = os.path.join(output_folder, uploaded_file.name)
            with open(file_path, "wb") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            saved_file_paths.append(file_path)

        if conversion_type == "image_to_pdf":
            pdf_path = convert_images_to_pdf(saved_file_paths, os.path.join(output_folder, "output.pdf"))
            if pdf_path:
                return redirect("download", file_path=os.path.basename(pdf_path))

        elif conversion_type == "pdf_to_image":
            uploaded_pdf = uploaded_files[0]
            pdf_path = os.path.join(output_folder, uploaded_pdf.name)
            with open(pdf_path, "wb") as f:
                for chunk in uploaded_pdf.chunks():
                    f.write(chunk)
    
            output = convert_pdf_to_images(pdf_path, output_folder)

            if output:
                return redirect("download", file_path=os.path.basename(output["file_path"]))

        messages.error(request, "Conversion failed. Please try again.")
        return redirect("base-homepage")

class DownloadFileView(View):
    def get(self, request, file_path):
        file_path = os.path.join(settings.MEDIA_ROOT, "conversions", file_path)

        if not os.path.exists(file_path):
            raise Http404("File not found.")

        return FileResponse(open(file_path, "rb"), as_attachment=True)
    
class DownloadPageView(TemplateView):
    template_name = 'download.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the file name from the URL keyword argument
        file_path = self.kwargs.get('file_path')
        # Build a full URL for the download file view
        context['file_url'] = self.request.build_absolute_uri(
            reverse_lazy('download_file', kwargs={'file_path': file_path})
        )
        return context
    

class PDFSummarizingView(TemplateView):
    template_name = "pdf_summarizing.html"

class ConvertWordView(TemplateView):
    template_name = "convert_word.html"

class ConvertPowerPointView(TemplateView):
    template_name = "convert_powerpoint.html"

class PDFTTSView(TemplateView):
    template_name = "pdf_tts.html"

class MergePDFView(TemplateView):
    template_name = "merge_pdf.html"

class SplitPDFView(TemplateView):
    template_name = "split_pdf.html"

class CompressPDFView(TemplateView):
    template_name = "compress_pdf.html"

class ConvertExcelView(TemplateView):
    template_name = "convert_excel.html"