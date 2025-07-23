from typing import Dict, List, Any
from datetime import datetime
import pandas as pd

class CalendarWorkflow:
    """Calendar analysis workflow"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def analyze_daily_schedule(self, events: List[Dict], config) -> Dict:
        """Analyze daily schedule and provide insights"""
        
        if not events:
            return {
                "summary": "No meetings scheduled - great day for focused work!",
                "schedule_health": "excellent",
                "focus_time_opportunities": [],
                "meeting_prep": [],
                "recommendations": ["Block time for deep work"]
            }
        
        # Calculate meeting statistics
        total_meeting_time = 0
        meeting_events = [e for e in events if not e.get('agent_generated', False)]
        
        for event in meeting_events:
            try:
                start_time = datetime.fromisoformat(event["start_time"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(event["end_time"].replace('Z', '+00:00'))
                duration_hours = (end_time - start_time).total_seconds() / 3600
                total_meeting_time += duration_hours
            except:
                total_meeting_time += 0.5  # Default 30 min
        
        # Analyze schedule health
        if len(meeting_events) > 6 or total_meeting_time > 5:
            schedule_health = "overloaded"
        elif len(meeting_events) > 4 or total_meeting_time > 3:
            schedule_health = "busy"
        elif len(meeting_events) < 2:
            schedule_health = "light"
        else:
            schedule_health = "balanced"
        
        # Find focus time opportunities
        focus_opportunities = []
        focus_blocks = [e for e in events if e.get('event_type') == 'focus_block']
        for block in focus_blocks:
            focus_opportunities.append({
                'start_time': block['start_time'],
                'duration': block.get('duration_hours', 1) * 60,
                'recommendation': 'Deep work session'
            })
        
        # Generate meeting prep items
        meeting_prep = []
        for event in meeting_events:
            if event.get('agent_importance_score', 0) > 0.7:
                meeting_prep.append({
                    'event_title': event['title'],
                    'prep_time': event.get('agent_prep_time_estimate', 15),
                    'prep_items': event.get('agent_prep_items', ['Review agenda'])
                })
        
        return {
            "summary": f"Schedule health: {schedule_health}. {len(meeting_events)} meetings, {total_meeting_time:.1f}h total",
            "schedule_health": schedule_health,
            "total_meetings": len(meeting_events),
            "total_meeting_time": total_meeting_time,
            "focus_time_opportunities": focus_opportunities,
            "meeting_prep": meeting_prep,
            "recommendations": self._generate_recommendations(schedule_health, meeting_events, focus_opportunities)
        }
    
    def _generate_recommendations(self, health: str, meetings: List[Dict], focus_ops: List[Dict]) -> List[str]:
        """Generate schedule recommendations"""
        recommendations = []
        
        if health == "overloaded":
            recommendations.append("Consider rescheduling non-critical meetings")
            recommendations.append("Block buffer time between meetings")
        elif health == "light":
            recommendations.append("Good day for tackling complex projects")
            recommendations.append("Consider scheduling important one-on-ones")
        
        if len(focus_ops) == 0:
            recommendations.append("Try to block at least one hour for focused work")
        
        return recommendations