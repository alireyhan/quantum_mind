from django.urls import path
from .views import (
    MoodEntryCreateView,
    MoodEntryUpdateView,
    MoodHistoryView,
    SessionFeedbackCreateView,
    TherapeuticProfileView,
)

urlpatterns = [
    path('mood/', MoodHistoryView.as_view(), name='mood-list'),
    path('mood/create/', MoodEntryCreateView.as_view(), name='mood-create'),
    path('mood/<int:pk>/', MoodEntryUpdateView.as_view(), name='mood-update'),
    path('session/', SessionFeedbackCreateView.as_view(), name='session-feedback'),
    path('profile/', TherapeuticProfileView.as_view(), name='therapeutic-profile'),
]
