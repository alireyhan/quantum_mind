from rest_framework import serializers
from .models import TherapySession, AudioAsset


class AudioAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioAsset
        fields = ['cdn_url', 'file_size_bytes', 'duration_seconds', 'format', 'created_at']


class TherapySessionSerializer(serializers.ModelSerializer):
    audio_asset = AudioAssetSerializer(read_only=True)
    intake_id = serializers.IntegerField(write_only=True)
    program_day_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = TherapySession
        fields = [
            'id', 'status', 'duration_minutes', 'credits_used', 'language',
            'script_text', 'script_chunks', 'audio_url',
            'audio_duration_seconds', 'techniques_used', 'problem_category',
            'error_message', 'created_at', 'completed_at',
            'audio_asset', 'intake_id', 'program_day_id',
        ]
        read_only_fields = [
            'id', 'status', 'credits_used', 'script_text', 'script_chunks',
            'audio_url', 'audio_duration_seconds', 'techniques_used',
            'problem_category', 'error_message', 'created_at', 'completed_at',
        ]


class TherapySessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for session list views."""
    class Meta:
        model = TherapySession
        fields = [
            'id', 'status', 'duration_minutes', 'credits_used',
            'audio_url', 'problem_category', 'created_at', 'completed_at',
        ]


class SessionCreateSerializer(serializers.Serializer):
    """Input serializer for session creation endpoint.

    All fields are optional to support lightweight "trigger" requests from the
    client. Server will fall back to the user's latest intake and default
    duration when not provided.
    """
    intake_id = serializers.IntegerField(required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(required=False, allow_null=True, min_value=10, max_value=45)
    program_day_id = serializers.IntegerField(required=False, allow_null=True)
    language = serializers.CharField(required=False, allow_null=True, max_length=10, default='en')
