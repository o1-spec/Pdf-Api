from django.urls import path
from django.conf.urls.static import static
from .views import RegisterView, LoginView,LogoutView,VerifyEmailOTPView,ConvertPdfView, DownloadPageView, DownloadFileView
from django.conf import settings

urlpatterns = [
   path('register/', RegisterView.as_view(), name='register'),
   path('login/',LoginView.as_view(), name="login"),
   path('logout/',LogoutView.as_view(), name="logout"),
   path('verify_otp/<int:user_id>/', VerifyEmailOTPView.as_view(), name='verify_otp'),
   
   path('', ConvertPdfView.as_view() ,name='base-homepage'),
   path('download/<str:file_path>/', DownloadPageView.as_view(), name='download'),
   
   path('download_file/<str:file_path>/', DownloadFileView.as_view(), name='download_file'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)