# main/views.py
from django.shortcuts import render
from django.http import HttpResponse
import os
import base64
from django.conf import settings
from .main import main_process
from django.http import StreamingHttpResponse
from .predict_process import predict_process

def index(request):
    return render(request, 'main/index.html')

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        file_name = file.name
        with open(f"data_input/{file_name}", "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        # You can call your `main_process` function here if needed
        main_process(file_name)
        return HttpResponse("Finish! Clik on menu for detail") 
    return render(request, 'main/upload.html')

def stream_process(request, file_name):
    def generate():
        def callback(message):
            yield f"{message}<br>"  # Mengirimkan pesan dengan format HTML
        main_process(file_name, callback)
    
    return StreamingHttpResponse(generate(), content_type='text/html')

def download_csv(request):
    file_path = os.path.join('data_input', 'DataFinal.csv')  # Sesuaikan dengan jalur Anda
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="DataFinal.csv"'
            return response
    else:
        return HttpResponse("File not found.", status=404)

def folium_map(request):
    folium_file_path = os.path.join(settings.DATA_INPUT_DIR, 'folium_map.html')
    with open(folium_file_path, 'r') as file:
        html_content = file.read()
    return render(request, 'data_input/folium_map.html', {'html_content': html_content})

def csv_data(request):
    file_path = os.path.join(settings.DATA_INPUT_DIR, 'DataFinal.csv')
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            csv_content = f.read()
        # Convert CSV to HTML table
        html_content = "<table border='1'>"
        for row in csv_content.split("\n"):
            html_content += "<tr>"
            for cell in row.split(","):
                html_content += f"<td>{cell}</td>"
            html_content += "</tr>"
        html_content += "</table>"
        return HttpResponse(html_content)
    return HttpResponse("CSV file not found.")

def display_images(request):
    image_paths = ["data_input/satellite_images.png", "data_input/posisi_cb.png"]
    html_content = "<div>"
    for image_path in image_paths:
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
                css = "<style>img { max-width: 100%; height: auto; }</style>"
                html_content += f"{css}<img src='data:image/jpeg;base64,{image_data}'/>"
    html_content += "</div>"
    return HttpResponse(html_content)
