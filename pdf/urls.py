from django.urls import path
from django.conf.urls.static import static
from .views import RegisterView, LoginView,LogoutView,VerifyEmailOTPView,ConvertPdfView, DownloadView
from django.conf import settings

urlpatterns = [
   path('register/', RegisterView.as_view(), name='register'),
   path('login/',LoginView.as_view(), name="login"),
   path('logout/',LogoutView.as_view(), name="logout"),
   path('verify_otp/<int:user_id>/', VerifyEmailOTPView.as_view(), name='verify_otp'),
   
   path('', ConvertPdfView.as_view() ,name='base-homepage'),
    path('download/<str:file_path>/', DownloadView.as_view(), name='download'),
   
   #path('pdf-home/', PdfHomePageView.as_view(), name='pdf-home')\
   # path('pdf_convert/', ConvertView.as_view(), name='pdf_convert'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)