import os
import uuid
import pandas as pd
import csv
import re
import plotly.express as px
import plotly.figure_factory as ff
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
import plotly.graph_objects as go
from statistics import mode
from django.http import HttpResponseServerError
import io
import base64
import matplotlib
import plotly.graph_objs as go
from sklearn.linear_model import LinearRegression
import plotly.io as pio
from scipy.stats import t
from scipy import stats
from sklearn.linear_model import LinearRegression
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

def save_image(fig, settings, result, key_for_image, plot_type):
    image_filename = f'{plot_type}_{str(uuid.uuid4())}.png'
    result_directory = os.path.join(settings.MEDIA_ROOT, 'results')

    if not os.path.exists(result_directory):
        os.makedirs(result_directory)

    image_path = os.path.join(result_directory, image_filename)
    pio.write_image(fig, image_path)

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
                    
                    # Line Plot
                    if plot_type == 'line':
                        if not pd.api.types.is_numeric_dtype(df[y_column]):
                            raise ValueError(f"La colonne {y_column} doit contenir uniquement des nombres numériques.")

                        fig = px.line(df, x=x_column, y=y_column, title='Line Plot')

                    # Scatter Plot
                    elif plot_type == 'scatter':
                        if not pd.api.types.is_numeric_dtype(df[x_column]) or not pd.api.types.is_numeric_dtype(df[y_column]):
                            raise ValueError(f"La colonne {x_column} et colonne {y_column} doivent être de type numérique.")

                        fig = px.scatter(df, x=x_column, y=y_column, title='Scatter Plot')

                    # Box Plot 1
                    elif plot_type == 'box1':
                        if not pd.api.types.is_numeric_dtype(df[column]):
                            raise ValueError(f"La colonne {column} doit contenir uniquement des nombres.")

                        fig = px.box(df, y=column, title='Box Plot')

                    # Box Plot 2
                    elif plot_type == 'box2':
                        if not pd.api.types.is_numeric_dtype(df[y_column]):
                            raise ValueError(f"La colonne {y_column} doit contenir uniquement des nombres numériques.")

                        fig = px.box(df, x=x_column, y=y_column, title='Box Plot')

                    # Histogram
                    elif plot_type == 'histogram':
                        fig = px.histogram(df, x=column, title='Histogram Plot')

                    # KDE (Kernel Density Estimation) Plot
                     
                    elif plot_type == 'kde':
                        if not pd.api.types.is_numeric_dtype(df[column]):
                            raise ValueError(f"La colonne {column} doit contenir uniquement des nombres.")

                        data_to_plot = df[column].replace([np.inf, -np.inf], np.nan).dropna()

                        group_labels = ['distplot']
                        fig = ff.create_distplot([data_to_plot], group_labels, curve_type='kde')

                        # Mise à jour de la disposition (layout)
                        fig.update_layout(
                            title="Kernel Density Estimation (KDE) Plot",
                            yaxis_title="Density",
                            xaxis_title=column,
                            showlegend=False
                        )

                    # Violin Plot 1
                    elif plot_type == 'violin1':
                        if not pd.api.types.is_numeric_dtype(df[column]):
                            raise ValueError(f"La colonne {column} doit contenir uniquement des nombres pour le Violin Plot.")

                        fig = px.violin(df, x=column, box=True, points="all", title='Violin Plot')

                    # Violin Plot 2
                    elif plot_type == 'violin2':
                        if not pd.api.types.is_numeric_dtype(df[x_column]) or not pd.api.types.is_numeric_dtype(df[y_column]):
                            raise ValueError(f"La colonne {x_column} et colonne {y_column} doivent être de type numérique.")

                        fig = px.violin(df, x=x_column, y=y_column, box=True, points="all", title='Violin Plot')

                    # Bar Plot
                    elif plot_type == 'bar':
                        if not pd.api.types.is_numeric_dtype(df[y_column]):
                            raise ValueError(f"La colonne {y_column} doit contenir uniquement des nombres numériques.")

                        fig = px.bar(df, x=x_column, y=y_column, title='Bar Plot')

                    # Heatmap
                    elif plot_type == 'heatmap':
                        numeric_df = df.select_dtypes(include=['number'])

                        if numeric_df.empty:
                            raise ValueError("Les données pour le heatmap doivent contenir au moins une colonne numérique.")

                        correlation_matrix = numeric_df.corr()

                        # Create a heatmap using go.Heatmap
                        heatmap = go.Heatmap(
                            z=correlation_matrix.values,
                            x=correlation_matrix.columns,
                            y=correlation_matrix.index,
                            colorscale='Blues',
                            colorbar=dict(title='Correlation')
                        )

                        # Create a layout for the heatmap
                        layout = go.Layout(
                            title='Correlation Matrix Heatmap',
                            xaxis=dict(title='Columns'),
                            yaxis=dict(title='Columns')
                        )

                        # Create a figure and update layout
                        fig = go.Figure(data=[heatmap], layout=layout)

                    # Pie Chart
                    elif plot_type == 'pie':
                        fig = px.pie(df, names=column, title='Pie Chart')

                    # Save the generated plot
                    save_image(fig, settings, result, 'image_url', plot_type)

                    # Convert the Plotly figure to JSON
                    plot_data = fig.to_json()

                    return JsonResponse({'plot_data': plot_data})

            except pd.errors.ParserError as e:
                return JsonResponse({'error_message': f'Error reading file: {str(e)}'})
            except FileNotFoundError as e:
                return JsonResponse({'error_message': f'File not found: {str(e)}'})

            except ValueError as e:
                return JsonResponse({'error_message': f'Invalid input values: {str(e)}'})

            except pd.errors.ParserError as e:
                return JsonResponse({'error_message': f'Error reading file: {str(e)}'})

            except Exception as e:
                return JsonResponse({'error_message': f'Unexpected error: {str(e)}'})

    return JsonResponse({'error_message': 'Invalid request'})

def link_manager(request, directory=''):
    segment = 'link_manager'
    return render(request, 'pages/link-manager.html', {'segment': segment})

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

    return JsonResponse({})

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

def apply_pandas_operation(df, selected_rows, selected_columns, selected_operation):
    # Validate if there is a valid DataFrame and selected operation
    if df is None or selected_operation not in ['mean', 'mode', 'median', 'variance', 'std_deviation', 'min_value', 'max_value', 'range', 'sum']:
        return None
    # Handle the case when a row is selected
    if selected_rows and any(selected_rows):
        # Check if the selected rows exist in the DataFrame
        valid_rows = [row for row in selected_rows if row in df.index]
        if valid_rows:
            selected_data = df.loc[valid_rows]
        else:
            return None
    # Handle the case when a column is selected
    elif selected_columns and any(selected_columns):
        # Check if the selected columns exist in the DataFrame
        valid_columns = [col for col in selected_columns if col in df.columns]
        if valid_columns:
            selected_data = df[valid_columns]
        else:
            return None
    else:
        return None

    # Apply the selected operation
    if selected_operation == 'mean':
        result_data = selected_data.mean()
    elif selected_operation == 'mode':
        result_data = selected_data.mode()
    elif selected_operation == 'median':
        result_data = selected_data.median()
    elif selected_operation == 'variance':
        result_data = selected_data.var()
    elif selected_operation == 'std_deviation':
        result_data = selected_data.std()
    elif selected_operation == 'min_value':
        result_data = selected_data.min()
    elif selected_operation == 'max_value':
        result_data = selected_data.max()
    elif selected_operation == 'range':
        result_data = selected_data.max() - selected_data.min()
    elif selected_operation == 'sum':
        result_data = selected_data.sum()

    # Convert the result to JSON
    numeric_value = float(result_data.iloc[0]) if not result_data.empty else None
    return numeric_value

def process_operation(request):
    # Handle the POST request for processing selected rows and columns
    file_path = request.GET.get('file_path', '')
    selected_rows = request.GET.getlist('selected_rows[]')
    selected_columns = request.GET.getlist('selected_columns[]')
    selected_operation = request.GET.get('selected_operation')

    print(f"Received file_path: {file_path}, selected_rows: {selected_rows}, selected_columns: {selected_columns}")

    link_path = request.GET.get('link_path')

    # Check if the file path is provided
    if file_path or link_path:
        try:
            # Use link_path if file_path is None
            if not file_path:
                file_path = link_path

            # Construct the absolute file path
            media_path = os.path.join(settings.MEDIA_ROOT)
            absolute_file_path = os.path.join(media_path, file_path)

            # Check if the file exists
            if os.path.exists(absolute_file_path) or link_path:
                # Read the DataFrame from the file
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

                # Apply the Pandas operation
                result_data = apply_pandas_operation(df, selected_rows, selected_columns, selected_operation)

                # Check if the result is not None before returning JsonResponse
                if result_data is not None:
                    return JsonResponse({'result_data': result_data})
                else:
                    return JsonResponse({'error_message': 'Invalid operation or no data selected'})
        except pd.errors.ParserError:
            return JsonResponse({'error_message': 'The file cannot be read as a valid CSV or Excel file.'})

    return JsonResponse({'error_message': 'The file path is missing.'})

def manipulate_dataframe(request):
    if request.method == 'POST':
        file_path = request.POST.get('file_path', '')
        link_path = request.POST.get('link_path', '')
        manipulation_type = request.POST.get('manipulation_type', '')
        filter_expression = request.POST.get('filter_expression', '')
        group_by_expression=request.POST.get('group_by_expression', '')

        try:
            # Utiliser link_path si file_path est None
            if not file_path:
                file_path = link_path

            # Construire le chemin de fichier absolu
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
                    return JsonResponse({'error_message': 'Format de fichier non pris en charge'})

                # Créer une copie du DataFrame pour laisser l'original intact
                df_copy = df.copy()

                # Appliquer le filtrage si le type de manipulation est "filter"
                if manipulation_type == 'filter' and filter_expression:
                    try:
                        # Convertir les noms de colonnes et l'expression de filtre en minuscules
                        df_copy.columns = map(str.lower, df_copy.columns)
                        filter_expression = filter_expression.lower()
                        
                        # Appliquer l'expression de filtre
                        df_copy = df_copy.query(filter_expression)
                    except pd.errors.ParserError:
                        return JsonResponse({'error_message': 'Expression de filtre invalide'})

                # Supprimer les valeurs nulles si le type de manipulation est "removeNull"
                elif manipulation_type == 'removeNull':
                    df_copy = df_copy.dropna()
                    
                elif manipulation_type == 'groupBy' and group_by_expression:
                    try:
                        # Convertir les noms de colonnes en minuscules
                        df_copy.columns = map(str.lower, df_copy.columns)
                        group_by_expression = group_by_expression.lower()

                        # Compter le nombre d'occurrences de la valeur dans toute la DataFrame
                        occurrences_count = int(df_copy.applymap(lambda x: group_by_expression in str(x).lower()).sum().sum())

                        return JsonResponse({'group_by_expression': group_by_expression, 'occurrences_count': occurrences_count})
                    except pd.errors.ParserError:
                        return JsonResponse({'error_message': 'Expression "Group By" invalide'})



                return JsonResponse({'file_content': df_copy.to_html(classes='table table-bordered table-striped text-center', index=False)})

        except pd.errors.ParserError:
            return JsonResponse({'error_message': "Le fichier ne peut pas être lu comme un fichier CSV ou Excel valide."})

    return JsonResponse({'error_message': 'Méthode de requête non valide'})

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
    segment = 'probability'
    # Assuming 'probability.html' is located in the 'templates' directory
    return render(request, 'pages/probability.html', {'segment': segment})

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
        save_image2(plt, settings, result, 'image_url', 'plot')

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
        save_image2(plt, settings, result, 'image_url', 'plot')

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
        save_image2(plt, settings, result, 'image_url', 'plot')

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
        save_image2(plt, settings, result, 'image_url', 'plot')

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
        save_image2(plt, settings, result, 'image_url', 'plot')

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
        save_image2(plt, settings, result, 'image_url', 'plot')

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
        save_image2(plt, settings, result, 'image_url', 'plot')

        plot_data = get_plot_data_as_json(plt)
        plt.close()

        return JsonResponse({'plot_data': plot_data})

    except Exception as e:
        return JsonResponse({'error_message': f'Error generating Exponential plot: {str(e)}'})
        
def get_plot_data_as_json(plt):
    # Save the plot to a BytesIO object
    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='png')
    plt.close()

    # Encode the image data as base64
    image_base64 = base64.b64encode(image_stream.getvalue()).decode('utf-8')

    return {'image_base64': image_base64}

def save_image2(plt, settings, result, key_for_image, plot_type):
    image_filename = f'{plot_type}_{str(uuid.uuid4())}.png'  # Adjust the filename as needed
    result_directory = os.path.join(settings.MEDIA_ROOT, 'results')

    if not os.path.exists(result_directory):
        os.makedirs(result_directory)

    image_path = os.path.join(result_directory, image_filename)
    plt.savefig(image_path, format='png')
    result[key_for_image] = os.path.join('results', image_filename)

def mode(valeurs):
    uniques, counts = np.unique(valeurs, return_counts=True)
    max_count = np.max(counts)
    modes = uniques[counts == max_count]
    if max_count == 1:
        return "Il n'y a pas de mode"
    else:
        return modes.tolist()

def mesures(request):
    segment = 'mesures'
    error_message = None
    initial_values = None
    
    if request.method == 'POST':
        valeurs_input = request.POST.get('valeurs', '')
        initial_values = valeurs_input

        try:
            # Replace commas with dots for decimal points
            valeurs_input = valeurs_input.replace(',', '.')

            # Traiter les valeurs saisies avec n'importe quel séparateur
            separators = ['/', '_', ';', ':', ' ', '\s+']
            separator_pattern = '|'.join(map(re.escape, separators))
            
            # Split the values
            split_values = re.split(separator_pattern, valeurs_input)

            # Process the values (integers or floats)
            valeurs = [float(x.replace(',', '.')) if '.' in x or ',' in x else int(x) for x in split_values if x]
           
            # Calcul des statistiques
            mean_value = np.mean(valeurs)
            median_value = np.median(valeurs)
            mode_value = mode(valeurs)
            variance_value = np.var(valeurs, ddof=1)
            #variance_value = np.var(valeurs)
            stdev_value = np.std(valeurs)
            etendue_value = np.ptp(valeurs)  # Peak-to-peak, which is the range

            return render(request, 'pages/calculs.html', {'mean': mean_value,
                                                     'median': median_value, 'mode': mode_value,
                                                     'variance': variance_value, 'stdev': stdev_value,
                                                     'etendue': etendue_value,
                                                     'segment': segment, 'initial_values': initial_values})
        except ValueError as e:
            # Handle the ValueError and set the error_message
            error_message = "Erreur: Veuillez saisir des valeurs numériques valides."

    # In case of 'GET' request, still pass initial_values to the template
    return render(request, 'pages/calculs.html', {'segment': segment, 'error_message': error_message, 'initial_values': initial_values})

def tests(request, directory=''):
    segment = 'tests'
    return render(request, 'pages/tests.html', {'segment': segment})

def calculate_z_test(field, sigma, n, significance):
    # Convertir les valeurs en nombres
    field = float(field)
    sigma = float(sigma)
    n = int(n)
    significance = float(significance)

    # Calculer le z-test
    z_stat = norm.sf(abs((field - 0) / (sigma / np.sqrt(n)))) * 2  # Two-tailed test

    # Interpréter les résultats du test
    if z_stat < significance:
        hypothesis_result = "Hypothesis rejected: The sample mean is significantly different from the population mean."
    else:
        hypothesis_result = "Hypothesis not rejected : There is no significant difference between the sample mean and the population mean."

    return z_stat, hypothesis_result

def calculate_z_test(field,zTestmi,sigma, n, significance):
    # Convertir les valeurs en nombres
    field = float(field)
    sigma = float(sigma)
    n = int(n)
    significance = float(significance)
    zTestmi = float(zTestmi.replace(',', '.'))
    # Calculer le z-test
    z_stat = (field - zTestmi) / (sigma / np.sqrt(n))

    # Calculer les p-values pour les trois cas
    p_value_two_sided = norm.sf(abs(z_stat)) * 2  # Bilatéral
    p_value_left = norm.cdf(z_stat)  # Unilatéral à gauche
    p_value_right = norm.sf(z_stat)  # Unilatéral à droite

    # Interpréter les résultats du test
    hypothesis_result_two_sided = "Hypothesis rejected: The sample mean is significantly different from the population mean." if p_value_two_sided < significance else "Hypothesis not rejected: There is no significant difference between the sample mean and the population mean."

    hypothesis_result_left = "Hypothesis rejected: The sample mean is significantly less than the population mean." if p_value_left < significance else "Hypothesis not rejected: There is no significant difference, or the sample mean is greater than the population mean."

    hypothesis_result_right = "Hypothesis rejected: The sample mean is significantly greater than the population mean." if p_value_right < significance else "Hypothesis not rejected: There is no significant difference, or the sample mean is less than the population mean."

    # Retourner les résultats du test sous forme de dictionnaire
    return {
        'z_statistic': z_stat,
        'p_value_two_sided': p_value_two_sided,
        'p_value_left': p_value_left,
        'p_value_right': p_value_right,
        'hypothesis_result_two_sided': hypothesis_result_two_sided,
        'hypothesis_result_left': hypothesis_result_left,
        'hypothesis_result_right': hypothesis_result_right
    }

def calculate_linear_regression(x_values, y_values):
    # Convert x_values and y_values to numpy arrays
    x_values = np.array(x_values)
    y_values = np.array(y_values)

    # Use numpy's polyfit to perform linear regression and get the slope and intercept
    slope, intercept = np.polyfit(x_values, y_values, 1)

    # Retourner uniquement la pente et l'ordonnée à l'origine
    return slope, intercept

def calculate_t_test(field1, field2, s1, s2, n1, n2, significance):
    # Convertir les valeurs en nombres
    field1 = float(field1)
    field2 = float(field2)
    s1 = float(s1)
    s2 = float(s2)
    n1 = int(n1)
    n2 = int(n2)

    # Calculer la statistique t
    t_stat, p_value = stats.ttest_ind_from_stats(mean1=field1, std1=s1, nobs1=n1, mean2=field2, std2=s2, nobs2=n2)

    # Tester l'hypothèse nulle
    if p_value < significance:
        hypothesis_result = "Reject the null hypothesis"
    else:
        hypothesis_result = "Fail to reject the null hypothesis"

    return t_stat, p_value, hypothesis_result

def calculate_t_test2(field, tTestmi, sigma, n, significance):
    # Convertir les valeurs en nombres
    field = float(field)
    sigma = float(sigma)
    n = int(n)
    significance = float(significance)
    tTestmi = float(tTestmi)  

    # Calculer le t-test
    t_statistic = (field - tTestmi) / (sigma / np.sqrt(n))

    # Calculer la p-value pour le test bilatéral
    p_value_two_sided = t.sf(abs(t_statistic), df=n-1) * 2

    # Interpréter les résultats du test
    hypothesis_result_two_sided = "Hypothesis rejected: The sample mean is significantly different from the specified mean." if p_value_two_sided < significance else "Hypothesis not rejected: There is no significant difference between the sample mean and the specified mean."

    # Retourner les résultats du test sous forme de dictionnaire
    return {
        't_statistic': t_statistic,
        'p_value_two_sided': p_value_two_sided,
        'hypothesis_result_two_sided': hypothesis_result_two_sided,
    }

def test_traitement(request):
    if request.method == 'GET':
        test_type = request.GET.get('testType')
        if test_type:
            # Récupérer les paramètres communs à tous les tests
            significance = float(request.GET.get('significance', 0.05))

            if test_type == 'tTest':
                # Récupérer les paramètres spécifiques au t-test
                field1 = request.GET.get('tTestField1')
                field2 = request.GET.get('tTestField2')
                s1 = request.GET.get('tTestS1')
                s2 = request.GET.get('tTestS2')
                n1 = request.GET.get('tTestN1')
                n2 = request.GET.get('tTestN2')

                t_stat, p_value, hypothesis_result = calculate_t_test(field1, field2, s1, s2, n1, n2, significance)

                # Construire la réponse JSON avec chaque résultat dans des phrases distinctes
                result_json = {
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'hypothesis_result': hypothesis_result,
                    'formula': f"t = (X̄1 - X̄2) / sqrt(s1^2/n1 + s2^2/n2)"
                }

                return JsonResponse(result_json)
                
            elif test_type == 'zTest':
                # Récupérer les paramètres spécifiques au z-test
                field = request.GET.get('zTestField')
                sigma = request.GET.get('zTestSigma')
                n = request.GET.get('zTestN')
                zTestmi =request.GET.get('zTestmi')
                z_test_results = calculate_z_test(field,  zTestmi,sigma, n, significance)

                # Extraire chaque résultat pour l'affichage
                z_statistic_result = z_test_results['z_statistic']
                p_value_two_sided_result = z_test_results['p_value_two_sided']
                p_value_left_result = z_test_results['p_value_left']
                p_value_right_result = z_test_results['p_value_right']
                hypothesis_result_two_sided = z_test_results['hypothesis_result_two_sided']
                hypothesis_result_left = z_test_results['hypothesis_result_left']
                hypothesis_result_right = z_test_results['hypothesis_result_right']

                # Construire la réponse JSON avec chaque résultat dans des phrases distinctes
                result_json = {
                    'z_statistic': z_statistic_result,
                    'p_value_two_sided': p_value_two_sided_result,
                    'p_value_left': p_value_left_result,
                    'p_value_right': p_value_right_result,
                    'hypothesis_result_two_sided': hypothesis_result_two_sided,
                    'hypothesis_result_left': hypothesis_result_left,
                    'hypothesis_result_right': hypothesis_result_right,
                    'formula': f"Z = (X̄ - μ) / (σ/ √n)"
                }

                return JsonResponse(result_json)
            
            elif test_type == 'tTest2':
                # Récupérer les paramètres spécifiques au t-test
                field = request.GET.get('tTestField2')
                sigma = request.GET.get('tTestSigma2')
                n = request.GET.get('testTestN2')
                tTestmi = request.GET.get('tTestmi2')
                t_test_results = calculate_t_test2(field, tTestmi, sigma, n, significance)

                # Extraire chaque résultat pour l'affichage
                t_statistic_result = t_test_results['t_statistic']
                p_value_two_sided_result = t_test_results['p_value_two_sided']
                hypothesis_result_two_sided = t_test_results['hypothesis_result_two_sided']

                # Construire la réponse JSON avec chaque résultat dans des phrases distinctes
                result_json = {
                    't_statistic': t_statistic_result,
                    'p_value_two_sided': p_value_two_sided_result,
                    'hypothesis_result_two_sided': hypothesis_result_two_sided,
                    'formula': f"t = (X̄ - μ) / (σ/ √n)"
                }

                return JsonResponse(result_json)

            elif test_type == 'linearRegression':
                x_values_str = request.GET.get('linearRegressionX', '')
                y_values_str = request.GET.get('linearRegressionY', '')

                x_values = [float(value) for value in x_values_str.split()]
                y_values = [float(value) for value in y_values_str.split()]

                # Appeler la fonction calculate_linear_regression
                slope, intercept = calculate_linear_regression(x_values, y_values)

                # Créer un graphique de dispersion avec la ligne de régression
                plt.scatter(x_values, y_values, label='Data points')
                plt.plot(x_values, slope * np.array(x_values) + intercept, color='red', label='Regression line')
                plt.xlabel('Variable indépendante (X)')
                plt.ylabel('Variable dépendante (Y)')
                plt.legend()

                # Convertir le graphique en image
                image_stream = io.BytesIO()
                plt.savefig(image_stream, format='png')
                image_stream.seek(0)

                # Encoder l'image en base64 pour l'inclure dans la réponse JSON
                image_data = base64.b64encode(image_stream.read()).decode('utf-8')

                # Fermer le graphique
                plt.close()

                # Retourner l'image en réponse JSON, ainsi que la pente et l'ordonnée à l'origine
                return JsonResponse({'image_path': image_data, 'slope': slope, 'intercept': intercept})

            else:
                return JsonResponse({'error': 'Invalid test type'})

        else:
            return JsonResponse({'error': 'Invalid test type'})
    else:
        return JsonResponse({'error': 'Invalid request method'})

def dashboard(request):
    segment = 'dashboard'
    # Assuming 'probability.html' is located in the 'templates' directory
    return render(request, 'pages/dashboard.html', {'segment': segment})