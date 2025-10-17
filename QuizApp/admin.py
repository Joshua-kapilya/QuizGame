from django.contrib import admin
from django.utils.html import format_html
from .models import Subject, SubjectPlay, PastPaper, Question, Tournament_subject, Tournament_question, Tournament, Score, UserProfile

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'past_paper', 'question_type', 'text', 'image_preview', 'correct_answers_display')
    list_filter = ('subject', 'past_paper', 'question_type')
    search_fields = ('text', 'correct_answer')

    def correct_answers_display(self, obj):
        return obj.correct_answer if obj.correct_answer else "No Correct Answer"
    correct_answers_display.short_description = "Correct Answer"

    # Allow inline image preview
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.diagram:
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 5px;"/>', obj.diagram.url)
        return "No Image"

    image_preview.short_description = "Preview"

admin.site.register(Subject)
admin.site.register(PastPaper)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Tournament_subject)
admin.site.register(Tournament_question)
admin.site.register(Tournament)
admin.site.register(Score)
admin.site.register(UserProfile)
admin.site.register(SubjectPlay)

