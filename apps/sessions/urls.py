from django.urls import path
from .views import SessionCreateView, SessionListView, SessionDetailView

urlpatterns = [
    path('', SessionListView.as_view(), name='session-list'),
    path('create/', SessionCreateView.as_view(), name='session-create'),
    path('<int:pk>/', SessionDetailView.as_view(), name='session-detail'),
]
