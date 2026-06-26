import os
from django.conf import settings
from users.models import UserProfile
from user_interaction.models import UserInput, AIResponse, InteractionSession
import json
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIService:
    def __init__(self):
        self.openai_available = OPENAI_AVAILABLE
        if self.openai_available:
            try:
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = getattr(settings, 'AI_SETTINGS', {}).get('MODEL_NAME', 'gpt-3.5-turbo')
                self.max_tokens = getattr(settings, 'AI_SETTINGS', {}).get('MAX_TOKENS', 500)
                self.temperature = getattr(settings, 'AI_SETTINGS', {}).get('TEMPERATURE', 0.7)
            except Exception as e:
                print(f"OpenAI initialization failed: {e}")
                self.openai_available = False
    
    def get_user_context(self, user, session_id=None):
        """Get user's historical context and preferences"""
        try:
            profile = UserProfile.objects.get(user=user)
            
            # Get recent interactions
            recent_interactions = UserInput.objects.filter(
                session__user=user
            ).prefetch_related('ai_response').order_by('-timestamp')[:5]
            
            context = {
                'user_profile': {
                    'bio': profile.bio,
                    'location': profile.location,
                    'emotional_patterns': profile.emotional_patterns,
                    'trust_score': user.trust_score
                },
                'recent_interactions': []
            }
            
            for interaction in recent_interactions:
                context['recent_interactions'].append({
                    'user_input': interaction.input_data,
                    'ai_response': interaction.ai_response.response_data if hasattr(interaction, 'ai_response') and interaction.ai_response else None,
                    'emotional_state': interaction.emotional_state,
                    'timestamp': interaction.timestamp.isoformat()
                })
            
            return context
        except Exception as e:
            return {'error': str(e)}
    
    def generate_response(self, user_input, user, session_id, emotional_state=None):
        """Generate AI response using OpenAI GPT or fallback"""
        if not self.openai_available or not getattr(settings, 'OPENAI_API_KEY', None):
            return self._generate_fallback_response(user_input, emotional_state)
        
        try:
            # Get user context
            user_context = self.get_user_context(user, session_id)
            
            # Prepare conversation history
            messages = self._prepare_messages(user_input, user_context, emotional_state)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                n=1
            )
            
            ai_response_text = response.choices[0].message.content
            
            # Extract reasoning if present
            reasoning = self._extract_reasoning(ai_response_text)
            if reasoning:
                # Remove reasoning from main response
                ai_response_text = ai_response_text.replace(f"Reasoning: {reasoning}", "").strip()
            
            return {
                'success': True,
                'response': ai_response_text,
                'reasoning': reasoning or "Analysis based on user input and contextual understanding.",
                'confidence': min(0.95, 0.9 if response.choices[0].finish_reason == 'stop' else 0.7)
            }
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_response(user_input, emotional_state)
    
    def _prepare_messages(self, user_input, user_context, emotional_state):
        """Prepare messages for OpenAI API"""
        system_message = getattr(settings, 'AI_SETTINGS', {}).get('SYSTEM_PROMPT', 
            "You are HAIS (Human AI Interaction System), an advanced AI assistant designed to help users with decision-making, problem-solving, and personal development.")
        
        # Add emotional context to system message
        if emotional_state:
            system_message += f"\n\nCurrent user emotional state: {emotional_state}. Adjust your tone accordingly."
        
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Add user context if available
        if 'user_profile' in user_context and not user_context.get('error'):
            profile = user_context['user_profile']
            context_message = f"User Context:\n"
            if profile.get('bio'):
                context_message += f"- Bio: {profile['bio']}\n"
            if profile.get('emotional_patterns'):
                context_message += f"- Typical emotional patterns: {profile['emotional_patterns']}\n"
            if profile.get('trust_score'):
                context_message += f"- Trust level: {profile['trust_score']}\n"
            
            messages.append({"role": "system", "content": context_message})
        
        # Add recent conversation history
        if 'recent_interactions' in user_context:
            for interaction in user_context['recent_interactions'][:3]:  # Last 3 interactions
                if interaction['user_input']:
                    messages.append({"role": "user", "content": interaction['user_input']})
                if interaction['ai_response']:
                    messages.append({"role": "assistant", "content": interaction['ai_response']})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _extract_reasoning(self, response_text):
        """Extract reasoning from response if present"""
        reasoning_indicators = [
            "Reasoning:",
            "Analysis:",
            "Thinking:",
            "Here's my thought process:"
        ]
        
        for indicator in reasoning_indicators:
            if indicator in response_text:
                parts = response_text.split(indicator, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return None
    
    def _generate_fallback_response(self, user_input, emotional_state=None):
        """Generate intelligent fallback responses"""
        # More sophisticated fallback responses based on input type
        if any(word in user_input.lower() for word in ['career', 'job', 'work', 'professional']):
            response = self._get_career_advice(user_input)
        elif any(word in user_input.lower() for word in ['decision', 'choose', 'option', 'select']):
            response = self._get_decision_advice(user_input)
        elif any(word in user_input.lower() for word in ['time', 'schedule', 'busy', 'overwhelmed']):
            response = self._get_time_management_advice(user_input)
        elif any(word in user_input.lower() for word in ['learn', 'skill', 'study', 'education']):
            response = self._get_learning_advice(user_input)
        else:
            response = self._get_general_advice(user_input)
        
        return {
            'success': True,
            'response': response['response'],
            'reasoning': response['reasoning'],
            'confidence': 0.7
        }
    
    def _get_career_advice(self, user_input):
        advice_responses = [
            "When considering career decisions, it's important to align your choices with your long-term goals, values, and strengths. Research shows that people who choose careers matching their intrinsic motivations report higher job satisfaction.",
            "Career transitions can be challenging but rewarding. I'd recommend conducting a thorough self-assessment of your skills and interests, researching market trends, and networking with professionals in your target field.",
            "For career advancement, focus on developing both technical skills and soft skills like communication and leadership. Consider finding a mentor who can provide guidance based on their experience in your industry."
        ]
        import random
        return {
            'response': random.choice(advice_responses),
            'reasoning': 'Career advice based on established career development principles and research.'
        }
    
    def _get_decision_advice(self, user_input):
        decision_frameworks = [
            "For complex decisions, consider using a decision matrix where you weight different factors by importance. This helps quantify subjective preferences.",
            "The 'Pros and Cons' method is classic for a reason - it forces you to consider both sides objectively. You might also consider the 10-10-10 rule: how will this decision affect you in 10 weeks, 10 months, and 10 years?",
            "When facing uncertainty, scenario planning can be helpful. Consider the best-case, worst-case, and most likely outcomes for each option."
        ]
        import random
        return {
            'response': random.choice(decision_frameworks),
            'reasoning': 'Decision-making framework suggestion based on established methodologies.'
        }
    
    def _get_time_management_advice(self, user_input):
        time_management_tips = [
            "The Eisenhower Matrix can help prioritize tasks by urgency and importance. Focus on important but not urgent tasks to prevent future crises.",
            "Time blocking is effective for many people - schedule specific blocks of time for different types of work and include buffer time for unexpected interruptions.",
            "Consider the Pareto Principle (80/20 rule) - often 80% of results come from 20% of efforts. Identify which activities yield the highest return on your time investment."
        ]
        import random
        return {
            'response': random.choice(time_management_tips),
            'reasoning': 'Time management strategy based on proven productivity techniques.'
        }
    
    def _get_learning_advice(self, user_input):
        learning_strategies = [
            "For effective learning, spaced repetition has been shown to significantly improve long-term retention. Review material at increasing intervals over time.",
            "The Feynman Technique is powerful - try to explain the concept in simple terms as if teaching someone else. This reveals gaps in your understanding.",
            "Active recall (retrieving information from memory) is more effective than passive review. Test yourself regularly rather than just re-reading material."
        ]
        import random
        return {
            'response': random.choice(learning_strategies),
            'reasoning': 'Learning strategy based on cognitive science and educational research.'
        }
    
    def _get_general_advice(self, user_input):
        general_responses = [
            "I understand you're seeking guidance. It can be helpful to break complex situations into smaller, manageable components and address them systematically.",
            "When facing challenges, sometimes stepping back to gain perspective can reveal new approaches. Consider discussing the situation with trusted colleagues or mentors for additional insights.",
            "Many successful problem-solvers recommend defining the problem clearly first, then brainstorming multiple solutions before evaluating them against your specific criteria and constraints."
        ]
        import random
        return {
            'response': random.choice(general_responses),
            'reasoning': 'General problem-solving approach based on systematic thinking principles.'
        }

# Singleton instance
ai_service = AIService()