from rest_framework import serializers
from .models import MoodEntry, SessionFeedback, TherapeuticProfile


class MoodEntrySerializer(serializers.ModelSerializer):
    improvement = serializers.IntegerField(read_only=True)

    class Meta:
        model = MoodEntry
        fields = [
            'id', 'session', 'mood_before', 'mood_after',
            'improvement', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'improvement', 'created_at']

    def validate_mood_before(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError('Mood must be between 1 and 10.')
        return value

    def validate_mood_after(self, value):
        if value is not None and not (1 <= value <= 10):
            raise serializers.ValidationError('Mood must be between 1 and 10.')
        return value


class SessionFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionFeedback
        fields = [
            'id', 'session', 'effectiveness_rating', 'techniques_resonated',
            'techniques_to_adjust', 'general_notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_effectiveness_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class TherapeuticProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapeuticProfile
        fields = [
            'most_effective_techniques', 'least_effective_techniques',
            'average_mood_improvement_by_category', 'session_count',
            'key_themes', 'updated_at',
        ]
        read_only_fields = fields
