from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse  # HttpResponse ki jagah JsonResponse use karenge

# Professional API jaisa Home page
def home(request):
    return JsonResponse({
        "developer": "Umer Mirza",
        "message": "Welcome",
        "status": "Server is Running smoothly ",
    })

urlpatterns = [
    path('', home),  
    path('admin/', admin.site.urls),
    
    # Aapki 'myapp' ki sari APIs ko 'api/' ke raste se connect kar diya
    path('api/', include('myapp.urls')),
]