from rest_framework import serializers
from django.conf import settings
from .models import IntakeResponse


class IntakeResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntakeResponse
        fields = '__all__'
        read_only_fields = ['id', 'user', 'problem_category', 'created_at', 'updated_at']

    def validate_session_duration_minutes(self, value):
        if not (settings.MIN_SESSION_DURATION <= value <= settings.MAX_SESSION_DURATION):
            raise serializers.ValidationError(
                f'Session duration must be between {settings.MIN_SESSION_DURATION} '
                f'and {settings.MAX_SESSION_DURATION} minutes.'
            )
        return value

    def validate_mood_before(self, value):
        """Ensure mood scores are in range."""
        if not (1 <= value <= 10):
            raise serializers.ValidationError('Mood score must be between 1 and 10.')
        return value

    def validate(self, data):
        # Warn if no advanced fields are provided (they're optional but unlock deeper techniques)
        if not any([
            data.get('repeating_thoughts'),
            data.get('negative_beliefs'),
            data.get('has_inner_conflict') is not None,
        ]):
            # Not an error — just allow it; basic session will still be generated
            pass
        return data


class IntakeResponseListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""
    class Meta:
        model = IntakeResponse
        fields = [
            'id', 'main_issue', 'problem_category',
            'session_duration_minutes', 'created_at',
        ]
