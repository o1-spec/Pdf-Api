from django.urls import path
from .views import RegisterView, PdfCreateView, LoginView,LogoutView

urlpatterns = [
   path('register/', RegisterView.as_view(), name='register'),
   path('login/',LoginView.as_view(), name="login"),
   path('logout/',LogoutView.as_view(), name="logout"),
   
   path('', PdfCreateView.as_view() ,name='base-pdf'),
#    path('pdf-home/', PdfHomePageView.as_view(), name='pdf-home')
]