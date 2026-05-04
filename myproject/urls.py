from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# =====================================================================
# SYSTEM HEALTH CHECK & ROOT ENDPOINT
# =====================================================================

def api_root(request):
    """
    Root endpoint returning a JSON payload for system health monitoring
    and general API routing information.
    """
    return JsonResponse({
        "developer": "Muhammad Umar",
        "system": "Student OS Backend API",
        "status": "Operational",
        "environment": "Production Ready",
        "version": "1.0.0"
    })

# =====================================================================
# MAIN URL ROUTING
# =====================================================================

urlpatterns = [
    # API Health Check Endpoint
    path('', api_root, name='api-root'),  
    
    # Django Administrative Panel
    path('admin/', admin.site.urls),
    
    # Core Application Endpoints Routing
    path('api/', include('myapp.urls')),
]
