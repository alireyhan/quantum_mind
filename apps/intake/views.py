from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import IntakeResponse
from .serializers import IntakeResponseSerializer, IntakeResponseListSerializer
from services.ai_service import OpenAIService


class IntakeCreateView(generics.CreateAPIView):
    """POST /api/intake/ — Submit a new clinical intake wizard response."""
    serializer_class = IntakeResponseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        ai_service = OpenAIService()
        data = serializer.validated_data
        # Auto-diagnose the problem category before persisting
        category = ai_service.diagnose_problem_category({
            'main_issue': data.get('main_issue', ''),
            'triggers': data.get('triggers', []),
            'symptoms': data.get('symptoms', []),
        })
        serializer.save(user=self.request.user, problem_category=category)


class IntakeListView(generics.ListAPIView):
    """GET /api/intake/ — List all intake responses for the current user."""
    serializer_class = IntakeResponseListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IntakeResponse.objects.filter(user=self.request.user)


class IntakeDetailView(generics.RetrieveAPIView):
    """GET /api/intake/<id>/ — Retrieve a specific intake response."""
    serializer_class = IntakeResponseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IntakeResponse.objects.filter(user=self.request.user)
