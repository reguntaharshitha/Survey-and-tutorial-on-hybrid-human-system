import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_core.settings')
django.setup()

from users.models import CustomUser, UserProfile
from user_interaction.models import InteractionSession, UserInput, AIResponse
from feedback.models import Feedback
from decision_reports.models import DecisionReport, CriticalNotice
from trust_ethics.models import TrustMetric, EthicalAlignment, MutualTrust
from recommendations.models import Recommendation

def generate_sample_data():
    """Generate comprehensive sample data for testing"""
    
    # Get or create test user
    user, created = CustomUser.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'role': 'user'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        UserProfile.objects.create(user=user)
    
    # Generate interaction sessions
    sessions = []
    for i in range(5):
        session = InteractionSession.objects.create(
            user=user,
            session_id=f"SESSION-{user.id}-{i+1}",
            end_time=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        sessions.append(session)
    
    # Generate user inputs and AI responses
    sample_inputs = [
        "I'm trying to decide on a career path. What factors should I consider?",
        "How can I improve my decision-making skills?",
        "I'm feeling uncertain about a major life decision. Any advice?",
        "What's the best way to balance logic and emotion in decisions?",
        "How do I know if I'm making the right choice?"
    ]
    
    sample_responses = [
        "Consider your passions, skills, market demand, and work-life balance preferences. Also think about long-term growth opportunities.",
        "Practice making smaller decisions quickly, gather diverse perspectives, and reflect on past decisions to learn from outcomes.",
        "Break down the decision into smaller parts, consider worst-case scenarios, and trust your accumulated experience and intuition.",
        "Use logical analysis for facts and data, but also acknowledge emotional signals as valuable information about your values and preferences.",
        "There's rarely one 'right' choice. Focus on making the best decision with available information and be prepared to adapt as needed."
    ]
    
    for i, (input_text, response_text) in enumerate(zip(sample_inputs, sample_responses)):
        user_input = UserInput.objects.create(
            session=sessions[i % len(sessions)],
            input_type='text',
            input_data=input_text,
            emotional_state=random.choice(['curious', 'uncertain', 'thoughtful', 'anxious']),
            confidence_score=random.uniform(0.6, 0.9)
        )
        
        ai_response = AIResponse.objects.create(
            user_input=user_input,
            response_data=response_text,
            reasoning=f"Analysis based on user's stated concerns and general decision-making principles. Emotional context: {user_input.emotional_state}",
            confidence_score=random.uniform(0.7, 0.95)
        )
        
        # Generate feedback for some responses
        if i % 2 == 0:
            Feedback.objects.create(
                user=user,
                ai_response=ai_response,
                feedback_type=random.choice(['agreement', 'correction', 'suggestion']),
                rating=random.randint(3, 5),
                comment="Helpful response, thank you!",
                emotional_response='satisfied'
            )
    
    # Generate decision reports
    for i in range(3):
        report = DecisionReport.objects.create(
            user=user,
            report_id=f"RPT-{user.id}-{i+1}",
            title=f"Decision Pattern Analysis #{i+1}",
            summary=f"Analysis of decision-making patterns and behavioral tendencies for user {user.username}.",
            insights={
                "pattern_consistency": random.uniform(0.6, 0.9),
                "decision_confidence": random.uniform(0.5, 0.8),
                "learning_velocity": random.uniform(0.4, 0.7),
                "adaptability_score": random.uniform(0.6, 0.85)
            },
            recommendations=[
                {"type": "behavioral", "action": "Practice divergent thinking", "priority": "medium"},
                {"type": "learning", "action": "Review past successful decisions", "priority": "high"}
            ],
            confidence_scores={
                "overall": random.uniform(0.7, 0.9),
                "behavioral": random.uniform(0.6, 0.8),
                "cognitive": random.uniform(0.7, 0.9),
                "emotional": random.uniform(0.5, 0.75)
            },
            visual_data={
                "chart_type": "radar",
                "labels": ["Pattern Consistency", "Decision Confidence", "Learning Velocity", "Adaptability"],
                "data": [0.85, 0.72, 0.63, 0.78]
            }
        )
        
        # Add critical notice for one report
        if i == 0:
            CriticalNotice.objects.create(
                report=report,
                notice_type="High Emotional Variability",
                priority="medium",
                message="Detected significant emotional fluctuations in decision contexts. Consider implementing emotional regulation techniques.",
                suggested_actions=["Mindfulness practice", "Emotional journaling", "Decision delay for high-stakes choices"]
            )
    
    # Generate trust metrics
    for i in range(10):
        TrustMetric.objects.create(
            user=user,
            metric_type="system_trust",
            value=random.uniform(0.6, 0.95),
            confidence=random.uniform(0.7, 0.9),
            timestamp=datetime.now() - timedelta(days=9-i)
        )
    
    # Generate ethical alignments
    principles = [
        "Transparency in AI reasoning",
        "User autonomy preservation",
        "Fairness in recommendations",
        "Privacy protection",
        "Beneficence in guidance"
    ]
    
    for principle in principles:
        EthicalAlignment.objects.create(
            user=user,
            principle=principle,
            alignment_score=random.uniform(0.7, 0.95),
            explanation=f"System demonstrates strong alignment with {principle.lower()} through consistent behavior and transparent processes."
        )
    
    # Generate mutual trust
    MutualTrust.objects.create(
        user=user,
        ai_trust_in_user=random.uniform(0.7, 0.9),
        user_trust_in_ai=random.uniform(0.6, 0.85),
        mutual_trust_score=random.uniform(0.65, 0.88)
    )
    
    # Generate recommendations
    recommendation_types = ['behavioral', 'content', 'interaction', 'learning']
    for i in range(8):
        Recommendation.objects.create(
            user=user,
            recommendation_type=random.choice(recommendation_types),
            content=f"Sample recommendation #{i+1} for improving decision-making effectiveness.",
            confidence=random.uniform(0.6, 0.9),
            context={"pattern": f"sample_pattern_{i}", "frequency": "regular"},
            is_accepted=random.choice([True, False]),
            is_implemented=random.choice([True, False]) if i % 2 == 0 else False
        )
    
    print(f"Sample data generated successfully for user: {user.username}")

if __name__ == "__main__":
    generate_sample_data()