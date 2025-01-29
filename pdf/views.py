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

class DownloadView(View):
    # template_name = "download.html"
     
    def get(self, request, file_path):
        # file_name = request.GET.get("file_path")
        file_path = os.path.join(settings.MEDIA_ROOT, "conversions", file_path)

        if not os.path.exists(file_path):
            raise Http404("File not found.")

        return FileResponse(open(file_path, "rb"), as_attachment=True)

    
# class ConvertPdfView(View):
#     template_name = 'homepage.html'

#     def get(self, request):
#         return render(request, self.template_name)

#     def post(self, request):
#         conversion_type = request.POST.get('conversion_type')
#         uploaded_files = request.FILES.getlist('file')

#         if not uploaded_files:
#             messages.error(request, "Please upload a file to convert.")
#             return redirect('base-homepage')

#         try:
#             output_folder = os.path.join(settings.MEDIA_ROOT, 'converted')
#             os.makedirs(output_folder, exist_ok=True)

#             converted_file_path = None

#             if conversion_type == 'image_to_pdf':
#                 image_paths = []
#                 for uploaded_file in uploaded_files:
#                     temp_path = os.path.join(output_folder, uploaded_file.name)
#                     with open(temp_path, 'wb+') as temp_file:
#                         for chunk in uploaded_file.chunks():
#                             temp_file.write(chunk)
#                     image_paths.append(temp_path)
                
#                 converted_file_path = convert_images_to_pdf(image_paths, os.path.join(output_folder, 'output.pdf'))

#             elif conversion_type == 'pdf_to_image':
#                 pdf_file = uploaded_files[0]
#                 pdf_path = os.path.join(output_folder, pdf_file.name)
#                 with open(pdf_path, 'wb+') as temp_file:
#                     for chunk in pdf_file.chunks():
#                        temp_file.write(chunk)
#                 converted_result = convert_pdf_to_images(pdf_path, output_folder)
#                 if converted_result:
#                     if converted_result["type"] == "single":
#                         converted_file_path = converted_result["file_path"]
#                     elif converted_result["type"] == "zip":
#                         converted_file_path = converted_result["file_path"]
#                 else:
#                     messages.error(request, "PDF to image conversion failed.")
#                     return redirect('base-homepage')

#             if converted_file_path:
#                 if request.user.is_authenticated:
#                     FileConversion.objects.create(
#                         user=request.user,
#                         original_file=uploaded_files[0].name,
#                         converted_file=os.path.basename(converted_file_path),
#                         conversion_type=conversion_type
#                     )
#                 relative_path = os.path.relpath(converted_file_path, settings.MEDIA_ROOT)
#                 file_url = os.path.join(settings.MEDIA_URL, relative_path)
#                 encoded_url = urllib.parse.quote(file_url)
#                 return redirect(f"{reverse_lazy('download')}?file_url={encoded_url}")
#             else:
#                 messages.error(request, "Conversion failed. Please try again.")
#                 return redirect('base-homepage')

#         except Exception as e:
#             messages.error(request, f"An error occurred: {str(e)}")
#             return redirect('base-homepage')
        
    
# class UserProfileView(LoginRequiredMixin, View):
#     template_name = 'profile.html'

#     def get(self, request):
#         conversions = FileConversion.objects.filter(user=request.user)
#         return render(request, self.template_name, {'conversions': conversions})

# class DownloadView(TemplateView):
#     template_name = "download.html"

#     def get(self, request, *args, **kwargs):
#         file_url = request.GET.get('file_url')
        
#         if not file_url:
#             messages.error(request, "No file URL provided.")
#             return redirect('base-homepage')

#         try:
#             # Convert URL to filesystem path
#             relative_path = urllib.parse.unquote(file_url).lstrip('/')
#             file_path = os.path.join(settings.MEDIA_ROOT, relative_path.replace(settings.MEDIA_URL.lstrip('/'), ''))

#             if not os.path.exists(file_path):
#                 raise Http404("File not found")

#             # # For initial page load, just show the download page
#             # if not request.GET.get('download'):
#             #     return render(request, self.template_name, {
#             #         'file_url': file_url,
#             #         'filename': os.path.basename(file_path)
#             #     })

#             # For actual download request
#             response = FileResponse(
#                 open(file_path, 'rb'),
#                 as_attachment=True,
#                 filename=os.path.basename(file_path)
#             )
#             return response

#         except Exception as e:
#             messages.error(request, f"Error accessing file: {str(e)}")
#             return redirect('base-homepage')
        
#     def post(self, request, *args, **kwargs):
#         messages.success(request, "Thank you for using our service!")
#         return redirect('base-homepage' if request.user.is_authenticated else 'register')