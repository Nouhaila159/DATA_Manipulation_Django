import os
import uuid
import pandas as pd
import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.conf import settings
from home.models import FileInfo
from django.http import JsonResponse
from django.http import JsonResponse
from django.http import JsonResponse, HttpResponse
import matplotlib.pyplot as plt
from django.http import HttpResponseRedirect
from django.urls import reverse
from scipy.stats import norm, bernoulli, binom, uniform, poisson, expon
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from sklearn.preprocessing import LabelEncoder
import numpy as np
from django.views.decorators.csrf import csrf_exempt
import openpyxl
import seaborn as sns
from django.http import HttpResponseServerError
import io
import base64
import matplotlib
matplotlib.use('Agg')

# Create your views here.

def index(request):

    context = {}
    return render(request, 'pages/dashboard.html', context=context)

def convert_csv_to_text(csv_file_path):
    with open(csv_file_path, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)

    text = ''
    for row in rows:
        text += ','.join(row) + '\n'

    return text

def convert_excel_to_text(excel_file_path):
    try:
        workbook = openpyxl.load_workbook(excel_file_path)
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)
        text = ''
        for row in rows:
            text += ','.join(map(str, row)) + '\n'
        return text
    except openpyxl.utils.exceptions.InvalidFileException:
        return 'Le fichier n\'est pas un fichier Excel valide.'

def get_files_from_directory(directory_path):
    files = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            try:
                print( ' > file_path ' + file_path)
                _, extension = os.path.splitext(filename)
                if extension.lower() == '.csv':
                    csv_text = convert_csv_to_text(file_path)
                else:
                    csv_text = ''

                files.append({
                    'file': file_path.split(os.sep + 'media' + os.sep)[1],
                    'filename': filename,
                    'file_path': file_path,
                    'csv_text': csv_text
                })
            except Exception as e:
                print( ' > ' +  str( e ) )    
    return files

def save_info(request, file_path):
    path = file_path.replace('%slash%', '/')
    if request.method == 'POST':
        FileInfo.objects.update_or_create(
            path=path,
            defaults={
                'info': request.POST.get('info')
            }
        )
    
    return redirect(request.META.get('HTTP_REFERER'))

def get_breadcrumbs(request):
    path_components = [component for component in request.path.split("/") if component]
    breadcrumbs = []
    url = ''

    for component in path_components:
        url += f'/{component}'
        if component == "file-manager":
            component = "media"
        elif component == "link-manager":
            component = "media"
        elif component == "probability":
            component = "media"
        breadcrumbs.append({'name': component, 'url': url})

    return breadcrumbs


def file_manager(request, directory=''):
    media_path = os.path.join(settings.MEDIA_ROOT)
    directories = generate_nested_directory(media_path, media_path)
    selected_directory = directory

    files = []
    selected_directory_path = os.path.join(media_path, selected_directory)
    if os.path.isdir(selected_directory_path):
        files = get_files_from_directory(selected_directory_path)

    breadcrumbs = get_breadcrumbs(request)

    context = {
        'directories': directories, 
        'files': files, 
        'selected_directory': selected_directory,
        'segment': 'file_manager',
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'pages/file-manager.html', context)


def generate_nested_directory(root_path, current_path):
    directories = []
    for name in os.listdir(current_path):
        if os.path.isdir(os.path.join(current_path, name)):
            unique_id = str(uuid.uuid4())
            nested_path = os.path.join(current_path, name)
            nested_directories = generate_nested_directory(root_path, nested_path)
            directories.append({'id': unique_id, 'name': name, 'path': os.path.relpath(nested_path, root_path), 'directories': nested_directories})
    return directories


def delete_file(request, file_path):
    path = file_path.replace('%slash%', '/')
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
    os.remove(absolute_file_path)
    print("File deleted", absolute_file_path)
    return redirect(request.META.get('HTTP_REFERER'))

    
def download_file(request, file_path):
    path = file_path.replace('%slash%', '/')
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(absolute_file_path):
        with open(absolute_file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(absolute_file_path)
            return response
    raise Http404


def upload_file(request):
    media_path = os.path.join(settings.MEDIA_ROOT)
    selected_directory = request.POST.get('directory', '') 
    selected_directory_path = os.path.join(media_path, selected_directory)
    if request.method == 'POST':
        file = request.FILES.get('file')
        file_path = os.path.join(selected_directory_path, file.name)
        with open(file_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    return redirect(request.META.get('HTTP_REFERER'))


def traitement(request):
    file_path = request.GET.get('file_path', '')

    if file_path:
        # Construisez le chemin absolu du fichier
        media_path = os.path.join(settings.MEDIA_ROOT)
        absolute_file_path = os.path.join(media_path, file_path)

        # Lisez le contenu du fichier en tant que DataFrame
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(absolute_file_path)
            elif file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(absolute_file_path)
            elif file_path.endswith('.txt'):
                        df = pd.read_csv(absolute_file_path)
            else:
                return HttpResponse('Format de fichier non pris en charge.')
                
            columns_info = df.dtypes.reset_index()
            columns_info.columns = ['Colonne', 'Type de données']
        except pd.errors.ParserError:
            return HttpResponse('Le fichier ne peut pas être lu comme un fichier valide.')

        # Ajoutez ceci à votre vue Django
        context = {
            'file_path': absolute_file_path,
            'file_content': df.to_html(classes='table table-bordered table-striped text-center', index=False),
            'columns_info': columns_info.to_html(index=False),
            'columns': df.columns,  # Ajoutez toutes les colonnes sans valeur par défaut
        }
        return render(request, 'pages/traitement.html', context)
    else:
        return HttpResponse('Le chemin du fichier est manquant.')


def save_image(plt, settings, result, key_for_image, plot_type):
    image_filename = f'{plot_type}_{str(uuid.uuid4())}.png'  # Adjust the filename as needed
    result_directory = os.path.join(settings.MEDIA_ROOT, 'results')

    if not os.path.exists(result_directory):
        os.makedirs(result_directory)

    image_path = os.path.join(result_directory, image_filename)
    plt.savefig(image_path, format='png')
    result[key_for_image] = os.path.join('results', image_filename)

def process_treatment(request):
    print("Processing treatment...")
    x_column = request.GET.get('x_column')
    y_column = request.GET.get('y_column')
    column = request.GET.get('column')
    plot_type = request.GET.get('plot_type')
    file_path = request.GET.get('file_path')
    link_path = request.GET.get('link_path')
    result={}
    print(f"x_column: {x_column}, y_column: {y_column},column: {column}, plot_type: {plot_type}, file_path: {file_path},link_path: {link_path},")

    if file_path or link_path:
            try:
                # Utilisez link_path si file_path est None
                if file_path is None:
                    file_path = link_path

                # Construct the absolute file path
                media_path = os.path.join(settings.MEDIA_ROOT)
                absolute_file_path = os.path.join(media_path, file_path)

                if os.path.exists(absolute_file_path) or link_path:
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(absolute_file_path)
                    elif file_path.endswith('.txt'):
                        df = pd.read_csv(absolute_file_path)
                    elif file_path.endswith(('.xls', '.xlsx')):
                        df = pd.read_excel(absolute_file_path)
                    elif link_path:
                        df = pd.read_excel(link_path)
                    else:
                        return JsonResponse({'error_message': 'Unsupported file format'})

                    #line
                    if plot_type == 'line':
                        plt.figure(figsize=(10, 6))
                        sns.lineplot(x=x_column, y=y_column, data=df)
                        plt.xlabel(x_column)
                        plt.ylabel(y_column)
                        plt.title('Line Plot')
                        plt.legend()
                    #scatter
                    if plot_type == 'scatter':
                        plt.figure(figsize=(10, 6))
                        sns.scatterplot(x=x_column, y=y_column, data=df)
                        plt.xlabel(x_column)
                        plt.ylabel(y_column)
                        plt.title('Scatter Plot')
                        plt.legend()               
                    #box1
                    if plot_type == 'box1':
                        plt.figure(figsize=(10, 6))
                        sns.boxplot(x=column, data=df)
                        plt.xlabel(column)
                        plt.title('Box Plot')
                        plt.legend()  
                    #box2
                    if plot_type == 'box2':
                        plt.figure(figsize=(10, 6))
                        sns.boxplot(x=x_column, y=y_column, data=df)
                        plt.xlabel(x_column)
                        plt.ylabel(y_column)
                        plt.title('Box Plot')
                        plt.legend() 
                    #histogram
                    if plot_type == 'histogram':
                        plt.figure(figsize=(10, 6))
                        sns.histplot(x=column, data=df, kde=True)
                        plt.xlabel(column)
                        plt.title('Histograme')
                        plt.legend()
                    #kde
                    if plot_type == 'kde':
                        plt.figure(figsize=(10, 6))
                        sns.kdeplot(x=column, data=df,fill=True)
                        plt.xlabel(column)
                        plt.title('Kde Plot')
                        plt.legend()
                    #violin1
                    if plot_type == 'violin1':
                        plt.figure(figsize=(10, 6))
                        sns.violinplot(x=column, data=df)
                        plt.xlabel(column)
                        plt.title('Violin Plot')
                        plt.legend()
                    #violin2
                    if plot_type == 'violin2':
                        plt.figure(figsize=(10, 6))
                        sns.violinplot(x=x_column, y=y_column, data=df)
                        plt.xlabel(x_column)
                        plt.ylabel(y_column)
                        plt.title('Violin Plot')
                        plt.legend()
                    #bar
                    if plot_type == 'bar':
                        plt.figure(figsize=(10, 6))
                        sns.barplot(x=x_column, y=y_column, data=df)
                        plt.xlabel(x_column)
                        plt.ylabel(y_column)
                        plt.title('Bar Plot')
                        plt.legend()
                    #heatmap
                    if plot_type == 'heatmap':
                        numeric_df = df.select_dtypes(include=['number'])
                        correlation_matrix = numeric_df.corr()
                        plt.figure(figsize=(10, 6))
                        sns.heatmap(correlation_matrix, annot=True, cmap='YlGnBu', fmt=".2f")
                        plt.title('Correlation Matrix Heatmap')
                    #pie
                    if plot_type == 'pie':
                        pie_data = df[column].value_counts()
                        plt.figure(figsize=(8, 8))
                        plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=140)
                        plt.title('Pie Chart')

                    # Save the generated plot
                    save_image(plt, settings, result, 'image_url', plot_type)

                    plot_data = get_plot_data_as_json(plt)
                    plt.close()

                    return JsonResponse({'plot_data': plot_data})

            except pd.errors.ParserError as e:
                return JsonResponse({'error_message': f'Error reading file: {str(e)}'})

    return JsonResponse({'error_message': 'Invalid request'})

def get_plot_data_as_json(plt):
    # Save the plot to a BytesIO object
    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='png')
    plt.close()

    # Encode the image data as base64
    image_base64 = base64.b64encode(image_stream.getvalue()).decode('utf-8')

    return {'image_base64': image_base64}

def link_manager(request, directory=''):
    return render(request, 'pages/link-manager.html')


def traitement_link(request):
        # Obtenez l'URL à partir du formulaire
        file_link = request.GET.get('dataFrameLink', '')
        print(file_link)
        if file_link:
            try:
                df = pd.read_excel(file_link)
                columns_info = df.dtypes.reset_index()
                columns_info.columns = ['Colonne', 'Type de données']

                return JsonResponse({
                    'file_content': df.to_html(classes='table table-bordered table-striped text-center', index=False),
                    'columns_info': columns_info.to_html(index=False),
                    'columns': df.columns.tolist(), 
                })
            except pd.errors.ParserError:
                # Gérez les erreurs de parsing du DataFrame
                return HttpResponse('Les données ne peuvent pas être lues comme un DataFrame valide.')

def get_columns(request):
    data_frame_link = request.GET.get('data_frame_link')
    if data_frame_link:
            df = pd.read_excel(data_frame_link)
            columns_info = df.dtypes.reset_index()
            columns_info.columns = ['Colonne', 'Type de données']
            return JsonResponse({'columns': df.columns.tolist()})
   
def pandas(request):
        file_path = request.GET.get('file_path', '')
        link_path = request.GET.get('link_path')

        if file_path or link_path:
            try:
                # Utilisez link_path si file_path est None
                if file_path is None:
                    file_path = link_path

                # Construct the absolute file path
                media_path = os.path.join(settings.MEDIA_ROOT)
                absolute_file_path = os.path.join(media_path, file_path)

                if os.path.exists(absolute_file_path) or link_path:
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(absolute_file_path)
                    elif file_path.endswith(('.xls', '.xlsx')):
                        df = pd.read_excel(absolute_file_path)
                    elif file_path.endswith('.txt'):
                        df = pd.read_csv(absolute_file_path)
                    elif link_path:
                        df = pd.read_excel(link_path)
                    else:
                        return JsonResponse({'error_message': 'Unsupported file format'})

                    columns_info = df.dtypes.reset_index()
                    columns_info.columns = ['Colonne', 'Type de données']

            except pd.errors.ParserError:
                return HttpResponse('Le fichier ne peut pas être lu comme un CSV ou EXCEL valide.')

            # Add all rows and columns to the context
            rows = df.index.tolist()
            columns = df.columns.tolist()

            # Add this to your Django view
            context = {
                'link_path':link_path,
                'file_path': absolute_file_path,
                'file_content': df.to_html(classes='table table-bordered table-striped text-center', index=False),
                'columns_info': columns_info.to_html(index=False),
                'rows': rows,
                'columns': columns,
                'df_data': df.to_dict(orient='split'),  # Add DataFrame data to the context
            }

            return render(request, 'pages/pandas.html', context)
        else:
            return HttpResponse('Le chemin du fichier est manquant.')

def get_selectedValue(request):
        # Handle the POST request for processing selected rows and columns
        file_path = request.GET.get('file_path', '')
        selected_rows = request.GET.getlist('selected_rows[]')
        selected_columns = request.GET.getlist('selected_columns[]')
        print(f"Received file_path: {file_path}, selected_rows: {selected_rows}, selected_columns: {selected_columns}")

        link_path = request.GET.get('link_path')

        if file_path or link_path:
            try:
                # Utilisez link_path si file_path est None
                if file_path is None:
                    file_path = link_path

                # Construct the absolute file path
                media_path = os.path.join(settings.MEDIA_ROOT)
                absolute_file_path = os.path.join(media_path, file_path)

                if os.path.exists(absolute_file_path) or link_path:
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(absolute_file_path)
                    elif file_path.endswith(('.xls', '.xlsx')):
                        df = pd.read_excel(absolute_file_path)
                    elif file_path.endswith('.txt'):
                        df = pd.read_csv(absolute_file_path)
                    elif link_path:
                        df = pd.read_excel(link_path)
                    else:
                        return JsonResponse({'error_message': 'Unsupported file format'})

                    # Process the selected rows and columns
                    if selected_rows and selected_columns:
                        df = df.loc[df.index.isin(map(int, selected_rows)), selected_columns]

                    elif selected_rows:
                        df = df.loc[df.index.isin(map(int, selected_rows))]  # Convert selected_rows to integers

                    elif selected_columns:
                        df = df[selected_columns]
                    

                    # Prepare the updated context
                    updated_context = {
                        'file_content': df.to_html(classes='table table-bordered table-striped text-center', index=False),
                    }

                    return JsonResponse(updated_context)
            except pd.errors.ParserError:
                return HttpResponse('Le fichier ne peut pas être lu comme un CSV ou EXCEL valide.')


        return HttpResponse('Invalid request method.')
            
def probability(request):
    # Assuming 'probability.html' is located in the 'templates' directory
    return render(request, 'pages/probability.html')

# views.py


@csrf_exempt
def generate_pdf_plot(request):
    try:
        mu = float(request.GET.get('mu', 0.0))
        sigma = float(request.GET.get('sigma', 1.0))
        lower_bound = float(request.GET.get('lowerBound', -5.0))
        upper_bound = float(request.GET.get('upperBound', 5.0))

        x = np.linspace(lower_bound, upper_bound, 1000)
        pdf = norm.pdf(x, loc=mu, scale=sigma)
        prob = norm.cdf(upper_bound, loc=mu, scale=sigma) - norm.cdf(lower_bound, loc=mu, scale=sigma)

        plt.plot(x, pdf, c='r', ls='-', lw=2, label='DDP')
        plt.fill_between(x, pdf, where=(x >= lower_bound) & (x <= upper_bound), alpha=0.2,
                         color='blue', label=f'Probability: {prob:.4f}')
        plt.legend()
        plt.grid()

        result = {}
        # Save the generated plot
        save_image(plt, settings, result, 'image_url', 'plot')

        plot_data = get_plot_data_as_json(plt)
        plt.close()

        return JsonResponse({'plot_data': plot_data})
    except Exception as e:
        return JsonResponse({'error_message': f'Error generating plot: {str(e)}'})

def generate_bernoulli_plot(request):
    try:
        probability = float(request.GET.get('probability', 0.5))

        data_bernoulli = bernoulli.rvs(size=1000, p=probability)
        
        plt.figure(figsize=(6, 4))
        ax = sns.histplot(data_bernoulli, kde=True, stat='probability')
        ax.set(xlabel='Bernoulli', ylabel='Probability')

        result = {}
        # Sauvegarder le graphique généré
        save_image(plt, settings, result, 'image_url', 'plot')

        plot_data = get_plot_data_as_json(plt)
        plt.close()
        return JsonResponse({'plot_data': plot_data})

    except Exception as e:
        return JsonResponse({'error_message': f'Error generating Bernoulli plot: {str(e)}'})

def generate_binomial_plot(request):
    try:
        n = int(request.GET.get('n', 10))  # Le nombre d'essais
        p = float(request.GET.get('p', 0.5))  # La probabilité de succès
        plt.figure(figsize=(6,4))

        data_binomial = binom.rvs(n=n,p=p,loc=0,size=1000)
        ax = sns.histplot(data_binomial, kde=True, stat='probability')
        ax.set(xlabel='Binomial', ylabel='Probabilité')

        result = {}
        save_image(plt, settings, result, 'image_url', 'plot')

        plot_data = get_plot_data_as_json(plt)
        plt.close()

        return JsonResponse({'plot_data': plot_data})
    except Exception as e:
        return JsonResponse({'error_message': f'Error generating binomial plot: {str(e)}'})

def generate_uniform_plot(request):
    try:
        loc = float(request.GET.get('loc', 1))
        scale = float(request.GET.get('scale', 5))

        data_uniform = uniform.rvs(loc=loc, scale=scale, size=1000)
        plt.figure(figsize=(6, 4))
        ax = sns.histplot(data_uniform, kde=True, stat='probability')
        ax.set(xlabel='Uniforme', ylabel='Probability');

        result = {}
        # Sauvegarder le graphique généré
        save_image(plt, settings, result, 'image_url', 'plot')

        plot_data = get_plot_data_as_json(plt)
        plt.close()

        return JsonResponse({'plot_data': plot_data})
   
    except Exception as e:
        return JsonResponse({'error_message': f'Error generating Uniform plot: {str(e)}'})

def generate_poisson_plot(request):
    try:
        mu = float(request.GET.get('mu', 4))

        data_poisson = poisson.rvs(mu=mu, size=1000)

        plt.figure(figsize=(6, 4))
        ax = sns.histplot(data_poisson, kde=True, stat='probability')
        ax.set(xlabel='Poisson', ylabel='Probability')

        result = {}
        # Sauvegarder le graphique généré
        save_image(plt, settings, result, 'image_url', 'plot')

        plot_data = get_plot_data_as_json(plt)
        plt.close()

        return JsonResponse({'plot_data': plot_data})
    except Exception as e:
        return JsonResponse({'error_message': f'Error generating Poisson plot: {str(e)}'})

def generate_normal_plot(request):
    try:
        mean = float(request.GET.get('mean', 0))
        std_dev = float(request.GET.get('std_dev', 1))

   
        data_normal = norm.rvs(loc=mean, scale=std_dev, size=1000)
        # sns.histplot(data, kde=True);
        sns.kdeplot(data_normal, fill=True)

        result = {}
        # Sauvegarder le graphique généré
        save_image(plt, settings, result, 'image_url', 'plot')

        plot_data = get_plot_data_as_json(plt)
        plt.close()

        return JsonResponse({'plot_data': plot_data})

    except Exception as e:
        return JsonResponse({'error_message': f'Error generating Normal plot: {str(e)}'})

def generate_exponential_plot(request):
    try:
        rate = float(request.GET.get('rate', 1))

        data_exponential = expon.rvs(scale=1/rate, size=1000)

        plt.figure(figsize=(6, 4))
        ax = sns.histplot(data_exponential, kde=True, stat='probability')
        ax.set(xlabel='Exponential', ylabel='Probability')

        result = {}
        # Save the generated plot
        save_image(plt, settings, result, 'image_url', 'plot')

        plot_data = get_plot_data_as_json(plt)
        plt.close()

        return JsonResponse({'plot_data': plot_data})

    except Exception as e:
        return JsonResponse({'error_message': f'Error generating Exponential plot: {str(e)}'})