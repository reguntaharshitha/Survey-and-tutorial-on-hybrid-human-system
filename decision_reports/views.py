from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
import json
import uuid
from datetime import datetime
from .models import DecisionReport, CriticalNotice

@login_required
def report_dashboard(request):
    reports = DecisionReport.objects.filter(user=request.user).order_by('-created_at')
    critical_notices = CriticalNotice.objects.filter(
        report__user=request.user,
        priority__in=['high', 'critical']
    ).order_by('-created_at')[:5]
    
    return render(request, 'decision_reports/dashboard.html', {
        'reports': reports,
        'critical_notices': critical_notices
    })

@login_required
def report_detail(request, report_id):
    report = get_object_or_404(DecisionReport, id=report_id, user=request.user)
    
    # Prepare chart data
    chart_data = {
        'confidence_scores': report.confidence_scores,
        'insights': report.insights,
        'recommendations': report.recommendations
    }
    
    return render(request, 'decision_reports/report_detail.html', {
        'report': report,
        'chart_data': json.dumps(chart_data)
    })

@login_required
def generate_sample_report(request):
    """Generate a unique sample report for the user"""
    try:
        # Generate unique report ID using timestamp and random component
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        report_id = f"RPT-{request.user.id}-{timestamp}-{unique_id}"
        
        # Check if report with this ID already exists (very unlikely but safe)
        if DecisionReport.objects.filter(report_id=report_id).exists():
            # If by some chance it exists, generate another one
            unique_id = str(uuid.uuid4())[:8]
            report_id = f"RPT-{request.user.id}-{timestamp}-{unique_id}"
        
        # Sample report templates
        report_templates = [
            {
                "title": "Behavioral Pattern Analysis Report",
                "summary": "Analysis of your decision-making patterns and behavioral tendencies based on recent interactions.",
                "insights": {
                    "pattern_consistency": 0.85,
                    "decision_confidence": 0.72,
                    "learning_velocity": 0.63,
                    "adaptability_score": 0.78
                },
                "confidence_scores": {
                    "overall": 0.82,
                    "behavioral": 0.75,
                    "cognitive": 0.88,
                    "emotional": 0.71
                }
            },
            {
                "title": "Cognitive Style Assessment Report", 
                "summary": "Evaluation of your cognitive processing style and thinking patterns.",
                "insights": {
                    "analytical_thinking": 0.79,
                    "intuitive_decision": 0.68,
                    "information_processing": 0.83,
                    "problem_solving": 0.76
                },
                "confidence_scores": {
                    "overall": 0.81,
                    "analytical": 0.84,
                    "creative": 0.73,
                    "practical": 0.79
                }
            },
            {
                "title": "Learning & Development Report",
                "summary": "Analysis of your learning patterns and skill development opportunities.",
                "insights": {
                    "knowledge_acquisition": 0.77,
                    "skill_application": 0.69,
                    "adaptive_learning": 0.82,
                    "retention_rate": 0.74
                },
                "confidence_scores": {
                    "overall": 0.78,
                    "theoretical": 0.81,
                    "practical": 0.72,
                    "collaborative": 0.79
                }
            }
        ]
        
        # Select a random template or cycle through them
        import random
        template = random.choice(report_templates)
        
        # Create the report
        report = DecisionReport.objects.create(
            user=request.user,
            report_id=report_id,
            title=template["title"],
            summary=template["summary"],
            insights=template["insights"],
            recommendations=[
                {"type": "behavioral", "action": "Practice divergent thinking exercises", "priority": "medium", "confidence": 0.76},
                {"type": "learning", "action": "Review past successful decisions for patterns", "priority": "high", "confidence": 0.82},
                {"type": "interaction", "action": "Increase feedback solicitation frequency", "priority": "medium", "confidence": 0.71}
            ],
            confidence_scores=template["confidence_scores"],
            visual_data={
                "chart_type": "radar",
                "labels": list(template["insights"].keys()),
                "data": list(template["insights"].values()),
                "colors": ["#3498db", "#2ecc71", "#e74c3c", "#f39c12"]
            },
            is_critical=random.choice([True, False])
        )
        
        # Randomly add a critical notice (30% chance)
        if random.random() < 0.3:
            notice_types = [
                ("High Decision Variability", "medium", "Detected significant variability in decision-making approaches. Consider establishing more consistent evaluation criteria."),
                ("Learning Pattern Shift", "low", "Recent changes in learning patterns detected. This may indicate adaptation or potential confusion."),
                ("Trust Score Fluctuation", "high", "Significant changes in trust metrics observed. Review recent interactions for potential causes.")
            ]
            
            notice_type, priority, message = random.choice(notice_types)
            
            CriticalNotice.objects.create(
                report=report,
                notice_type=notice_type,
                priority=priority,
                message=message,
                suggested_actions=[
                    "Implement structured decision matrix",
                    "Document decision rationale systematically", 
                    "Review past successful decisions for patterns"
                ]
            )
        
        messages.success(request, f'Sample report "{report.title}" generated successfully!')
        return redirect('report_detail', report_id=report.id)
        
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('report_dashboard')

@login_required
def critical_notices(request):
    notices = CriticalNotice.objects.filter(
        report__user=request.user
    ).order_by('-created_at')
    
    return render(request, 'decision_reports/critical_notices.html', {'notices': notices})