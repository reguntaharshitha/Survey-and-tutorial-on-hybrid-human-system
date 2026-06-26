from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import uuid
import json
from .forms import TextInputForm, ImageInputForm
from .models import InteractionSession, UserInput, AIResponse
from hais_core.ai_service import ai_service

@login_required
def interaction_home(request):
    # Get or create active session
    session_id = request.session.get('current_session')
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session['current_session'] = session_id
        InteractionSession.objects.create(
            user=request.user,
            session_id=session_id
        )
    
    # Get session history for display - FIXED QUERY
    session_history = []
    if session_id:
        try:
            current_session = InteractionSession.objects.get(session_id=session_id)
            # Use prefetch_related instead of select_related for reverse relations
            session_history = UserInput.objects.filter(
                session=current_session
            ).prefetch_related('ai_response').order_by('timestamp')
        except InteractionSession.DoesNotExist:
            pass
    
    text_form = TextInputForm()
    image_form = ImageInputForm()
    
    return render(request, 'user_interaction/interaction_home.html', {
        'text_form': text_form,
        'image_form': image_form,
        'session_id': session_id,
        'session_history': session_history
    })

@login_required
def process_text_input(request):
    if request.method == 'POST':
        form = TextInputForm(request.POST)
        if form.is_valid():
            session_id = request.session.get('current_session')
            if not session_id:
                return JsonResponse({'success': False, 'error': 'No active session'})
            
            try:
                session = InteractionSession.objects.get(session_id=session_id)
                
                # Save user input
                user_input = UserInput.objects.create(
                    session=session,
                    input_type='text',
                    input_data=form.cleaned_data['text_input'],
                    emotional_state=form.cleaned_data['emotional_state'] or 'neutral',
                    confidence_score=0.9
                )
                
                # Generate AI response using the AI service
                ai_result = ai_service.generate_response(
                    user_input=form.cleaned_data['text_input'],
                    user=request.user,
                    session_id=session_id,
                    emotional_state=form.cleaned_data['emotional_state']
                )
                
                if ai_result['success']:
                    # Save AI response
                    ai_response = AIResponse.objects.create(
                        user_input=user_input,
                        response_data=ai_result['response'],
                        reasoning=ai_result['reasoning'],
                        confidence_score=ai_result['confidence']
                    )
                    
                    # Update user trust score based on interaction quality
                    _update_trust_score(request.user, ai_result['confidence'])
                    
                    return JsonResponse({
                        'success': True,
                        'user_input': form.cleaned_data['text_input'],
                        'ai_response': ai_result['response'],
                        'reasoning': ai_result['reasoning'],
                        'confidence': ai_result['confidence'],
                        'emotional_state': form.cleaned_data['emotional_state'],
                        'input_id': user_input.id,
                        'response_id': ai_response.id
                    })
                else:
                    # Use fallback if AI service fails
                    fallback = generate_fallback_response(form.cleaned_data['text_input'])
                    ai_response = AIResponse.objects.create(
                        user_input=user_input,
                        response_data=fallback['response'],
                        reasoning=fallback['reasoning'],
                        confidence_score=fallback['confidence']
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'user_input': form.cleaned_data['text_input'],
                        'ai_response': fallback['response'],
                        'reasoning': fallback['reasoning'],
                        'confidence': fallback['confidence'],
                        'emotional_state': form.cleaned_data['emotional_state'],
                        'input_id': user_input.id,
                        'response_id': ai_response.id
                    })
                    
            except InteractionSession.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Session not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def process_image_input(request):
    if request.method == 'POST':
        form = ImageInputForm(request.POST, request.FILES)
        if form.is_valid():
            session_id = request.session.get('current_session')
            if session_id:
                try:
                    session = InteractionSession.objects.get(session_id=session_id)
                    
                    # For image inputs, we'll use the description with the AI service
                    description = form.cleaned_data['description'] or 'Image analysis requested'
                    
                    # Save user input
                    user_input = UserInput.objects.create(
                        session=session,
                        input_type='image',
                        input_data=description,
                        emotional_state='analytical'
                    )
                    
                    # Generate AI response for the image context
                    prompt = f"User uploaded an image with description: '{description}'. Please provide analysis, insights, or respond to any questions about this image."
                    
                    ai_result = ai_service.generate_response(
                        user_input=prompt,
                        user=request.user,
                        session_id=session_id,
                        emotional_state='analytical'
                    )
                    
                    if ai_result['success']:
                        ai_response = AIResponse.objects.create(
                            user_input=user_input,
                            response_data=ai_result['response'],
                            reasoning=ai_result['reasoning'],
                            confidence_score=ai_result['confidence']
                        )
                        
                        return JsonResponse({
                            'success': True,
                            'user_input': f"Image: {description}",
                            'ai_response': ai_result['response'],
                            'reasoning': ai_result['reasoning'],
                            'confidence': ai_result['confidence']
                        })
                    else:
                        fallback = generate_fallback_response(description)
                        ai_response = AIResponse.objects.create(
                            user_input=user_input,
                            response_data=fallback['response'],
                            reasoning=fallback['reasoning'],
                            confidence_score=fallback['confidence']
                        )
                        
                        return JsonResponse({
                            'success': True,
                            'user_input': f"Image: {description}",
                            'ai_response': fallback['response'],
                            'reasoning': fallback['reasoning'],
                            'confidence': fallback['confidence']
                        })
                        
                except InteractionSession.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Session not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid image upload'})

def _update_trust_score(user, confidence):
    """Update user's trust score based on interaction quality"""
    try:
        # Simple trust scoring based on AI confidence and recent interactions
        user.trust_score = min(1.0, user.trust_score + (confidence * 0.01))
        user.save(update_fields=['trust_score'])
    except Exception as e:
        print(f"Error updating trust score: {e}")

def generate_fallback_response(user_input, emotional_state=None):
    """Generate fallback responses when AI service is down"""
    fallback_responses = [
        "I understand you're asking about {topic}. Based on general principles, I'd suggest considering multiple perspectives and gathering more information before making decisions.",
        "That's an interesting question about {topic}. In similar situations, people often find it helpful to break down the problem into smaller parts and address each systematically.",
        "Regarding {topic}, I recommend looking at both short-term and long-term implications. It might also help to discuss this with trusted colleagues or mentors.",
        "I appreciate you sharing this about {topic}. Many factors could influence the best approach here - your personal goals, available resources, and timeline all play important roles.",
        "For {topic}, it's often useful to consider the potential risks and benefits of different approaches. You might also want to think about what aligns best with your values and long-term objectives."
    ]
    
    # Simple topic extraction
    topic = "this matter"
    keywords = ['career', 'decision', 'time', 'work', 'learn', 'skill', 'project', 'goal', 'relationship', 'problem']
    for keyword in keywords:
        if keyword in user_input.lower():
            topic = keyword
            break
    
    import random
    response = random.choice(fallback_responses).format(topic=topic)
    
    return {
        'response': response,
        'reasoning': 'Fallback response generated based on common decision-making principles.',
        'confidence': 0.6
    }