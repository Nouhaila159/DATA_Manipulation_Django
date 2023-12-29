from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('file-manager/', views.file_manager, name='file_manager'),
    re_path(r'^file-manager/(?P<directory>.*)?/$', views.file_manager, name='file_manager'),
    path('delete-file/<str:file_path>/', views.delete_file, name='delete_file'),
    path('download-file/<str:file_path>/', views.download_file, name='download_file'),
    path('upload-file/', views.upload_file, name='upload_file'),
    path('save-info/<str:file_path>/', views.save_info, name='save_info'),
    path('traitement/', views.traitement, name='traitement'),

    path('process_treatment/', views.process_treatment, name='process_treatment'),
    #path('traitement/<str:image_filename>/', views.traitement_image, name='traitement'),
    
    path('link-manager/', views.link_manager, name='link_manager'),
    path('traitement_link/', views.traitement_link, name='traitement_link'),
    path('get_columns/', views.get_columns, name='get_columns'),

    #Pandas
    path('pandas/', views.pandas, name='pandas'),
    path('get_selectedValue/', views.get_selectedValue, name='get_selectedValue'),
    path('process_operation/', views.process_operation, name='process_operation'),
    path('manipulate_dataframe/', views.manipulate_dataframe, name='manipulate_dataframe'),

    #Lois
    path('probability/', views.probability, name='probability'),
    path('generate_pdf_plot/', views.generate_pdf_plot, name='generate_pdf_plot'),
    path('generate_bernoulli_plot/', views.generate_bernoulli_plot, name='generate_bernoulli_plot'),
    path('generate_binomial_plot/', views.generate_binomial_plot, name='generate_binomial_plot'),
    path('generate_uniform_plot/', views.generate_uniform_plot, name='generate_uniform_plot'),
    path('generate_poisson_plot/', views.generate_poisson_plot, name='generate_poisson_plot'),
    path('generate_normal_plot/', views.generate_normal_plot, name='generate_normal_plot'),
    path('generate_exponential_plot/', views.generate_exponential_plot, name='generate_exponential_plot'),

    #mesures
    path('mesures/', views.mesures, name='mesures'),

    #dash
    path('/', views.dashboard, name='dashboard'),

    #Tests
    path('tests/', views.tests, name='tests'),
    path('test_traitement/', views.test_traitement, name='test_traitement'),

]
