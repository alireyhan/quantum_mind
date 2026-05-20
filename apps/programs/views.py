from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import TherapyProgram, UserProgramEnrollment
from .serializers import (
    TherapyProgramSerializer,
    TherapyProgramListSerializer,
    UserProgramEnrollmentSerializer,
)
from apps.core.permissions import IsPremiumUser
from rest_framework.permissions import IsAdminUser


class ProgramListView(generics.ListAPIView):
    """GET /api/programs/ — List all available therapy programs."""
    serializer_class = TherapyProgramListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TherapyProgram.objects.filter(is_active=True)
        # Filter premium-only programs for non-premium users
        if not self.request.user.is_premium:
            qs = qs.filter(is_premium_only=False)
        return qs


class ProgramDetailView(generics.RetrieveAPIView):
    """GET /api/programs/<id>/ — Full program detail with all days."""
    serializer_class = TherapyProgramSerializer
    permission_classes = [IsAuthenticated]
    queryset = TherapyProgram.objects.filter(is_active=True).prefetch_related('days')


class ProgramEnrollView(generics.CreateAPIView):
    """POST /api/programs/enroll/ — Enroll the user in a program."""
    serializer_class = UserProgramEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MyEnrollmentsView(generics.ListAPIView):
    """GET /api/programs/my-enrollments/ — List the user's enrolled programs."""
    serializer_class = UserProgramEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProgramEnrollment.objects.filter(
            user=self.request.user
        ).select_related('program').prefetch_related('program__days')


class AdvanceDayView(generics.UpdateAPIView):
    """
    POST /api/programs/enrollments/<id>/advance/
    Mark the current day complete and advance to the next day.
    """
    serializer_class = UserProgramEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def get_queryset(self):
        return UserProgramEnrollment.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        enrollment = self.get_object()

        if enrollment.status != UserProgramEnrollment.STATUS_ACTIVE:
            return Response(
                {'error': True, 'detail': 'Enrollment is not active.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if enrollment.current_day >= enrollment.program.total_days:
            enrollment.status = UserProgramEnrollment.STATUS_COMPLETED
            enrollment.completed_at = timezone.now()
            enrollment.save()
            return Response(
                {'detail': 'Program completed!', **UserProgramEnrollmentSerializer(enrollment).data},
                status=status.HTTP_200_OK,
            )

        enrollment.current_day += 1
        enrollment.save()
        return Response(
            UserProgramEnrollmentSerializer(enrollment).data,
            status=status.HTTP_200_OK,
        )


class ProgramCreateView(generics.CreateAPIView):
    """POST /api/programs/create/ — Create a new program (Staff only)"""
    serializer_class = TherapyProgramSerializer
    permission_classes = [IsAdminUser]


class ProgramDayCreateView(generics.CreateAPIView):
    """POST /api/programs/days/create/ — Add a day to a program (Staff only)"""
    from .serializers import ProgramDayCreateSerializer
    serializer_class = ProgramDayCreateSerializer
    permission_classes = [IsAdminUser]
