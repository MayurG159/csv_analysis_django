from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
import pandas as pd
import numpy as np
from pandas.api.types import is_categorical_dtype
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import os
from io import BytesIO
import base64
import warnings

# Suppress specific pandas warning
warnings.simplefilter(action='ignore', category=FutureWarning)

# Create your views here.
def Home(request):
    return render(request, "upload_and_analyze//upload_and_analyze.html")

def upload_and_analyze(request):
    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        try:
            # Step 1: Read the CSV file using pandas
            df = pd.read_csv(csv_file, na_values=['na'])
            df = df.convert_dtypes(convert_integer=True, convert_string=False)
            # Step 2: Perform basic data analysis
            preview = df.head(5).to_html(classes='table table-bordered')  # First 5 rows
            summary_stats = df.describe().to_html(classes='table table-bordered')  # Summary statistics
            missing_values = df.isnull().sum().to_dict()  # Missing values per column
            filtered_dict = {key: value for key, value in missing_values.items() if value > 0}
            handled_missing_values={}
            if not filtered_dict:
                handled_missing_values = {'-' : ["No missing values","No need to replace"]}
            else :
                missing_values = filtered_dict
                # Handling missing values.
                for column, value in missing_values.items():
                    if is_categorical_dtype(df[column]) == True:
                        mode = df[column].mode()[0]
                        df[column].fillna(mode, inplace=True)
                        handled_missing_values[column]=[value, f"Mode : {mode}"]
                    else :
                        df_skewness = df[column].skew()
                        if pd.notna(df_skewness) and (df_skewness > 0.3 or df_skewness < 0.3):
                            median = df[column].median()
                            df[column].fillna(median, inplace=True)
                            handled_missing_values[column]=[value, f"Median : {median}"]
                        else:
                            df[column].fillna(0, inplace=True)
                            mean = df[column].mean()
                            df[column].fillna(mean, inplace=True)
                            handled_missing_values[column]=[value, f"Mean : {mean}"]

            # Step 3: Generate visualizations
            visualizations = []

            # Example: Generate a histogram for numerical columns
            for col in df.select_dtypes(include=['float64', 'int64']).columns:
                plt.figure(figsize=(6, 4))
                sns.histplot(df[col].dropna(), kde=True, color='skyblue', bins=20)
                plt.title(f"Histogram for {col}")
                plt.xlabel(col)
                plt.ylabel("Frequency")
                
                # Save the plot to a BytesIO object
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                encoded_img = base64.b64encode(image_png).decode('utf-8')
                visualizations.append(f"data:image/png;base64,{encoded_img}")
                plt.close()

            context = {
                'preview': preview,
                'summary_stats': summary_stats,
                'Columns_of_missing_values': handled_missing_values,
                'visualizations': visualizations,
                'message': 'Analysis completed successfully!',
            }

            return render(request, 'upload_and_analyze/analyze_result.html', context)

        except Exception as e:
            return render(request, 'upload_and_analyze/upload_and_analyze.html', {'error': f'Error: {str(e)}'})

    return render(request, 'upload_and_analyze/upload_and_analyze.html')