from django.contrib import admin
from .models import TherapyProgram, ProgramDay, UserProgramEnrollment


class ProgramDayInline(admin.TabularInline):
    model = ProgramDay
    extra = 1
    ordering = ['day_number']


@admin.register(TherapyProgram)
class TherapyProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'total_days', 'is_active', 'is_premium_only', 'sort_order']
    list_editable = ['is_active', 'is_premium_only', 'sort_order']
    list_filter = ['category', 'is_active', 'is_premium_only']
    search_fields = ['name', 'description']
    inlines = [ProgramDayInline]


@admin.register(UserProgramEnrollment)
class UserProgramEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'program', 'current_day', 'status', 'progress_percentage', 'started_at']
    list_filter = ['status', 'program']
    search_fields = ['user__email', 'program__name']
    readonly_fields = ['started_at', 'completed_at', 'progress_percentage']
