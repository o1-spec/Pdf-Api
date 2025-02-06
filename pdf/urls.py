from django.urls import path
from django.conf.urls.static import static
from .views import RegisterView, LoginView,LogoutView,VerifyEmailOTPView,ConvertPdfView, DownloadPageView, DownloadFileView, PDFSummarizingView,ConvertWordView,ConvertPowerPointView, PDFTTSView, MergePDFView, SplitPDFView, CompressPDFView, ConvertExcelView
from django.conf import settings

urlpatterns = [
   path('register/', RegisterView.as_view(), name='register'),
   path('login/',LoginView.as_view(), name="login"),
   path('logout/',LogoutView.as_view(), name="logout"),
   path('verify_otp/<int:user_id>/', VerifyEmailOTPView.as_view(), name='verify_otp'),
   
   path('', ConvertPdfView.as_view() ,name='base-homepage'),
   path('download/<str:file_path>/', DownloadPageView.as_view(), name='download'),
   path('download_file/<str:file_path>/', DownloadFileView.as_view(), name='download_file'),
   
   #PDF DIFFERENT FEATURES
   path('pdf-summarizing/', PDFSummarizingView.as_view(), name='pdf_summarizing'),
   path('convert-word/', ConvertWordView.as_view(), name='convert_word'),
   path('convert-powerpoint/', ConvertPowerPointView.as_view(), name='convert_powerpoint'),
   path('pdf-tts/', PDFTTSView.as_view(), name='pdf_tts'),
   path('merge-pdf/', MergePDFView.as_view(), name='merge_pdf'),
   path('split-pdf/', SplitPDFView.as_view(), name='split_pdf'),
   path('compress-pdf/', CompressPDFView.as_view(), name='compress_pdf'),
   path('convert-excel/pdf/', ConvertExcelView.as_view(), name='convert_excel'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)