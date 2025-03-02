from django.shortcuts import render,redirect
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView,LogoutView
from .forms import UserRegistrationForm, EmailOTPVerificationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .utils import convert_images_to_pdf,convert_pdf_to_images, convert_pdf_to_word,convert_word_to_pdf, convert_excel_to_pdf,convert_pdf_to_excel,compress_pdf, split_pdf,merge_pdfs
from django.contrib.auth. models import User
from django.contrib.auth import login
from .utils import generate_otp, verify_otp
from .models import CustomUser
from django.http import FileResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from .models import  FileConversion
import os
import zipfile
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View

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
        # Define possible directories
        possible_dirs = [
            os.path.join(settings.MEDIA_ROOT, "merged_pdfs"),
            os.path.join(settings.MEDIA_ROOT, "conversions"),
            os.path.join(settings.MEDIA_ROOT, "split_pdfs")
        ]

        # Check where the file exists
        file_full_path = None
        for directory in possible_dirs:
            temp_path = os.path.join(directory, file_path)
            if os.path.exists(temp_path):
                file_full_path = temp_path
                break

        if not file_full_path:
            raise Http404("File not found.")

        return FileResponse(open(file_full_path, "rb"), as_attachment=True, filename=os.path.basename(file_full_path))
    
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

class ConvertWordView(TemplateView):
    template_name = "convert_word.html"

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        conversion_type = request.POST.get("conversion_type")

        if not uploaded_file:
            messages.error(request, "Please upload a file.")
            return redirect("convert_word")

        output_folder = os.path.join(settings.MEDIA_ROOT, "conversions")
        os.makedirs(output_folder, exist_ok=True)

        file_path = os.path.join(output_folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        if conversion_type == "word_to_pdf":
            pdf_path = convert_word_to_pdf(file_path, output_folder)
            if pdf_path:
                return redirect("download", file_path=os.path.basename(pdf_path))

        elif conversion_type == "pdf_to_word":
            docx_path = convert_pdf_to_word(file_path, output_folder)
            if docx_path:
                return redirect("download", file_path=os.path.basename(docx_path))

        messages.error(request, "Conversion failed. Please try again.")
        return redirect("convert_word")
    

class ConvertExcelView(TemplateView):
    template_name = "convert_excel.html"

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        conversion_type = request.POST.get("conversion_type")

        if not uploaded_file:
            messages.error(request, "Please upload a file.")
            return redirect("convert_excel")

        output_folder = os.path.join(settings.MEDIA_ROOT, "conversions")
        os.makedirs(output_folder, exist_ok=True)

        file_path = os.path.join(output_folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        if conversion_type == "pdf_to_excel":
            excel_path = convert_pdf_to_excel(file_path, output_folder)
            if excel_path:
                return redirect("download", file_path=os.path.basename(excel_path))

        elif conversion_type == "excel_to_pdf":
            pdf_path = convert_excel_to_pdf(file_path, output_folder)
            if pdf_path:
                return redirect("download", file_path=os.path.basename(pdf_path))

        messages.error(request, "Conversion failed. Please try again.")
        return redirect("convert_excel")

class CompressPDFView(TemplateView):
    template_name = "compress_pdf.html"

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        
        if not uploaded_file:
            messages.error(request, "Please upload a PDF file.")
            return redirect("compress_pdf")

        output_folder = os.path.join(settings.MEDIA_ROOT, "compressed_pdfs")
        os.makedirs(output_folder, exist_ok=True)

        # Save uploaded PDF temporarily
        input_pdf_path = os.path.join(output_folder, uploaded_file.name)
        with open(input_pdf_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Define output compressed PDF path
        output_pdf_path = os.path.join(output_folder, f"compressed_{uploaded_file.name}")

        # Compress the PDF
        compressed_pdf = compress_pdf(input_pdf_path, output_pdf_path)

        if compressed_pdf:
            return redirect("download", file_path=os.path.basename(compressed_pdf))

        messages.error(request, "Compression failed. Please try again.")
        return redirect("compress_pdf")
    
class MergePDFView(TemplateView):
    template_name = "merge_pdf.html"

    def post(self, request):
        uploaded_files = request.FILES.getlist("files")
        if not uploaded_files or len(uploaded_files) < 2:
            messages.error(request, "Please upload at least two PDF files.")
            return redirect("merge_pdf")
        
        output_folder = os.path.join(settings.MEDIA_ROOT, "merged_pdfs")
        os.makedirs(output_folder, exist_ok=True)
        
        file_paths = []
        for uploaded_file in uploaded_files:
            file_path = os.path.join(output_folder, uploaded_file.name)
            with open(file_path, "wb") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            file_paths.append(file_path)
        
        merged_pdf_path = merge_pdfs(file_paths, os.path.join(output_folder, "merged_output.pdf"))
        
        if merged_pdf_path:
            return redirect("download", file_path=os.path.basename(merged_pdf_path))
        
        messages.error(request, "Merging failed. Please try again.")
        return redirect("merge_pdf")

class SplitPDFView(TemplateView):
    template_name = "split_pdf.html"

    def post(self, request):
        uploaded_file = request.FILES.get("pdf_file")
        page_ranges = request.POST.get("page_range")

        if not uploaded_file:
            messages.error(request, "Please upload a PDF file.")
            return redirect("split_pdf")

        output_folder = os.path.join(settings.MEDIA_ROOT, "split_pdfs")
        os.makedirs(output_folder, exist_ok=True)

        input_pdf_path = os.path.join(output_folder, uploaded_file.name)
        with open(input_pdf_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        split_files = split_pdf(input_pdf_path, output_folder, page_ranges)

        if split_files:
            # If multiple files, create a ZIP
            zip_path = os.path.join(output_folder, "split_pages.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for file in split_files:
                    zipf.write(file, os.path.basename(file))

            return redirect("download", file_path=os.path.basename(zip_path))

        messages.error(request, "Splitting failed. Please try again.")
        return redirect("split_pdf")


class PDFSummarizingView(TemplateView):
    template_name = "pdf_summarizing.html"

class ConvertPowerPointView(TemplateView):
    template_name = "convert_powerpoint.html"

class PDFTTSView(TemplateView):
    template_name = "pdf_tts.html"
