# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('folium_map/', views.folium_map, name='folium_map'),
    path('csv_data/', views.csv_data, name='csv_data'),
    path('display_images/', views.display_images, name='display_images'),
    path('download_csv/', views.download_csv, name='download_csv'),
    path('stream_process/<str:file_name>/', views.stream_process, name='stream_process'),
]
