"""
Management command to populate the Q&A database with sample questions and answers.

Usage:
    python manage.py populate_qa
"""

from django.core.management.base import BaseCommand
from recommendations.models import QuestionCategory, Question, Answer


class Command(BaseCommand):
    help = 'Populate the Q&A database with sample questions and answers'

    def handle(self, *args, **options):
        # Create categories
        categories = {}
        category_names = [
            'Career Advice',
            'Decision Making',
            'Time Management',
            'Learning & Development',
            'Problem Solving',
            'Confidence & Self-Doubt',
            'Relationships & Communication',
            'Goal Setting',
        ]
        
        for cat_name in category_names:
            cat, created = QuestionCategory.objects.get_or_create(name=cat_name)
            categories[cat_name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created category: {cat_name}'))
        
        # Sample Q&A data
        qa_data = [
            {
                'category': 'Career Advice',
                'questions': [
                    {
                        'text': 'How should I approach a career transition?',
                        'keywords': ['career', 'transition', 'change', 'new job'],
                        'answers': [
                            {
                                'text': 'Career transitions require strategic planning:\n\n1. **Financial Readiness**: Save 6-12 months expenses\n2. **Skill Gap Analysis**: Identify what to learn\n3. **Network Building**: Start connecting in your target field\n4. **Timing**: Plan smooth handover\n5. **Learning Path**: Take relevant courses\n\nMake the transition when 70% ready—perfect readiness rarely exists.',
                                'reasoning': 'Career transition strategy',
                                'confidence': 0.85
                            },
                            {
                                'text': 'Start with self-assessment: What are your strengths? What do you want to do? Then research the market, network with people in that field, and create a 6-12 month transition plan. Consider taking courses or certifications to fill gaps.',
                                'reasoning': 'Practical transition steps',
                                'confidence': 0.80
                            }
                        ]
                    },
                    {
                        'text': 'What should I do to advance in my career?',
                        'keywords': ['advancement', 'promotion', 'career growth', 'progress'],
                        'answers': [
                            {
                                'text': 'For career advancement:\n\n• **Develop both technical AND soft skills**\n• **Lead visible projects** that increase your impact\n• **Seek regular feedback** from supervisors\n• **Build relationships** across levels and departments\n• **Document achievements** with quantifiable results\n• **Find a sponsor** (not just mentor) who advocates for you\n\nAdvancement is as much about visibility as capability.',
                                'reasoning': 'Career advancement framework',
                                'confidence': 0.88
                            },
                            {
                                'text': 'Focus on building expertise in your domain while also developing leadership skills. Take on challenging projects, mentor others, and make your contributions visible to decision-makers. Request feedback regularly.',
                                'reasoning': 'Core advancement principles',
                                'confidence': 0.82
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Decision Making',
                'questions': [
                    {
                        'text': 'How do I make better decisions?',
                        'keywords': ['decision', 'choose', 'option', 'decision making'],
                        'answers': [
                            {
                                'text': 'Use a systematic approach:\n\n1. **Define clearly** - What exactly are you deciding?\n2. **Identify options** - Generate 3-5 viable choices\n3. **List criteria** - What matters for this decision?\n4. **Evaluate each** - Pros, cons, consequences\n5. **Seek input** - Talk to experienced people\n6. **Trust your judgment** - You have good instincts\n\nUse the 10-10-10 rule: How will you feel in 10 minutes, 10 months, 10 years?',
                                'reasoning': 'Systematic decision framework',
                                'confidence': 0.87
                            }
                        ]
                    },
                    {
                        'text': 'How do I decide between multiple options?',
                        'keywords': ['choose between', 'compare options', 'which option'],
                        'answers': [
                            {
                                'text': 'Try a Decision Matrix:\n\n1. List options across columns\n2. List important criteria down rows\n3. Weight each criterion (1-5)\n4. Score each option (1-5)\n5. Calculate weighted totals\n\nThis quantifies comparison and reduces emotional bias. Look for patterns in which options emerge strongest.',
                                'reasoning': 'Decision matrix methodology',
                                'confidence': 0.83
                            }
                        ]
                    },
                    {
                        'text': 'What should I do when facing uncertainty?',
                        'keywords': ['uncertainty', 'uncertain', 'risk', 'unsure'],
                        'answers': [
                            {
                                'text': 'Use scenario planning:\n\nCreate three scenarios:\n• **Best-case**: What goes right?\n• **Worst-case**: What could go wrong?\n• **Most-likely**: What probably happens?\n\nAsk: "Can I live with the worst-case outcome?"\nIf yes and upside justifies risk, move forward.\nIf no, find ways to reduce that risk.',
                                'reasoning': 'Scenario-based approach',
                                'confidence': 0.84
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Time Management',
                'questions': [
                    {
                        'text': 'How should I prioritize my tasks?',
                        'keywords': ['priority', 'prioritize', 'urgent', 'important'],
                        'answers': [
                            {
                                'text': 'Use the Eisenhower Matrix:\n\n• **Urgent + Important** → Do immediately\n• **Not Urgent + Important** → Schedule and protect\n• **Urgent + Not Important** → Delegate\n• **Not Urgent + Not Important** → Eliminate\n\nMost people spend too much time on Urgent tasks and too little on Important ones. Focus on preventing crises, not just reacting.',
                                'reasoning': 'Priority matrix methodology',
                                'confidence': 0.89
                            }
                        ]
                    },
                    {
                        'text': 'How can I be more productive with limited time?',
                        'keywords': ['productive', 'productivity', 'time management', 'efficiency'],
                        'answers': [
                            {
                                'text': 'Apply the 80/20 principle:\n\n• Identify which 20% of activities produce 80% of results\n• Double down on high-impact activities\n• Learn to say "no" to good opportunities that don\'t align\n• Automate, delegate, or eliminate the rest\n\nYour time is finite—invest it in what truly matters.',
                                'reasoning': 'Pareto principle application',
                                'confidence': 0.85
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Learning & Development',
                'questions': [
                    {
                        'text': 'What\'s the best way to learn something new?',
                        'keywords': ['learn', 'learning', 'study', 'education', 'how to learn'],
                        'answers': [
                            {
                                'text': 'Evidence-based learning strategies:\n\n1. **Understand fundamentals** - Don\'t skip basics\n2. **Active practice** - Build projects, solve problems\n3. **Teach others** - Explaining reveals gaps\n4. **Spaced repetition** - Review at increasing intervals\n5. **Seek feedback** - Understand what you\'re missing\n6. **Set milestones** - Celebrate small wins\n\nProgress matters more than speed.',
                                'reasoning': 'Evidence-based strategies',
                                'confidence': 0.86
                            }
                        ]
                    },
                    {
                        'text': 'How do I improve my technical skills?',
                        'keywords': ['skill development', 'technical skills', 'improve skills'],
                        'answers': [
                            {
                                'text': 'Use the Feynman Technique:\n\n1. Choose a concept\n2. Explain it simply as if teaching a beginner\n3. Identify gaps where you struggled\n4. Simplify and refine your explanation\n\nCombine with: deliberate practice, project-based learning, and finding a community. This reveals what you truly understand vs. memorized.',
                                'reasoning': 'Deep learning methodology',
                                'confidence': 0.82
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Problem Solving',
                'questions': [
                    {
                        'text': 'How do I solve a difficult problem?',
                        'keywords': ['problem', 'solve', 'stuck', 'difficult', 'challenge'],
                        'answers': [
                            {
                                'text': 'Systematic problem-solving:\n\n1. **Define clearly** - What\'s the actual problem?\n2. **Gather info** - What data do you need?\n3. **Break into parts** - Decompose into pieces\n4. **Brainstorm solutions** - No judgment at first\n5. **Evaluate each** - Pros, cons, feasibility\n6. **Test solution** - Start small before full rollout\n\nGetting the problem definition right is crucial.',
                                'reasoning': 'Structured approach',
                                'confidence': 0.84
                            }
                        ]
                    },
                    {
                        'text': 'What should I do when I\'m stuck on a problem?',
                        'keywords': ['stuck', 'blocked', 'can\'t solve', 'help with problem'],
                        'answers': [
                            {
                                'text': '**When stuck, try these**:\n\n• **Change perspective** - View it differently\n• **Sleep on it** - Subconscious continues working\n• **Explain to others** - External view reveals blind spots\n• **Root cause analysis** - Ask "why?" 5 times\n• **Constraints thinking** - What if you had half the resources?\n\nOften the best solutions come from constraints.',
                                'reasoning': 'Alternative problem-solving',
                                'confidence': 0.78
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Goal Setting',
                'questions': [
                    {
                        'text': 'How do I set effective goals?',
                        'keywords': ['goal', 'goals', 'objective', 'target', 'goal setting'],
                        'answers': [
                            {
                                'text': 'Use the SMART framework:\n\n• **Specific** - Clear and well-defined\n• **Measurable** - Concrete metrics\n• **Achievable** - Challenging but realistic\n• **Relevant** - Aligned with bigger purpose\n• **Time-bound** - Clear deadline\n\nExample: Instead of "Get better at coding", try "Complete 50 LeetCode problems and 3 real projects by June 30".\n\nClear goals create clarity and focus.',
                                'reasoning': 'SMART goal framework',
                                'confidence': 0.87
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Confidence & Self-Doubt',
                'questions': [
                    {
                        'text': 'How do I build more confidence?',
                        'keywords': ['confidence', 'self-confidence', 'confident', 'doubt'],
                        'answers': [
                            {
                                'text': 'Confidence comes from:\n\n• **Competence** - Building relevant skills\n• **Experience** - Putting yourself out there\n\n**Action steps**:\n1. Start with small challenges you can win\n2. Build one skill addressing your doubt\n3. Use that skill in progressively bigger situations\n4. Track your successes\n\nConfidence is built, not found. Each small win compounds.',
                                'reasoning': 'Confidence building approach',
                                'confidence': 0.83
                            }
                        ]
                    },
                    {
                        'text': 'How do I deal with imposter syndrome?',
                        'keywords': ['imposter', 'imposter syndrome', 'not good enough', 'self doubt'],
                        'answers': [
                            {
                                'text': '**Understand imposter syndrome**:\n\n• Doubt is normal—even experts feel it\n• You know LESS than you think (keeping learning)\n• But also MORE than you realize\n• Focus on growth, not perfection\n\n**Reframe your thinking**:\n"I\'m learning and improving" (not just unprepared)\n"Everyone started where I am" (not uniquely behind)\n"I\'ll learn from whatever happens" (not destined to fail)\n\nThe only real failure is not trying.',
                                'reasoning': 'Self-doubt management',
                                'confidence': 0.80
                            }
                        ]
                    }
                ]
            }
        ]
        
        # Populate questions and answers
        for category_data in qa_data:
            category = categories[category_data['category']]
            
            for q_data in category_data['questions']:
                question, q_created = Question.objects.get_or_create(
                    question_text=q_data['text'],
                    category=category,
                    defaults={'keywords': q_data['keywords']}
                )
                
                if q_created:
                    self.stdout.write(f'  ✓ Created question: {q_data["text"][:50]}...')
                
                # Create answers
                for a_idx, a_data in enumerate(q_data['answers']):
                    answer, a_created = Answer.objects.get_or_create(
                        question=question,
                        answer_text=a_data['text'],
                        defaults={
                            'reasoning': a_data.get('reasoning', ''),
                            'confidence': a_data.get('confidence', 0.8),
                        }
                    )
                    
                    if a_created:
                        self.stdout.write(f'    ✓ Created answer {a_idx + 1}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Q&A database populated successfully!'))
        self.stdout.write(self.style.WARNING(
            '\nNext steps:\n'
            '1. Visit /admin/recommendations/question/ to view and manage questions\n'
            '2. Visit /recommendations/qa/dashboard/ to see the Q&A management dashboard\n'
            '3. Add more questions and answers as needed\n'
            '4. Test the AI service with new questions\n'
        ))
