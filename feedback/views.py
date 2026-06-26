from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .forms import FeedbackForm
from .models import Feedback
from user_interaction.models import AIResponse, InteractionSession

@login_required
def provide_feedback(request, response_id):
    ai_response = get_object_or_404(AIResponse, id=response_id)
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.ai_response = ai_response
            feedback.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            messages.success(request, 'Feedback submitted successfully!')
            return redirect('interaction_home')
    else:
        form = FeedbackForm()
    
    return render(request, 'feedback/feedback_form.html', {
        'form': form,
        'ai_response': ai_response
    })

@login_required
def feedback_history(request):
    feedbacks = Feedback.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'feedback/feedback_history.html', {'feedbacks': feedbacks})

@login_required
def ajax_feedback(request, response_id):
    if request.method == 'POST':
        ai_response = get_object_or_404(AIResponse, id=response_id)
        
        feedback = Feedback.objects.create(
            user=request.user,
            ai_response=ai_response,
            feedback_type=request.POST.get('feedback_type', 'agreement'),
            rating=request.POST.get('rating'),
            comment=request.POST.get('comment', ''),
            emotional_response=request.POST.get('emotional_response', 'neutral')
        )
        
        return JsonResponse({'success': True, 'feedback_id': feedback.id})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})



@login_required
def submit_feedback(request):
    """View for users to submit feedback"""
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        interaction_id = request.POST.get('interaction_id')
        try:
            # Get the interaction session if provided
            interaction_session = None
            if interaction_id:
                interaction_session = InteractionSession.objects.filter(id=interaction_id, user=request.user).first()

            # Create feedback. `Feedback.ai_response` is optional now so we
            # don't require an AIResponse when storing generic feedback from
            # users (e.g. from a feedback form).
            feedback = Feedback.objects.create(
                user=request.user,
                rating=rating or None,
                comment=comment or '',
                ai_response=None
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for your feedback!'
                })
            else:
                messages.success(request, 'Thank you for your feedback!')
                return redirect('user_dashboard')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Error submitting feedback. Please try again.'
                })
            else:
                messages.error(request, 'Error submitting feedback. Please try again.')
    
    # Get recent interactions for context
    recent_interactions = InteractionSession.objects.filter(
        user=request.user
    ).order_by('-start_time')[:5]
    
    return render(request, 'feedback/submit_feedback.html', {
        'recent_interactions': recent_interactions
    })

@login_required
def feedback_success(request):
    """Feedback submission success page"""
    return render(request, 'feedback/feedback_success.html')

@login_required
def my_feedback(request):
    """View for users to see their own feedback history"""
    user_feedback = Feedback.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'feedback/my_feedback.html', {
        'feedbacks': user_feedback
    })