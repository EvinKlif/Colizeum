from django.db import models

class CSVResult(models.Model):
    email = models.EmailField()
    processed_data = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for {self.email} at {self.created_at}"