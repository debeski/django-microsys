from django.apps import apps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
import json
from datetime import date, datetime

def _can_view_model(user, app_label, model_name):
    """Check if user has permission to view the model."""
    perm = f"{app_label}.view_{model_name}"
    return user.has_perm(perm)

def _serialize_instance(instance):
    """Serialize model instance to a dictionary for autofill."""
    data = {}
    
    # Iterate over model fields
    for field in instance._meta.fields:
        field_name = field.name
        
        # Skip sensitive or system fields
        if field_name in ['password', 'id', 'pk'] or field.auto_created:
            continue
            
        value = getattr(instance, field_name)
        
        # Handle different field types
        if value is None:
            data[field_name] = ""
        
        elif field.is_relation:
            # For ForeignKey, return the PK
            if field.many_to_one:
                data[field_name] = value.pk
        
        elif isinstance(value, (datetime, date)):
             data[field_name] = value.isoformat()
             
        elif field.get_internal_type() in ['FileField', 'ImageField']:
            # Skip files for autofill
            continue
            
        else:
            data[field_name] = value
            
    # Include metadata
    data['_pk'] = instance.pk
    return data

@login_required
def get_last_entry(request, app_label, model_name):
    """
    Fetch the last created entry for a model.
    Supports ?before_id=<int> to fetch previous records (for blacklist navigation).
    """
    if not _can_view_model(request.user, app_label, model_name):
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        return JsonResponse({'error': 'Model not found'}, status=404)
        
    # Build query
    qs = model.objects.all().order_by('-pk')
    
    # Handle pagination/blacklist skip
    before_id = request.GET.get('before_id')
    if before_id:
        try:
            qs = qs.filter(pk__lt=int(before_id))
        except ValueError:
            pass
            
    instance = qs.first()
    
    if not instance:
        return JsonResponse({'error': 'No record found'}, status=404)
        
    return JsonResponse(_serialize_instance(instance))

@login_required
def get_model_details(request, app_label, model_name, pk):
    """
    Fetch a specific model instance by PK.
    Used when sticky fields point to a specific valid ID.
    """
    if not _can_view_model(request.user, app_label, model_name):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        return JsonResponse({'error': 'Model not found'}, status=404)
        
    instance = get_object_or_404(model, pk=pk)
    return JsonResponse(_serialize_instance(instance))
