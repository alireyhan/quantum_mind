from django.urls import path
from .views import IntakeCreateView, IntakeListView, IntakeDetailView

urlpatterns = [
    path('', IntakeListView.as_view(), name='intake-list'),
    path('create/', IntakeCreateView.as_view(), name='intake-create'),
    path('<int:pk>/', IntakeDetailView.as_view(), name='intake-detail'),
]
