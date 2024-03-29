from django.db import models
from django.contrib.auth.models import User
class Chat(models.Model):
    message = models.TextField()
    response = models.TextField()

    def __str__(self):
        return f"Message: {self.message}, Response: {self.response}"

class Response(models.Model):
    response = models.TextField()

    def __str__(self):
        return self.response
    
class AssessmentQuestion(models.Model):
    question = models.TextField()
    options = models.JSONField()
    answer = models.CharField(max_length=255)

    def __str__(self):
        return self.question
    

class AssessmentHistory(models.Model):
    assessment_id = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    result_details = models.JSONField()

    def __str__(self):
        return f"Assessment History ID: {self.assessment_id} - User: {self.user.username}"
