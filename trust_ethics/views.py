from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import TrustMetric, EthicalAlignment, MutualTrust
import json
import os
from user_interaction.models import AIResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from .trust_ml import trainer

@login_required
def trust_dashboard(request):
    trust_metrics = TrustMetric.objects.filter(user=request.user).order_by('-timestamp')[:10]
    ethical_alignments = EthicalAlignment.objects.filter(user=request.user)
    mutual_trust = MutualTrust.objects.filter(user=request.user).last()
    
    # Prepare data for charts
    trust_data = {
        'labels': [metric.timestamp.strftime('%Y-%m-%d') for metric in trust_metrics],
        'values': [metric.value for metric in trust_metrics]
    }
    
    ethical_data = {
        'principles': [alignment.principle for alignment in ethical_alignments],
        'scores': [alignment.alignment_score for alignment in ethical_alignments]
    }
    
    return render(request, 'trust_ethics/dashboard.html', {
        'trust_metrics': trust_metrics,
        'ethical_alignments': ethical_alignments,
        'mutual_trust': mutual_trust,
        'trust_data': json.dumps(trust_data),
        'ethical_data': json.dumps(ethical_data)
    })

@login_required
def update_trust_preferences(request):
    if request.method == 'POST':
        # Update user trust preferences
        try:
            user_profile = request.user.userprofile
            preferences = user_profile.preferences
            
            preferences['trust_settings'] = {
                'transparency_level': request.POST.get('transparency_level', 'medium'),
                'explanation_depth': request.POST.get('explanation_depth', 'detailed'),
                'feedback_frequency': request.POST.get('feedback_frequency', 'regular')
            }
            
            user_profile.save()
            messages.success(request, 'Trust preferences updated successfully!')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Error updating preferences: {str(e)}')
    
    return render(request, 'trust_ethics/preferences.html')

@login_required
def ethical_metrics(request):
    metrics = TrustMetric.objects.filter(user=request.user).order_by('-timestamp')
    alignments = EthicalAlignment.objects.filter(user=request.user)
    
    return render(request, 'trust_ethics/ethical_metrics.html', {
        'metrics': metrics,
        'alignments': alignments
    })


@login_required
@require_POST
def calibrated_confidence_api(request):
    """Return calibrated confidence for one or more AIResponse ids.

    POST JSON body should be {"ai_response_id": 123} or {"ai_response_ids": [1,2,3]}
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    ids = []
    if 'ai_response_id' in data:
        ids = [int(data['ai_response_id'])]
    elif 'ai_response_ids' in data:
        ids = [int(i) for i in data['ai_response_ids']]
    else:
        return JsonResponse({'error': 'no id provided'}, status=400)

    results = {}
    for rid in ids:
        try:
            ar = AIResponse.objects.get(id=rid)
            c = trainer.predict_confidence(ar)
            results[rid] = c
        except AIResponse.DoesNotExist:
            results[rid] = None
    return JsonResponse({'confidences': results})


@staff_member_required
def admin_model_dashboard(request):
    """Simple staff-only dashboard showing model versions and recent metrics."""
    models = trainer.list_saved_models()
    recent_metrics = TrustMetric.objects.order_by('-timestamp')[:50]
    # Basic model metadata
    model_info = {
        'vectorizer': trainer.vectorizer,
        'has_calibrator': trainer.calibrator is not None,
        'latest_model': os.path.basename(trainer.model_path) if trainer.model_path else None,
    }
    return render(request, 'trust_ethics/admin_dashboard.html', {
        'models': models,
        'recent_metrics': recent_metrics,
        'model_info': model_info,
    })