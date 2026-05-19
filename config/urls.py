from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Apps
    path('api/users/', include('apps.users.urls')),
    path('api/intake/', include('apps.intake.urls')),
    path('api/sessions/', include('apps.sessions.urls')),
    path('api/credits/', include('apps.credits.urls')),
    path('api/feedback/', include('apps.feedback.urls')),
    path('api/programs/', include('apps.programs.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
