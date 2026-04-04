from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include app URLs under /basic/
    path('basic/', include('basic.urls')),

    # redirect root '/' to /basic/
    path('', lambda request: redirect('/basic/')),
]