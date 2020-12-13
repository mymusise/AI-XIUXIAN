from django.urls import path
from model import views


urlpatterns = [
    path('start/', views.TextGeneratorView.as_view({'get': 'get_start_text'})),
    path('gen/', views.TextGeneratorView.as_view({'post': 'gen_next'})),
]
