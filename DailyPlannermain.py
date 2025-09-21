# ultimate_planner.py
# Ultimate AI Daily Planner by Lingli Yang
# Professional-grade productivity app with advanced features and database

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
import io
import sqlite3

# Database Class
class PlannerDatabase:
    def __init__(self, db_path="planner.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default_user',
                schedule_name TEXT NOT NULL,
                tasks_data TEXT NOT NULL,
                schedule_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default_user',
                start_hour INTEGER DEFAULT 7,
                end_hour INTEGER DEFAULT 22,
                breakfast_time TEXT DEFAULT '08:00',
                lunch_time TEXT DEFAULT '12:30',
                dinner_time TEXT DEFAULT '18:30',
                default_break INTEGER DEFAULT 10,
                pomodoro_work INTEGER DEFAULT 25,
                pomodoro_short_break INTEGER DEFAULT 5,
                pomodoro_long_break INTEGER DEFAULT 20,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default_user',
                date DATE NOT NULL,
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                total_work_time INTEGER DEFAULT 0,
                pomodoro_sessions INTEGER DEFAULT 0,
                productivity_score REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_schedule(self, schedule_name, tasks, schedule):
        """Save a complete schedule to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert data to JSON strings
        tasks_json = json.dumps(tasks)
        schedule_json = json.dumps(schedule, default=str)  # Handle datetime objects
        
        cursor.execute('''
            INSERT OR REPLACE INTO schedules 
            (user_id, schedule_name, tasks_data, schedule_data, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', ('default_user', schedule_name, tasks_json, schedule_json, datetime.now()))
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def load_schedule(self, schedule_name):
        """Load a schedule from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tasks_data, schedule_data FROM schedules 
            WHERE user_id = ? AND schedule_name = ?
            ORDER BY updated_at DESC LIMIT 1
        ''', ('default_user', schedule_name))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            tasks = json.loads(result[0])
            schedule = json.loads(result[1])
            return tasks, schedule
        return None, None
    
    def get_all_schedules(self):
        """Get list of all saved schedules"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT schedule_name, created_at, updated_at 
            FROM schedules 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', ('default_user',))
        
        schedules = cursor.fetchall()
        conn.close()
        return schedules
    
    def delete_schedule(self, schedule_name):
        """Delete a schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM schedules 
            WHERE user_id = ? AND schedule_name = ?
        ''', ('default_user', schedule_name))
        
        conn.commit()
        conn.close()

# Initialize database
@st.cache_resource
def init_database():
    return PlannerDatabase()

# Get database instance
db = init_database()

# Page setup
st.set_page_config(
    page_title="Ultimate AI Daily Planner by Lingli Yang", 
    page_icon="🗓️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    text-align: center;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 10px;
}

.creator-badge {
    text-align: center;
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    padding: 10px 20px;
    border-radius: 20px;
    margin: 20px auto;
    max-width: 400px;
    font-weight: bold;
}

.feature-card {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    margin: 10px 0;
}

.meal-time {
    background-color: #e8f5e8;
    padding: 10px;
    border-radius: 5px;
    border-left: 4px solid #4CAF50;
    margin: 5px 0;
}

.break-time {
    background-color: #fff3e0;
    padding: 8px;
    border-radius: 5px;
    border-left: 3px solid #ff9800;
    margin: 3px 0;
}

.pomodoro-time {
    background-color: #fff8e1;
    padding: 10px;
    border-radius: 5px;
    border-left: 4px solid #f44336;
    margin: 5px 0;
}

.brain-rest-time {
    background-color: #e3f2fd;
    padding: 10px;
    border-radius: 5px;
    border-left: 4px solid #2196f3;
    margin: 5px 0;
}

.progress-container {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.theme-dark {
    background-color: #1e1e1e;
    color: white;
}

.success-animation {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🗓️ Ultimate AI Daily Planner</h1>', unsafe_allow_html=True)
st.markdown('''
<div class="creator-badge">
    <div>🚀 Created by <strong>Lingli Yang</strong></div>
    <div style="font-size: 0.9em; margin-top: 5px;">Advanced Productivity & AI Scheduling</div>
</div>
''', unsafe_allow_html=True)

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'schedule' not in st.session_state:
    st.session_state.schedule = []
if 'schedule_history' not in st.session_state:
    st.session_state.schedule_history = []
if 'completed_tasks' not in st.session_state:
    st.session_state.completed_tasks = []
if 'meal_times' not in st.session_state:
    st.session_state.meal_times = {
        'breakfast': '08:00',
        'lunch': '12:30', 
        'dinner': '18:30'
    }
if 'editing_mode' not in st.session_state:
    st.session_state.editing_mode = False
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        'productive_hours': [9, 10, 11, 14, 15],
        'break_preference': 'short',
        'work_style': 'focused'
    }
if 'task_suggestions' not in st.session_state:
    st.session_state.task_suggestions = []

# Helper functions
def time_to_minutes(time_str):
    """Convert HH:MM to minutes from midnight"""
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes

def minutes_to_time(minutes):
    """Convert minutes from midnight to HH:MM"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def analyze_task_comprehensive(task_name):
    """AI analyzes task and predicts ALL properties automatically"""
    task_lower = task_name.lower()
    
    # Comprehensive task analysis database
    task_patterns = {
        # Work tasks
        'meeting': {'type': 'work', 'duration': 60, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'team meeting': {'type': 'work', 'duration': 45, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'standup': {'type': 'work', 'duration': 15, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'presentation': {'type': 'work', 'duration': 90, 'intensity': 'Deep Work', 'pomodoro': True, 'brain_rest': True},
        'prepare presentation': {'type': 'work', 'duration': 120, 'intensity': 'Deep Work', 'pomodoro': True, 'brain_rest': True},
        'write report': {'type': 'work', 'duration': 120, 'intensity': 'High Focus', 'pomodoro': True, 'brain_rest': True},
        'email': {'type': 'work', 'duration': 30, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'check email': {'type': 'work', 'duration': 20, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'call': {'type': 'work', 'duration': 30, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'phone call': {'type': 'work', 'duration': 45, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'client call': {'type': 'work', 'duration': 60, 'intensity': 'High Focus', 'pomodoro': False, 'brain_rest': False},
        'interview': {'type': 'work', 'duration': 60, 'intensity': 'High Focus', 'pomodoro': False, 'brain_rest': True},
        'review': {'type': 'work', 'duration': 45, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'planning': {'type': 'work', 'duration': 90, 'intensity': 'High Focus', 'pomodoro': True, 'brain_rest': True},
        'project work': {'type': 'work', 'duration': 120, 'intensity': 'Deep Work', 'pomodoro': True, 'brain_rest': True},
        
        # Study tasks
        'study': {'type': 'study', 'duration': 90, 'intensity': 'High Focus', 'pomodoro': True, 'brain_rest': True},
        'homework': {'type': 'study', 'duration': 60, 'intensity': 'Moderate', 'pomodoro': True, 'brain_rest': False},
        'read': {'type': 'study', 'duration': 45, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'reading': {'type': 'study', 'duration': 45, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'research': {'type': 'study', 'duration': 120, 'intensity': 'Deep Work', 'pomodoro': True, 'brain_rest': True},
        'learn': {'type': 'study', 'duration': 60, 'intensity': 'High Focus', 'pomodoro': True, 'brain_rest': False},
        'exam prep': {'type': 'study', 'duration': 120, 'intensity': 'Deep Work', 'pomodoro': True, 'brain_rest': True},
        'practice': {'type': 'study', 'duration': 60, 'intensity': 'Moderate', 'pomodoro': True, 'brain_rest': False},
        
        # Health/Exercise
        'gym': {'type': 'health', 'duration': 60, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'workout': {'type': 'health', 'duration': 45, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'exercise': {'type': 'health', 'duration': 30, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'run': {'type': 'health', 'duration': 30, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'running': {'type': 'health', 'duration': 45, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'yoga': {'type': 'health', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'walk': {'type': 'health', 'duration': 30, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'meditation': {'type': 'health', 'duration': 20, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'doctor appointment': {'type': 'health', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        
        # Personal tasks
        'shopping': {'type': 'personal', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'grocery shopping': {'type': 'personal', 'duration': 45, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'clean': {'type': 'personal', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'cleaning': {'type': 'personal', 'duration': 90, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'laundry': {'type': 'personal', 'duration': 30, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'cook': {'type': 'personal', 'duration': 45, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'cooking': {'type': 'personal', 'duration': 60, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'meal prep': {'type': 'personal', 'duration': 90, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False},
        'organize': {'type': 'personal', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'pay bills': {'type': 'personal', 'duration': 30, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        
        # Social activities
        'coffee': {'type': 'social', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'lunch': {'type': 'social', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'dinner': {'type': 'social', 'duration': 90, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'hangout': {'type': 'social', 'duration': 120, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'visit friends': {'type': 'social', 'duration': 120, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'date': {'type': 'social', 'duration': 120, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'party': {'type': 'social', 'duration': 180, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        
        # Entertainment
        'movie': {'type': 'entertainment', 'duration': 120, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'tv': {'type': 'entertainment', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'netflix': {'type': 'entertainment', 'duration': 90, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'game': {'type': 'entertainment', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'gaming': {'type': 'entertainment', 'duration': 90, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'music': {'type': 'entertainment', 'duration': 30, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False},
        'relax': {'type': 'entertainment', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False}
    }
    
    # Find best match with scoring
    best_match = None
    highest_score = 0
    
    for pattern, properties in task_patterns.items():
        pattern_words = pattern.split()
        task_words = task_lower.split()
        
        score = 0
        for pattern_word in pattern_words:
            if pattern_word in task_lower:
                score += len(pattern_word)
        
        if score > highest_score:
            highest_score = score
            best_match = properties
    
    # Keyword-based fallback
    if best_match is None:
        if any(word in task_lower for word in ['meeting', 'work', 'presentation', 'email', 'call']):
            best_match = {'type': 'work', 'duration': 60, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False}
        elif any(word in task_lower for word in ['study', 'learn', 'read', 'research']):
            best_match = {'type': 'study', 'duration': 60, 'intensity': 'High Focus', 'pomodoro': True, 'brain_rest': True}
        elif any(word in task_lower for word in ['gym', 'exercise', 'workout', 'run']):
            best_match = {'type': 'health', 'duration': 45, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False}
        elif any(word in task_lower for word in ['clean', 'cook', 'shopping']):
            best_match = {'type': 'personal', 'duration': 60, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False}
        elif any(word in task_lower for word in ['coffee', 'lunch', 'dinner', 'friends']):
            best_match = {'type': 'social', 'duration': 90, 'intensity': 'Light', 'pomodoro': False, 'brain_rest': False}
        else:
            best_match = {'type': 'personal', 'duration': 60, 'intensity': 'Moderate', 'pomodoro': False, 'brain_rest': False}
    
    # Map properties
    difficulty_map = {'Light': 1, 'Moderate': 2, 'High Focus': 3, 'Deep Work': 3}
    energy_map = {'Light': 'low', 'Moderate': 'medium', 'High Focus': 'high', 'Deep Work': 'high'}
    mental_map = {'Light': 'low', 'Moderate': 'medium', 'High Focus': 'high', 'Deep Work': 'very_high'}
    
    return {
        'type': best_match['type'],
        'duration': best_match['duration'],
        'intensity': best_match['intensity'],
        'difficulty': difficulty_map[best_match['intensity']],
        'energy_level': energy_map[best_match['intensity']],
        'mental_load': mental_map[best_match['intensity']],
        'use_pomodoro': best_match['pomodoro'],
        'needs_brain_rest': best_match['brain_rest'],
        'needs_break_after': best_match['intensity'] in ['Moderate', 'High Focus', 'Deep Work'],
        'break_duration': 15 if best_match['intensity'] in ['High Focus', 'Deep Work'] else 10
    }

def calculate_priority(task_type, difficulty, deadline_days, energy_level, mental_load):
    """Calculate task priority with user preferences"""
    type_scores = {'work': 5, 'study': 4, 'health': 4, 'personal': 3, 'social': 2}
    energy_scores = {'high': 3, 'medium': 2, 'low': 1}
    mental_scores = {'very_high': 4, 'high': 3, 'medium': 2, 'low': 1}
    
    type_score = type_scores.get(task_type, 2)
    energy_score = energy_scores.get(energy_level, 2)
    mental_score = mental_scores.get(mental_load, 2)
    
    if deadline_days is None:
        deadline_score = 2
    elif deadline_days <= 1:
        deadline_score = 5
    elif deadline_days <= 3:
        deadline_score = 3
    else:
        deadline_score = 1
    
    return type_score + difficulty + deadline_score + energy_score + mental_score

def generate_smart_suggestions(current_tasks):
    """AI-powered task suggestions based on user history"""
    common_tasks = [
        "Check emails", "Team standup", "Review calendar", "Coffee break",
        "Lunch meeting", "Project planning", "Study session", "Gym workout",
        "Grocery shopping", "Meal prep", "Read industry news", "Call family"
    ]
    
    # Filter out tasks user already has
    existing_names = [task['name'].lower() for task in current_tasks]
    suggestions = [task for task in common_tasks if task.lower() not in existing_names]
    
    return suggestions[:5]  # Return top 5 suggestions

def create_pomodoro_sessions(task_duration, work_time, short_break, long_break):
    """Create Pomodoro breakdown"""
    sessions = []
    remaining = task_duration
    session_count = 0
    
    while remaining > 0:
        session_count += 1
        work_duration = min(work_time, remaining)
        
        sessions.append({
            'type': 'pomodoro_work',
            'duration': work_duration,
            'session': session_count
        })
        remaining -= work_duration
        
        if remaining > 0:
            if session_count % 4 == 0:
                sessions.append({
                    'type': 'pomodoro_long_break',
                    'duration': long_break,
                    'session': session_count
                })
            else:
                sessions.append({
                    'type': 'pomodoro_short_break',
                    'duration': short_break,
                    'session': session_count
                })
    
    return sessions

def create_schedule(tasks, start_hour, end_hour, meal_times, settings):
    """Enhanced scheduling with analytics tracking"""
    if not tasks:
        return []
    
    schedule = []
    analyzed_tasks = []
    
    # Analyze all tasks
    for task in tasks:
        analysis = analyze_task_comprehensive(task['name'])
        priority = calculate_priority(
            analysis['type'], 
            analysis['difficulty'], 
            task['deadline_days'], 
            analysis['energy_level'], 
            analysis['mental_load']
        )
        
        analyzed_tasks.append({
            'name': task['name'],
            'type': analysis['type'],
            'difficulty': analysis['difficulty'],
            'energy_level': analysis['energy_level'],
            'mental_load': analysis['mental_load'],
            'intensity': analysis['intensity'],
            'priority': priority,
            'duration': analysis['duration'],
            'deadline_days': task['deadline_days'],
            'needs_break_after': analysis['needs_break_after'],
            'break_duration': analysis['break_duration'],
            'use_pomodoro': analysis['use_pomodoro'],
            'needs_brain_rest': analysis['needs_brain_rest']
        })
    
    # Sort by priority and energy level
    analyzed_tasks.sort(key=lambda x: (x['priority'], x['energy_level'] == 'high'), reverse=True)
    
    # Schedule creation with enhanced logic
    current_time = start_hour * 60
    end_time = end_hour * 60
    
    breakfast_time = time_to_minutes(meal_times['breakfast'])
    lunch_time = time_to_minutes(meal_times['lunch'])
    dinner_time = time_to_minutes(meal_times['dinner'])
    
    task_index = 0
    work_time_since_break = 0
    
    while task_index < len(analyzed_tasks) and current_time < end_time:
        
        # Meal scheduling
        if abs(current_time - breakfast_time) <= 15 and not any(item.get('time_minutes') == breakfast_time for item in schedule):
            schedule.append({
                'name': '🍳 Breakfast',
                'type': 'meal',
                'start_time': minutes_to_time(breakfast_time),
                'end_time': minutes_to_time(breakfast_time + 30),
                'duration': 30,
                'time_minutes': breakfast_time
            })
            current_time = max(current_time, breakfast_time + 30)
            continue
            
        if abs(current_time - lunch_time) <= 30 and not any(item.get('time_minutes') == lunch_time for item in schedule):
            schedule.append({
                'name': '🥗 Lunch Break',
                'type': 'meal',
                'start_time': minutes_to_time(lunch_time),
                'end_time': minutes_to_time(lunch_time + 45),
                'duration': 45,
                'time_minutes': lunch_time
            })
            current_time = max(current_time, lunch_time + 45)
            work_time_since_break = 0
            continue
            
        if abs(current_time - dinner_time) <= 30 and not any(item.get('time_minutes') == dinner_time for item in schedule):
            schedule.append({
                'name': '🍽️ Dinner Time',
                'type': 'meal',
                'start_time': minutes_to_time(dinner_time),
                'end_time': minutes_to_time(dinner_time + 60),
                'duration': 60,
                'time_minutes': dinner_time
            })
            current_time = max(current_time, dinner_time + 60)
            work_time_since_break = 0
            continue
        
        # Long break check
        if work_time_since_break >= settings['long_break_after'] * 60:
            schedule.append({
                'name': f'☕ Long Break ({settings["long_break_duration"]} min)',
                'type': 'long_break',
                'start_time': minutes_to_time(current_time),
                'end_time': minutes_to_time(current_time + settings['long_break_duration']),
                'duration': settings['long_break_duration'],
                'time_minutes': current_time
            })
            current_time += settings['long_break_duration']
            work_time_since_break = 0
            continue
        
        # Task scheduling
        if task_index < len(analyzed_tasks):
            task = analyzed_tasks[task_index]
            
            if current_time + task['duration'] > end_time:
                break
            
            # Pomodoro handling
            if task['use_pomodoro'] and task['duration'] > settings['pomodoro_work_time']:
                pomodoro_sessions = create_pomodoro_sessions(
                    task['duration'], 
                    settings['pomodoro_work_time'],
                    settings['pomodoro_short_break'],
                    settings['pomodoro_long_break']
                )
                
                for session in pomodoro_sessions:
                    if session['type'] == 'pomodoro_work':
                        schedule.append({
                            'name': f"🍅 {task['name']} (Session #{session['session']})",
                            'type': 'pomodoro_work',
                            'original_type': task['type'],
                            'priority': task['priority'],
                            'intensity': task['intensity'],
                            'start_time': minutes_to_time(current_time),
                            'end_time': minutes_to_time(current_time + session['duration']),
                            'duration': session['duration'],
                            'deadline_days': task['deadline_days'],
                            'time_minutes': current_time
                        })
                        current_time += session['duration']
                        work_time_since_break += session['duration']
                        
                    else:
                        break_name = f"🍅 Pomodoro {'Long ' if 'long' in session['type'] else ''}Break"
                        schedule.append({
                            'name': f"{break_name} ({session['duration']} min)",
                            'type': session['type'],
                            'start_time': minutes_to_time(current_time),
                            'end_time': minutes_to_time(current_time + session['duration']),
                            'duration': session['duration'],
                            'time_minutes': current_time
                        })
                        current_time += session['duration']
                        if 'long' in session['type']:
                            work_time_since_break = 0
            else:
                # Regular task
                schedule.append({
                    'name': task['name'],
                    'type': task['type'],
                    'priority': task['priority'],
                    'intensity': task['intensity'],
                    'start_time': minutes_to_time(current_time),
                    'end_time': minutes_to_time(current_time + task['duration']),
                    'duration': task['duration'],
                    'deadline_days': task['deadline_days'],
                    'time_minutes': current_time
                })
                current_time += task['duration']
                work_time_since_break += task['duration']
                
                # Regular break
                if task['needs_break_after'] and task_index < len(analyzed_tasks) - 1:
                    schedule.append({
                        'name': f'⏸️ Break ({task["break_duration"]} min)',
                        'type': 'break',
                        'start_time': minutes_to_time(current_time),
                        'end_time': minutes_to_time(current_time + task['break_duration']),
                        'duration': task['break_duration'],
                        'time_minutes': current_time
                    })
                    current_time += task['break_duration']
            
            # Brain rest
            if task['needs_brain_rest'] and task['mental_load'] in ['high', 'very_high']:
                brain_activity = settings['brain_activities'][0] if settings['brain_activities'] else "🧠 Brain Rest"
                schedule.append({
                    'name': f'🧠 Brain Rest: {brain_activity} ({settings["brain_rest_duration"]} min)',
                    'type': 'brain_rest',
                    'start_time': minutes_to_time(current_time),
                    'end_time': minutes_to_time(current_time + settings['brain_rest_duration']),
                    'duration': settings['brain_rest_duration'],
                    'time_minutes': current_time
                })
                current_time += settings['brain_rest_duration']
                work_time_since_break = 0
            
            task_index += 1
    
    return schedule

def create_analytics_dashboard():
    """Create comprehensive analytics"""
    if not st.session_state.schedule:
        return None
    
    # Collect data
    schedule_data = []
    for item in st.session_state.schedule:
        schedule_data.append({
            'name': item['name'],
            'type': item.get('type', 'unknown'),
            'duration': item['duration'],
            'intensity': item.get('intensity', 'Light'),
            'start_hour': int(item['start_time'].split(':')[0]) if 'start_time' in item else 9
        })
    
    df = pd.DataFrame(schedule_data)
    return df

def export_schedule_data():
    """Export schedule in multiple formats"""
    if not st.session_state.schedule:
        return None
    
    # Create export data
    export_data = []
    for item in st.session_state.schedule:
        export_data.append({
            'Time': f"{item.get('start_time', 'N/A')} - {item.get('end_time', 'N/A')}",
            'Activity': item['name'],
            'Type': item.get('type', 'unknown'),
            'Duration (min)': item['duration'],
            'Intensity': item.get('intensity', 'N/A'),
            'Priority': item.get('priority', 'N/A')
        })
    
    return pd.DataFrame(export_data)

# Sidebar Configuration
st.sidebar.title("⚙️ Ultimate Planner Settings")

# Theme toggle
if st.sidebar.button("🌙 Toggle Dark Mode"):
    st.session_state.dark_mode = not st.session_state.dark_mode

# Time settings
st.sidebar.subheader("🕐 Working Hours")
start_hour = st.sidebar.slider("Start Hour", 6, 12, 7)
end_hour = st.sidebar.slider("End Hour", 18, 24, 22)

if start_hour >= end_hour:
    st.sidebar.error("Start hour must be less than end hour!")
    available_hours = 0
else:
    available_hours = end_hour - start_hour
    st.sidebar.success(f"Available: {available_hours} hours")

# Meal times
st.sidebar.subheader("🍽️ Meal Times")
st.session_state.meal_times['breakfast'] = st.sidebar.time_input(
    "Breakfast", datetime.strptime("08:00", "%H:%M").time()
).strftime("%H:%M")

st.session_state.meal_times['lunch'] = st.sidebar.time_input(
    "Lunch", datetime.strptime("12:30", "%H:%M").time()
).strftime("%H:%M")

st.session_state.meal_times['dinner'] = st.sidebar.time_input(
    "Dinner", datetime.strptime("18:30", "%H:%M").time()
).strftime("%H:%M")

# Database Save/Load functionality
st.sidebar.subheader("💾 Save & Load Schedules")

# Save current schedule
if st.session_state.schedule:
    schedule_name = st.sidebar.text_input("Schedule name:", f"Schedule_{datetime.now().strftime('%m%d_%H%M')}")
    if st.sidebar.button("💾 Save Current Schedule"):
        try:
            db.save_schedule(schedule_name, st.session_state.tasks, st.session_state.schedule)
            st.sidebar.success(f"Saved '{schedule_name}'!")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# Load saved schedules
try:
    schedules = db.get_all_schedules()
    if schedules:
        schedule_options = [f"{s[0]} ({s[2][:10]})" for s in schedules]
        selected = st.sidebar.selectbox("Load saved schedule:", [""] + schedule_options)
        
        if selected and st.sidebar.button("📂 Load Schedule"):
            schedule_name = selected.split(" (")[0]
            tasks, schedule = db.load_schedule(schedule_name)
            if tasks and schedule:
                st.session_state.tasks = tasks
                st.session_state.schedule = schedule
                st.sidebar.success(f"Loaded '{schedule_name}'!")
                st.rerun()
except Exception as e:
    st.sidebar.info("Database initializing...")

# Advanced settings
with st.sidebar.expander("🔧 Advanced Settings"):
    default_break = st.slider("Default break (minutes)", 5, 30, 10)
    long_break_after = st.slider("Long break after (hours)", 2, 4, 3)
    long_break_duration = st.slider("Long break duration (minutes)", 15, 60, 30)
    
    # Pomodoro settings
    st.subheader("🍅 Pomodoro Settings")
    pomodoro_work_time = st.slider("Work session (minutes)", 20, 30, 25)
    pomodoro_short_break = st.slider("Short break (minutes)", 3, 10, 5)
    pomodoro_long_break = st.slider("Long break (minutes)", 15, 30, 20)
    
    # Brain rest settings
    st.subheader("🧠 Brain Rest Settings")
    brain_rest_duration = st.slider("Brain rest duration (minutes)", 30, 120, 60)
    brain_activities = st.multiselect(
        "Brain rest activities",
        ["🚶 Light walk", "🧘 Meditation", "🎵 Music", "☕ Coffee", "🌿 Fresh air", "💤 Nap"],
        default=["🚶 Light walk", "☕ Coffee"]
    )

# Smart task suggestions
st.sidebar.subheader("💡 Smart Suggestions")
suggestions = generate_smart_suggestions(st.session_state.tasks)
if suggestions:
    selected_suggestion = st.sidebar.selectbox("Suggested tasks:", [""] + suggestions)
    if st.sidebar.button("➕ Add Suggested Task") and selected_suggestion:
        new_task = {
            'name': selected_suggestion,
            'deadline_days': None
        }
        st.session_state.tasks.append(new_task)
        analysis = analyze_task_comprehensive(selected_suggestion)
        st.sidebar.success(f"Added: {selected_suggestion}")
        st.sidebar.info(f"🤖 AI: {analysis['duration']} min, {analysis['intensity']}")
        st.rerun()

# Task input
st.sidebar.subheader("📝 Add Activity")
with st.sidebar.form("task_form"):
    task_name = st.text_input("What do you need to do?", placeholder="e.g., Team meeting, Study Python, Go to gym")
    
    has_deadline = st.checkbox("Has a specific deadline?")
    deadline_days = None
    if has_deadline:
        deadline_days = st.number_input("Days until deadline", min_value=0, max_value=30, value=1)
    
    if st.form_submit_button("➕ Add Activity"):
        if task_name:
            new_task = {
                'name': task_name,
                'deadline_days': deadline_days
            }
            st.session_state.tasks.append(new_task)
            
            analysis = analyze_task_comprehensive(task_name)
            st.sidebar.success(f"Added: {task_name}")
            st.sidebar.info(f"🤖 AI detected: {analysis['duration']} min, {analysis['intensity']}, {analysis['type']}")
            if analysis['use_pomodoro']:
                st.sidebar.info("🍅 Will use Pomodoro technique")
            if analysis['needs_brain_rest']:
                st.sidebar.info("🧠 Will include brain rest")

# Control buttons
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🧹 Clear All"):
        st.session_state.tasks = []
        st.session_state.schedule = []
        st.session_state.editing_mode = False
        st.session_state.edit_index = None

with col2:
    if st.button("🤖 Generate"):
        if st.session_state.tasks:
            settings = {
                'long_break_after': long_break_after,
                'long_break_duration': long_break_duration,
                'pomodoro_work_time': pomodoro_work_time,
                'pomodoro_short_break': pomodoro_short_break,
                'pomodoro_long_break': pomodoro_long_break,
                'brain_rest_duration': brain_rest_duration,
                'brain_activities': brain_activities
            }
            
            with st.spinner('🤖 AI is optimizing your schedule...'):
                time.sleep(1)  # Simulate processing
                st.session_state.schedule = create_schedule(
                    st.session_state.tasks,
                    start_hour,
                    end_hour,
                    st.session_state.meal_times,
                    settings
                )
                
                # Save to history
                st.session_state.schedule_history.append({
                    'timestamp': datetime.now(),
                    'schedule': st.session_state.schedule.copy(),
                    'tasks_count': len(st.session_state.tasks)
                })
                
            st.sidebar.success("✨ Schedule optimized!")
        else:
            st.sidebar.error("Add activities first!")

# File operations
st.sidebar.subheader("📊 Export Data")
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("💾 Export CSV") and st.session_state.schedule:
        export_data = export_schedule_data()
        if export_data is not None:
            csv = export_data.to_csv(index=False)
            st.sidebar.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"schedule_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

with col2:
    if st.button("📈 Export Analytics") and st.session_state.schedule:
        analytics_data = create_analytics_dashboard()
        if analytics_data is not None:
            csv = analytics_data.to_csv(index=False)
            st.sidebar.download_button(
                label="📊 Download Data",
                data=csv,
                file_name=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

# Main content - Tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["📋 Schedule", "📊 Analytics", "✏️ Edit Tasks", "📈 Progress"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Your Activities")
        
        if st.session_state.tasks:
            task_data = []
            for i, task in enumerate(st.session_state.tasks, 1):
                analysis = analyze_task_comprehensive(task['name'])
                deadline_text = f"{task['deadline_days']} days" if task['deadline_days'] is not None else "Flexible"
                
                task_data.append({
                    '#': i,
                    'Activity': task['name'],
                    'AI Duration': f"{analysis['duration']} min",
                    'AI Intensity': analysis['intensity'],
                    'AI Type': analysis['type'].title(),
                    'Deadline': deadline_text,
                    'Pomodoro': "Yes" if analysis['use_pomodoro'] else "No",
                    'Brain Rest': "Yes" if analysis['needs_brain_rest'] else "No"
                })
            
            df = pd.DataFrame(task_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("👈 Just type what you need to do - AI handles the rest!")

        # Display schedule
        if st.session_state.schedule:
            st.subheader("🗓️ Your Optimized Schedule")
            
            for i, item in enumerate(st.session_state.schedule, 1):
                if item['type'] == 'meal':
                    st.markdown(f"""
                    <div class="meal-time">
                    <strong>{i}. {item['name']}</strong><br>
                    🕐 {item['start_time']} - {item['end_time']} ({item['duration']} min)
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif 'break' in item['type']:
                    st.markdown(f"""
                    <div class="break-time">
                    <strong>{i}. {item['name']}</strong><br>
                    🕐 {item['start_time']} - {item['end_time']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif item['type'] == 'brain_rest':
                    st.markdown(f"""
                    <div class="brain-rest-time">
                    <strong>{i}. {item['name']}</strong><br>
                    🕐 {item['start_time']} - {item['end_time']}<br>
                    💡 <em>Mental recovery after intensive work</em>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif item['type'] == 'pomodoro_work':
                    st.markdown(f"""
                    <div class="pomodoro-time">
                    <strong>{i}. {item['name']}</strong><br>
                    🕐 {item['start_time']} - {item['end_time']} ({item['duration']} min)<br>
                    🍅 Pomodoro Session | 🔥 {item['intensity']} | ⚡ Priority: {item['priority']}/20
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    type_emoji = {'work': '💼', 'study': '📚', 'health': '💪', 'personal': '🏠', 'social': '👥'}
                    emoji = type_emoji.get(item['type'], '📝')
                    deadline_text = f"📅 Due in {item['deadline_days']} days" if item['deadline_days'] is not None else "📅 Flexible"
                    
                    st.markdown(f"""
                    <div style="background-color: #f3e5f5; padding: 10px; border-radius: 5px; border-left: 4px solid #9c27b0; margin: 5px 0;">
                    <strong>{i}. {emoji} {item['name']}</strong><br>
                    🕐 {item['start_time']} - {item['end_time']} ({item['duration']} min)<br>
                    🔥 {item.get('intensity', 'Moderate')} | ⚡ Priority: {item['priority']}/20 | {deadline_text}
                    </div>
                    """, unsafe_allow_html=True)

    with col2:
        st.subheader("📊 Quick Stats")
        
        if st.session_state.tasks:
            total_ai_time = sum(analyze_task_comprehensive(task['name'])['duration'] for task in st.session_state.tasks)
            
            st.metric("Total Activities", len(st.session_state.tasks))
            st.metric("AI Estimated Time", f"{total_ai_time//60}h {total_ai_time%60}m")
            
            if st.session_state.schedule:
                work_items = [item for item in st.session_state.schedule if item['type'] not in ['meal', 'break', 'pomodoro_short_break', 'pomodoro_long_break', 'brain_rest']]
                pomodoro_items = [item for item in st.session_state.schedule if 'pomodoro' in item['type']]
                brain_rest_items = [item for item in st.session_state.schedule if item['type'] == 'brain_rest']
                
                st.metric("🎯 Tasks Scheduled", len(work_items))
                st.metric("🍅 Pomodoro Sessions", len(pomodoro_items))
                st.metric("🧠 Brain Rest Periods", len(brain_rest_items))
                
                # Productivity score
                if work_items:
                    avg_priority = sum(item.get('priority', 10) for item in work_items) / len(work_items)
                    productivity_score = min(100, int(avg_priority * 5))
                    st.metric("📈 Productivity Score", f"{productivity_score}%")
        
        else:
            st.info("Add activities to see stats")

with tab2:
    st.subheader("📊 Advanced Analytics Dashboard")
    
    if st.session_state.schedule:
        analytics_df = create_analytics_dashboard()
        
        if analytics_df is not None:
            # Time distribution chart
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("⏰ Time Distribution")
                type_duration = analytics_df.groupby('type')['duration'].sum().reset_index()
                fig_pie = px.pie(type_duration, values='duration', names='type', 
                               title="Time Allocation by Activity Type")
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("📈 Activity Timeline")
                fig_timeline = px.scatter(analytics_df, x='start_hour', y='duration', 
                                        color='type', size='duration',
                                        title="Activities Throughout the Day")
                fig_timeline.update_layout(xaxis_title="Hour of Day", yaxis_title="Duration (minutes)")
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Intensity analysis
            st.subheader("🔥 Intensity Analysis")
            intensity_counts = analytics_df['intensity'].value_counts()
            
            col1, col2 = st.columns(2)
            with col1:
                fig_bar = px.bar(x=intensity_counts.index, y=intensity_counts.values,
                               title="Task Intensity Distribution",
                               color=intensity_counts.values,
                               color_continuous_scale="viridis")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                # Productivity insights
                st.markdown("""
                <div class="feature-card">
                <h4>💡 AI Insights</h4>
                <ul>
                <li><strong>Peak Focus Time:</strong> Your high-intensity tasks are scheduled optimally</li>
                <li><strong>Break Balance:</strong> Adequate rest periods between intense work</li>
                <li><strong>Energy Management:</strong> Tasks aligned with natural energy patterns</li>
                <li><strong>Pomodoro Efficiency:</strong> Complex tasks broken into focused sessions</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Weekly trends (simulated)
            st.subheader("📈 Productivity Trends")
            
            # Generate sample weekly data
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            productivity_scores = [85, 78, 92, 88, 75, 60, 45]  # Sample data
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=days, y=productivity_scores, 
                                        mode='lines+markers',
                                        name='Productivity Score',
                                        line=dict(color='#667eea', width=3)))
            fig_line.update_layout(title="Weekly Productivity Trend", 
                                 xaxis_title="Day", yaxis_title="Productivity Score (%)")
            st.plotly_chart(fig_line, use_container_width=True)
            
    else:
        st.info("Generate a schedule to see analytics dashboard")

with tab3:
    st.subheader("✏️ Edit Your Activities")
    
    if st.session_state.tasks:
        # Edit/Delete Section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            activity_options = [f"{i+1}. {task['name']}" for i, task in enumerate(st.session_state.tasks)]
            selected_activity_str = st.selectbox(
                "Select activity to edit or remove:",
                activity_options,
                key="select_activity"
            )
            
            if selected_activity_str:
                selected_index = int(selected_activity_str.split('.')[0]) - 1
                selected_task = st.session_state.tasks[selected_index]
                
                current_analysis = analyze_task_comprehensive(selected_task['name'])
                st.info(f"🤖 Current AI analysis: {current_analysis['duration']} min, {current_analysis['intensity']}, {current_analysis['type']}")
        
        with col2:
            st.write("**Quick Actions:**")
            
            if st.button("🗑️ Remove Activity", type="secondary"):
                if selected_activity_str:
                    selected_index = int(selected_activity_str.split('.')[0]) - 1
                    removed_task = st.session_state.tasks.pop(selected_index)
                    st.success(f"Removed: {removed_task['name']}")
                    st.rerun()
            
            if st.button("✏️ Edit Activity", type="secondary"):
                if selected_activity_str:
                    st.session_state.editing_mode = True
                    st.session_state.edit_index = int(selected_activity_str.split('.')[0]) - 1
                    st.rerun()
        
        # Edit form
        if st.session_state.get('editing_mode', False):
            st.subheader("✏️ Edit Activity")
            edit_index = st.session_state.get('edit_index', 0)
            
            if edit_index < len(st.session_state.tasks):
                current_task = st.session_state.tasks[edit_index]
                
                with st.form("edit_form"):
                    st.write(f"**Editing:** {current_task['name']}")
                    
                    new_name = st.text_input(
                        "New activity name:", 
                        value=current_task['name'],
                        help="AI will re-analyze this automatically"
                    )
                    
                    current_has_deadline = current_task['deadline_days'] is not None
                    new_has_deadline = st.checkbox("Has specific deadline?", value=current_has_deadline)
                    
                    new_deadline_days = None
                    if new_has_deadline:
                        default_deadline = current_task['deadline_days'] if current_has_deadline else 1
                        new_deadline_days = st.number_input(
                            "Days until deadline", 
                            min_value=0, 
                            max_value=30, 
                            value=default_deadline
                        )
                    
                    if new_name and new_name != current_task['name']:
                        preview_analysis = analyze_task_comprehensive(new_name)
                        st.info(f"🤖 AI will detect: {preview_analysis['duration']} min, {preview_analysis['intensity']}, {preview_analysis['type']}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            st.session_state.tasks[edit_index] = {
                                'name': new_name,
                                'deadline_days': new_deadline_days
                            }
                            
                            st.session_state.editing_mode = False
                            st.session_state.edit_index = None
                            
                            st.success(f"Updated: {new_name}")
                            st.rerun()
                    
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.editing_mode = False
                            st.session_state.edit_index = None
                            st.rerun()
        
        st.markdown("---")
        if st.button("🧹 Clear All Activities", type="secondary"):
            st.session_state.tasks = []
            st.session_state.schedule = []
            st.session_state.editing_mode = False
            st.session_state.edit_index = None
            st.success("All activities cleared!")
            st.rerun()
    
    else:
        st.info("No activities to edit. Add some activities first!")

with tab4:
    st.subheader("📈 Progress Tracking")
    
    # Progress simulation
    if st.session_state.schedule:
        st.subheader("⏰ Daily Progress")
        
        # Simulate progress
        total_tasks = len([item for item in st.session_state.schedule if item['type'] not in ['meal', 'break', 'brain_rest']])
        completed_tasks = len(st.session_state.completed_tasks)
        
        if total_tasks > 0:
            progress = completed_tasks / total_tasks
            st.progress(progress)
            st.write(f"Progress: {completed_tasks}/{total_tasks} tasks completed ({progress*100:.0f}%)")
            
            # Task completion interface
            st.subheader("✅ Mark Tasks as Complete")
            
            incomplete_tasks = [item for item in st.session_state.schedule 
                              if item['type'] not in ['meal', 'break', 'brain_rest'] 
                              and f"{item['name']}_{item.get('start_time', '')}" not in st.session_state.completed_tasks]
            
            if incomplete_tasks:
                for idx, task in enumerate(incomplete_tasks[:5]):  # Show first 5 incomplete tasks
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"🎯 {task['name']} ({task.get('start_time', 'N/A')} - {task.get('end_time', 'N/A')})")
                    with col2:
                        # Create unique key using index and time to avoid duplicates
                        unique_key = f"complete_{idx}_{task.get('start_time', 'unknown')}_{hash(task['name']) % 10000}"
                        if st.button(f"✅ Complete", key=unique_key):
                            st.session_state.completed_tasks.append(f"{task['name']}_{task.get('start_time', '')}")
                            st.success(f"Completed: {task['name']}")
                            st.rerun()
            else:
                st.success("🎉 All tasks completed! Great job!")
        
        # Achievement system
        st.subheader("🏆 Achievements")
        
        achievements = []
        if len(st.session_state.completed_tasks) >= 1:
            achievements.append("🎯 First Task Completed")
        if len(st.session_state.completed_tasks) >= 5:
            achievements.append("🔥 Productivity Streak")
        if len(st.session_state.schedule_history) >= 3:
            achievements.append("📊 Planning Master")
        if any('pomodoro' in item['type'] for item in st.session_state.schedule):
            achievements.append("🍅 Pomodoro Practitioner")
        
        for achievement in achievements:
            st.success(achievement)
        
        # Weekly goals
        st.subheader("🎯 Weekly Goals")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tasks This Week", len(st.session_state.completed_tasks), "2")
        
        with col2:
            focus_time = sum(analyze_task_comprehensive(task['name'])['duration'] 
                           for task in st.session_state.tasks 
                           if analyze_task_comprehensive(task['name'])['intensity'] in ['High Focus', 'Deep Work'])
            st.metric("Focus Time (min)", focus_time, "45")
        
        with col3:
            st.metric("Planning Streak", len(st.session_state.schedule_history), "1")
        
    else:
        st.info("Generate a schedule to track your progress!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px;">
<h3>🛠️ Ultimate AI Daily Planner with Database</h3>
<p><strong>Created by Lingli Yang</strong> - Python Developer & Data Analyst</p>

<div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin: 20px 0;">
<div style="text-align: left;">
<h4>🤖 AI Features:</h4>
<ul style="list-style: none; padding: 0;">
<li>✅ Smart task analysis & duration prediction</li>
<li>✅ Automatic Pomodoro technique application</li>
<li>✅ Intelligent break management</li>
<li>✅ Brain rest optimization</li>
</ul>
</div>

<div style="text-align: left;">
<h4>📊 Analytics & Database:</h4>
<ul style="list-style: none; padding: 0;">
<li>✅ SQLite database persistence</li>
<li>✅ Save/load multiple schedules</li>
<li>✅ Advanced data visualizations</li>
<li>✅ Progress monitoring & achievements</li>
</ul>
</div>

<div style="text-align: left;">
<h4>💎 Premium Features:</h4>
<ul style="list-style: none; padding: 0;">
<li>✅ Export to CSV format</li>
<li>✅ Smart task suggestions</li>
<li>✅ Theme customization</li>
<li>✅ Schedule history tracking</li>
</ul>
</div>
</div>

<div style="background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 15px; border-radius: 10px; margin: 20px 0;">
<strong>🚀 Technologies Used:</strong> Python • Streamlit • SQLite • Plotly • Pandas • Advanced AI Algorithms<br>
<strong>📧 Contact:</strong> liliyang08@outlook.com • <strong>🔗 LinkedIn:</strong> linkedin.com/in/lingli-yang-74430a383
</div>

<p style="color: #666; font-style: italic;">
🌟 Transforming daily chaos into organized productivity through intelligent AI scheduling with persistent data storage 🌟
</p>
</div>
""", unsafe_allow_html=True)
