from django.contrib import admin
from .models import IntakeResponse


@admin.register(IntakeResponse)
class IntakeResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'main_issue_short', 'problem_category', 'session_duration_minutes', 'created_at']
    list_filter = ['problem_category', 'representational_system', 'post_session_state']
    search_fields = ['user__email', 'main_issue']
    readonly_fields = ['problem_category', 'created_at', 'updated_at']

    def main_issue_short(self, obj):
        issue = obj.main_issue or ''
        return issue[:60] + '...' if len(issue) > 60 else issue
    main_issue_short.short_description = 'Main Issue'
