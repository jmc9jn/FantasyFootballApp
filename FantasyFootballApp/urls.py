from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include app URLs under /stats/
    path('stats/', include('stats.urls')),

    # redirect root '/' to /stats/
    path('', lambda request: redirect('/stats/')),
]