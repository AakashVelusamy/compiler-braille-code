from django.urls import path
from . import views

urlpatterns = [
    path('translate/', views.translate, name='translate'),
    path('compile/', views.compile_and_run, name='compile'),
    path('ast/', views.get_ast, name='ast'),
    path('debug/', views.debug, name='debug'),
]
