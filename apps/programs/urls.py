from django.urls import path
from .views import (
    ProgramListView,
    ProgramDetailView,
    ProgramEnrollView,
    MyEnrollmentsView,
    AdvanceDayView,
)

urlpatterns = [
    path('', ProgramListView.as_view(), name='program-list'),
    path('<int:pk>/', ProgramDetailView.as_view(), name='program-detail'),
    path('enroll/', ProgramEnrollView.as_view(), name='program-enroll'),
    path('my-enrollments/', MyEnrollmentsView.as_view(), name='my-enrollments'),
    path('enrollments/<int:pk>/advance/', AdvanceDayView.as_view(), name='advance-day'),
]
