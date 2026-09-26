from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("analyze/", views.analyze, name="analyze"),
    path("report/<int:report_id>/", views.report_detail, name="report_detail"),
]
