from django.urls import path

from apps.inference.views import InferView

app_name = 'inference'

urlpatterns = [
    path('infer/', InferView.as_view(), name='infer'),
]
