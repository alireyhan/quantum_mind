import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import MoodEntry, SessionFeedback, TherapeuticProfile
from .serializers import (
    MoodEntrySerializer,
    SessionFeedbackSerializer,
    TherapeuticProfileSerializer,
)
from .services import ProfileService

logger = logging.getLogger(__name__)


class MoodEntryCreateView(generics.CreateAPIView):
    """POST /api/feedback/mood/ — Log a mood entry (before or after session)."""
    serializer_class = MoodEntrySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MoodEntryUpdateView(generics.UpdateAPIView):
    """PATCH /api/feedback/mood/<id>/ — Update mood_after score post-session."""
    serializer_class = MoodEntrySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch']

    def get_queryset(self):
        return MoodEntry.objects.filter(user=self.request.user)


class SessionFeedbackCreateView(generics.CreateAPIView):
    """
    POST /api/feedback/session/
    Submit post-session feedback, which triggers a profile rebuild.
    """
    serializer_class = SessionFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        feedback = serializer.save()
        # Rebuild the adaptive therapeutic profile asynchronously
        try:
            profile_service = ProfileService()
            profile_service.rebuild_profile(self.request.user)
        except Exception as e:
            logger.warning(
                'Profile rebuild failed after feedback from user %s: %s',
                self.request.user.id, e
            )


class TherapeuticProfileView(APIView):
    """GET /api/feedback/profile/ — Return the user's adaptive therapeutic profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = TherapeuticProfile.objects.get_or_create(user=request.user)
        serializer = TherapeuticProfileSerializer(profile)
        return Response(serializer.data)


class MoodHistoryView(generics.ListAPIView):
    """GET /api/feedback/mood/ — List all mood entries for the current user."""
    serializer_class = MoodEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MoodEntry.objects.filter(user=self.request.user)
