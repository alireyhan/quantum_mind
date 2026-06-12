import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.conf import settings
from .models import TherapySession
from .serializers import (
    TherapySessionSerializer,
    TherapySessionListSerializer,
    SessionCreateSerializer,
)
from apps.credits.services import CreditService

logger = logging.getLogger(__name__)


class SessionCreateView(generics.CreateAPIView):
    """
    POST /api/sessions/
    Creates a TherapySession, deducts credits, and queues async generation.
    Returns 202 Accepted immediately — client should poll for status.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SessionCreateSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        intake_id = serializer.validated_data.get('intake_id')
        duration = serializer.validated_data.get('duration_minutes')
        program_day_id = serializer.validated_data.get('program_day_id')
        language = serializer.validated_data.get('language') or 'en'

        # If the client didn't provide an intake, use the user's most recent one
        from apps.intake.models import IntakeResponse
        intake = None
        if intake_id:
            try:
                intake = IntakeResponse.objects.get(id=intake_id, user=user)
            except IntakeResponse.DoesNotExist:
                return Response({'error': True, 'detail': 'Intake not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            intake = IntakeResponse.objects.filter(user=user).order_by('-created_at').first()
            if not intake:
                return Response({'error': True, 'detail': 'No intake found for user; provide intake_id.'}, status=status.HTTP_400_BAD_REQUEST)

        # If duration not provided, fall back to intake preference or minimum
        if duration is None:
            duration = getattr(intake, 'session_duration_minutes', None) or settings.MIN_SESSION_DURATION


        # Check credit balance
        credit_service = CreditService()
        if not credit_service.has_sufficient_credits(user, duration):
            available = credit_service.get_available_credits(user)
            return Response(
                {
                    'error': True,
                    'detail': 'Insufficient credits.',
                    'required': duration,
                    'available': available,
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        # Deduct credits atomically
        credit_service.deduct_credits(user, duration, transaction_type='session_use')

        # Determine category
        category = serializer.validated_data.get('category')
        if not category and intake:
            category = intake.problem_category

        # Create the session record
        session = TherapySession.objects.create(
            user=user,
            intake=intake,
            duration_minutes=duration,
            credits_used=duration,
            language=language,
            problem_category=category or '',
            program_day_id=program_day_id,
            status=TherapySession.STATUS_PENDING,
        )

        # Queue the async generation task
        try:
            from .tasks import generate_session_task
            generate_session_task.delay(session.id)
        except Exception as e:
            logger.error('Failed to queue generation task for session %s: %s', session.id, e)
            # Refund credits if we can't queue
            credit_service.refund_credits(user, session, 'Failed to queue generation task.')
            session.status = TherapySession.STATUS_FAILED
            session.error_message = str(e)
            session.save()
            return Response(
                {'error': True, 'detail': 'Failed to start session generation. Credits refunded.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            TherapySessionSerializer(session).data,
            status=status.HTTP_202_ACCEPTED,
        )


class SessionListView(generics.ListAPIView):
    """GET /api/sessions/ — List all sessions for the current user."""
    serializer_class = TherapySessionListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TherapySession.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class SessionDetailView(generics.RetrieveAPIView):
    """GET /api/sessions/<id>/ — Poll session status and retrieve results."""
    serializer_class = TherapySessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TherapySession.objects.filter(user=self.request.user).select_related('audio_asset')
