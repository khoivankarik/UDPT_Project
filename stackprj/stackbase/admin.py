from django.contrib import admin
from .models import Question, Comment, Tag, Category, Report

admin.site.register(Question)
admin.site.register(Comment)
admin.site.register(Tag)
admin.site.register(Category)

def delete_reported_questions(modeladmin, request, queryset):
    for report in queryset:
        question = report.question
        question.delete()
    modeladmin.message_user(request, f"Deleted {queryset.count()} reported questions.")

delete_reported_questions.short_description = "Delete reported questions"

class ReportAdmin(admin.ModelAdmin):
    list_display = ['question_title', 'reason', 'reported_question_creation_date']
    actions = [delete_reported_questions]

    def question_title(self, obj):
        return obj.question.title

    question_title.short_description = 'Question Title'

    def reported_question_creation_date(self, obj):
        return obj.question.date_created

    reported_question_creation_date.short_description = 'Reported Question Creation Date'

admin.site.register(Report, ReportAdmin)


