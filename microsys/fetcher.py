# Fundemental imports
#####################################################################
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.db.models.query import QuerySet
from django.contrib import messages
from io import BytesIO
import mimetypes
import openpyxl
import zipfile
from django.apps import apps

# Universal Downloader
#####################################################################
# Function to download a single specified file
def download_single_file(request, model_name, record_id, file_type):
    """
    A broker function to download files for a given model and record ID.
    
    Args:
    - model_name: The name of the model (e.g., 'Decree', 'Publication').
    - record_id: The ID of the record in the model.
    
    Returns:
    - A response with the file to download.
    """
    if file_type:
        file_type=file_type
    else:
        file_type='all'
    # Step 1: Get the model class dynamically using model_name
    try:
        model_class = apps.get_model('documents', model_name)  # <-- your app label
    except LookupError:
        return JsonResponse({'error': 'Invalid model name'}, status=400)

    # Step 2: Retrieve the record
    record = get_object_or_404(model_class, id=record_id)

    if not request.user.has_perm(f'documents.view_{model_name.lower()}'):
        messages.error(request, "ليس لديك صلاحية لتحميل هذا الملف.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    # Step 3: Now that we have the record, pass it to your file download logic
    return downloader(request, record, file_type=file_type)

# Function that gathers info for the files for renaming purposes
def gather_file_info(request, records, file_type=None):
    """
    Gathers necessary file information from the given records.
    
    Args:
    - records: List of model instances (e.g., Decree, Publication).
    
    Returns:
    - A list of dictionaries containing 'model_name', 'number', 'date', and 'file' for each record.
    """
    files_data = []
    
    for record in records:
        model_name = record.__class__.__name__
        number = getattr(record, 'number', 'unknown')

        # Try to get the date from different possible fields
        date = getattr(record, 'date', None) or \
               getattr(record, 'created_at', None) or \
               getattr(record, 'date_applied', None)

        # If only the year is present, treat it as a full date (e.g., 2022 becomes 2022-01-01)
        if not date:
            year = getattr(record, 'year', None)
            if year:
                date_str = f"{year}-01-01"
            else:
                date_str = 'unknown_date'
        else:
            # If we have a valid date, format it
            date_str = date.strftime('%Y-%m-%d') if date else 'unknown_date'

        file_fields = ["pdf_file", "attach", "receipt_file", "word_file", "response_file"]
        if not file_type:
            file_type='all'
        for field in file_fields:
            file_obj = getattr(record, field, None)
            if file_obj:
                # If file_type is None or matches the field, include it
                if file_type == "all" or field == file_type:
                    files_data.append({
                        "model_name": model_name,
                        "number": number,
                        "date": date_str,
                        "file": file_obj,
                        "field_name": field
                    })

    return files_data

# Main downloader function
def downloader(request, records, file_type=None):
    """
    Generalized function to download one or multiple files.
    
    Args:
    - request: Django request object.
    - files_data (list of dict): Each dict should contain:
        - 'model_name': Model name as a string (e.g., "Decree", "Publication").
        - 'number': Identifier (if applicable, else None).
        - 'date': Date string (formatted as YYYY-MM-DD or 'unknown_date').
        - 'file': File object (Django FileField or ImageField).
    
    Returns:
    - A single file download (PDF, Word, Image).
    - A ZIP download if multiple files are passed.
    """
    if isinstance(records, QuerySet):
        records = list(records)

    # If a single record is passed, wrap it in a list for uniform processing
    if isinstance(records, dict):
        files_data = gather_file_info(request, [records], file_type)
    elif isinstance(records, list):
        files_data = gather_file_info(request, records, file_type)
    else:
        # If it's not a list or dict, treat it as a single record and wrap it in a list
        files_data = gather_file_info(request, [records], file_type)

    # Validate input
    if not files_data or not isinstance(files_data, list):
        messages.error(request, "لا توجد اي ملفات متاحة للتحميـل.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    # If only one matching file exists, serve it directly
    if len(files_data) == 1:
        return serve_single_file(files_data[0])

    # If multiple files match, create a ZIP archive
    return serve_zip_file(files_data)

# Sub Function in charge of serving a single file to the client
def serve_single_file(file_info):
    """Serves a single file with the correct Content-Disposition header."""

    file_obj = file_info.get("file")
    if not file_obj or not file_obj.name:
        return JsonResponse({'error': 'File not found'}, status=404)

    # Generate proper filename
    model_name = file_info.get("model_name", "document")
    number = file_info.get("number", "unknown")
    date_str = file_info.get("date", "unknown_date")
    
    ext = file_obj.name.split('.')[-1]
    filename = f"{model_name}_{number}_{date_str}.{ext}"

    # Determine content type
    content_type, _ = mimetypes.guess_type(file_obj.name) or ('application/octet-stream',)
    
    # Create response
    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Serve file
    with file_obj.open('rb') as f:
        response.write(f.read())

    return response

# Sub Function in charge of serving a zip file to the client
def serve_zip_file(files_data):
    """Zips multiple files and serves as a downloadable response."""
    
    # Assume all files are from the same model
    model_name = files_data[0].get("model_name", "documents")
    
    numbers = [file_info.get("number", 0) for file_info in files_data]
    
    # Sort the numbers to find the first and last
    first_number = min(numbers)
    last_number = max(numbers)
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_info in files_data:
            file_obj = file_info.get("file")
            if file_obj and file_obj.name:
                number = file_info.get("number", "unknown")
                date_str = file_info.get("date", "unknown_date")
                ext = file_obj.name.split('.')[-1]
                filename = f"{model_name}_{number}_{date_str}.{ext}"
                
                with file_obj.open('rb') as f:
                    zip_file.writestr(filename, f.read())

    # Create the zip file name using first_number-last_number
    zip_filename = f"{model_name}_{first_number}-{last_number}.zip"

    # Serve ZIP file
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{zip_filename}"'
    return response

# Excel Exporter
#####################################################################
# Function to export any list of documents to Excel
def export_to_excel(request, queryset, headers_map, sheet_title="Documents"):
    """
    Generic function to export any document queryset to Excel.

    :param request: Django request object
    :param queryset: queryset or list of model instances
    :param headers_map: list of tuples (Excel Header, attribute_name)
    :param sheet_title: Name of Excel sheet
    :return: HttpResponse with Excel file
    """

    if isinstance(queryset, list):
        first_item = queryset[0] if queryset else None
        last_item = queryset[-1] if queryset else None
    else:
        first_item = queryset.first()
        last_item = queryset.last()

    # Create workbook and sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title

    # Add headers
    headers = [h for h, _ in headers_map]
    ws.append(headers)

    # Add rows
    for obj in queryset:
        row = []
        for _, attr in headers_map:
            value = getattr(obj, attr, "")
            # If attribute is a ForeignKey or Object
            if value:
                if hasattr(value, "name"):
                    value = value.name
                else:
                    value = str(value)
            row.append(value if value is not None else "")
        ws.append(row)

    # Filename
    first_number = getattr(first_item, "number", "0")
    last_number = getattr(last_item, "number", "0")
    filename = f"{first_number}-{last_number}.xlsx"

    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

# Headers for export_to_excel function
decree_headers = [
    ("رقم القرار", "number"),
    ("تاريخ القرار", "date"),
    ("الحكومة", "government"),
    ("الوزير", "minister"),
    ("العنوان", "title"),
    ("التفاصيل", "keywords"),
    ("النوع", "type"),
    ("التصنيف", "category"),
    ("ملاحظات", "notes"),
]
other_decree_headers = [
    ("رقم القرار", "number"),
    ("تاريخ القرار", "date"),
    ("الجهة", "affiliate"),
    ("العنوان", "title"),
    ("التفاصيل", "keywords"),
    ("النوع", "type"),
    ("التصنيف", "category"),
    ("ملاحظات", "notes"),
]
other_headers = [
    ("رقم المستند", "number"),
    ("التاريخ", "date"),
    ("العنوان", "title"),
    ("التفاصيل", "keywords"),
    ("ملاحظات", "notes"),
]
