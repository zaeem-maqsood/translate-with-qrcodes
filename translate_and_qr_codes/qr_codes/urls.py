from django.urls import path

from . import views

app_name = "qr_codes"
urlpatterns = [
    path("", views.hello_world, name="home"),
    path("read/<uuid:pk>/", views.read_qr_code_contents, name="read"),
]
