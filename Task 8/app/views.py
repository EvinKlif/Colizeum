from django.shortcuts import render, redirect
from .tasks import process_csv, send_processing_result


def upload_csv(request):
    if request.method == 'POST':
        if 'csv_file' in request.FILES and 'email' in request.POST:
            csv_file = request.FILES['csv_file']
            email = request.POST['email']  # Получаем email из формы
            csv_data = csv_file.read().decode('utf-8')
            task = process_csv.delay(email, csv_data)
            send_processing_result.delay(email, task.get())
            return redirect('success')
        else:
            return render(request, 'upload_csv.html', {'error': 'Please provide both email and CSV file.'})
    return render(request, 'upload_csv.html')

def success(request):
    return render(request, 'success.html')