from django.contrib import admin
from .models import Chat, Response, AssessmentQuestion,AssessmentHistory

admin.site.register(Chat)
admin.site.register(Response)
admin.site.register(AssessmentQuestion)
admin.site.register(AssessmentHistory)