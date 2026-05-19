from django.contrib import admin
from .models import TherapySession, AudioAsset


class AudioAssetInline(admin.StackedInline):
    model = AudioAsset
    extra = 0
    readonly_fields = ['cdn_url', 'file_key', 'file_size_bytes', 'format', 'created_at']


@admin.register(TherapySession)
class TherapySessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'duration_minutes', 'credits_used', 'problem_category', 'created_at']
    list_filter = ['status', 'problem_category']
    search_fields = ['user__email', 'problem_category']
    readonly_fields = ['status', 'script_text', 'audio_url', 'created_at', 'completed_at', 'error_message']
    inlines = [AudioAssetInline]


@admin.register(AudioAsset)
class AudioAssetAdmin(admin.ModelAdmin):
    list_display = ['session', 'cdn_url', 'file_size_bytes', 'format', 'created_at']
    readonly_fields = ['created_at']
