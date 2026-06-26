from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserProfile


class CustomLoginView(LoginView):
    """Custom login view that redirects admins to admin portal"""
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        """Redirect superuser/staff to admin portal, others to dashboard"""
        user = self.request.user
        
        # If user is superuser or staff, redirect to admin portal
        if user.is_superuser or user.is_staff:
            return reverse_lazy('admin_portal_dashboard')
        
        # Otherwise redirect to regular dashboard
        return reverse_lazy('dashboard')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Account created successfully! Welcome, {username}!')
                return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'users/profile.html', {'form': form})

@login_required
def dashboard(request):
    from user_interaction.models import InteractionSession, UserInput
    from decision_reports.models import DecisionReport
    from recommendations.models import Recommendation
    from trust_ethics.models import TrustMetric, MutualTrust
    from django.db.models import Count, Avg
    
    # Count interactions (sessions and inputs)
    total_interactions = InteractionSession.objects.filter(user=request.user).count()
    user_inputs = UserInput.objects.filter(session__user=request.user).count()
    active_sessions = InteractionSession.objects.filter(user=request.user, end_time__isnull=True).count()
    
    # Get recent interaction sessions
    recent_sessions = InteractionSession.objects.filter(
        user=request.user
    ).order_by('-start_time')[:5]
    
    # Count and get recent reports
    total_reports = DecisionReport.objects.filter(user=request.user).count()
    recent_reports = DecisionReport.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Count and get recommendations
    total_recommendations = Recommendation.objects.filter(user=request.user).count()
    accepted_recommendations = Recommendation.objects.filter(
        user=request.user, 
        is_accepted=True
    ).count()
    pending_recommendations = Recommendation.objects.filter(
        user=request.user, 
        is_accepted=False
    ).count()
    recent_recommendations = Recommendation.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Get trust metrics
    latest_trust_metric = TrustMetric.objects.filter(
        user=request.user
    ).order_by('-timestamp').first()
    
    mutual_trust = MutualTrust.objects.filter(
        user=request.user
    ).order_by('-timestamp').first()
    
    # Average confidence from AI responses
    avg_confidence = UserInput.objects.filter(
        session__user=request.user
    ).aggregate(avg_conf=Avg('confidence_score'))['avg_conf'] or 0.0
    
    # Calculate trust score from various metrics
    trust_score = request.user.trust_score
    if mutual_trust:
        trust_score = mutual_trust.mutual_trust_score
    
    # Calculate percentages for progress bars
    ai_trust_percentage = int(mutual_trust.ai_trust_in_user * 100) if mutual_trust else 50
    user_trust_percentage = int(mutual_trust.user_trust_in_ai * 100) if mutual_trust else 50
    avg_confidence_percentage = int(avg_confidence * 100) if avg_confidence else 0
    
    context = {
        'user': request.user,
        'total_interactions': total_interactions,
        'user_inputs': user_inputs,
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
        'total_reports': total_reports,
        'recent_reports': recent_reports,
        'total_recommendations': total_recommendations,
        'accepted_recommendations': accepted_recommendations,
        'pending_recommendations': pending_recommendations,
        'recent_recommendations': recent_recommendations,
        'trust_score': trust_score,
        'latest_trust_metric': latest_trust_metric,
        'mutual_trust': mutual_trust,
        'avg_confidence': avg_confidence,
        'ai_trust_percentage': ai_trust_percentage,
        'user_trust_percentage': user_trust_percentage,
        'avg_confidence_percentage': avg_confidence_percentage,
    }
    return render(request, 'users/dashboard.html', context)

def home(request):
    """Home page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

from django.contrib.auth import logout
def custom_logout(request):
    logout(request)
    return redirect('home') 