import time
from .models import CSVResult
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task


@shared_task
def send_processing_result(email, result_id):
    subject = 'Your CSV Processing Result'
    message = f'Your CSV file has been processed. Result ID: {result_id}'
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])


@shared_task
def process_csv(email, csv_data):
    time.sleep(60)
    processed_data = f"Processed data: {csv_data}"
    result = CSVResult.objects.create(email=email, processed_data=processed_data)
    return result.id