from django.urls import path
from . import views

urlpatterns = [
    path('',views.upload_and_analyze, name = 'upload and analyze' ),
]