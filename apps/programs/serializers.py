from rest_framework import serializers
from .models import TherapyProgram, ProgramDay, UserProgramEnrollment


class ProgramDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramDay
        fields = ['id', 'day_number', 'title', 'description', 'focus_technique']


class TherapyProgramSerializer(serializers.ModelSerializer):
    days = ProgramDaySerializer(many=True, read_only=True)
    enrolled = serializers.SerializerMethodField()

    class Meta:
        model = TherapyProgram
        fields = [
            'id', 'name', 'description', 'total_days', 'category',
            'is_premium_only', 'thumbnail_url', 'sort_order', 'days', 'enrolled',
        ]

    def get_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user).exists()
        return False


class TherapyProgramListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer without nested days."""
    enrolled = serializers.SerializerMethodField()

    class Meta:
        model = TherapyProgram
        fields = [
            'id', 'name', 'description', 'total_days', 'category',
            'is_premium_only', 'thumbnail_url', 'enrolled',
        ]

    def get_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user).exists()
        return False


class UserProgramEnrollmentSerializer(serializers.ModelSerializer):
    program = TherapyProgramListSerializer(read_only=True)
    program_id = serializers.IntegerField(write_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    current_program_day = serializers.SerializerMethodField()

    class Meta:
        model = UserProgramEnrollment
        fields = [
            'id', 'program', 'program_id', 'current_day', 'status',
            'progress_percentage', 'current_program_day',
            'started_at', 'completed_at',
        ]
        read_only_fields = [
            'id', 'current_day', 'status', 'progress_percentage',
            'started_at', 'completed_at',
        ]

    def get_current_program_day(self, obj):
        day = obj.get_current_program_day()
        if day:
            return ProgramDaySerializer(day).data
        return None


class ProgramDayCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramDay
        fields = ['id', 'program', 'day_number', 'title', 'description', 'focus_technique']
