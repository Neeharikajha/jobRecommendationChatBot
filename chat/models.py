from django.db import models

# Create your models here.
class Resume(models.Model):
    session_key = models.CharField(max_length=64, unique=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add = True)

class Application(models.Model):
    session_key = models.CharField(max_length=64, db_index= True)
    job_id = models.IntegerField()
    job_title = models.CharField(max_length=300)
    company = models.CharField(max_length=300)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default="Applied")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["session_key", "job_id"], name="uniq_application")]

class Message(models.Model):
    session_key = models.CharField(max_length=64, db_index=True)
    role = models.CharField(max_length=10)
    content = models.TextField()
    created_at= models.DateTimeField(auto_now_add= True)