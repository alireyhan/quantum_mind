from django.contrib import admin
from .models import MoodEntry, SessionFeedback, TherapeuticProfile


@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'mood_before', 'mood_after', 'improvement', 'session_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']


@admin.register(SessionFeedback)
class SessionFeedbackAdmin(admin.ModelAdmin):
    list_display = ['session', 'effectiveness_rating', 'created_at']
    list_filter = ['effectiveness_rating']
    search_fields = ['session__user__email']


@admin.register(TherapeuticProfile)
class TherapeuticProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_count', 'updated_at']
    readonly_fields = [
        'most_effective_techniques', 'least_effective_techniques',
        'average_mood_improvement_by_category', 'session_count',
        'key_themes', 'updated_at',
    ]
    search_fields = ['user__email']
