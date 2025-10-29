"""
Script to populate questions table with 1000 diverse questions
"""
import sqlite3
import os
from datetime import datetime

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'questions.db')

# Categories from .env
CATEGORIES = [
    'work_and_career', 'hobbies_and_interests', 'family', 'friends', 'travel',
    'food_and_dining', 'movies_and_tv_shows', 'music', 'books_and_reading', 'sports',
    'current_events', 'politics', 'home_and_lifestyle', 'religion_and_spirituality',
    'health_and_fitness', 'technology', 'science', 'education', 'art_and_culture',
    'pets', 'personal_growth', 'past_experiences', 'future_plans', 'relationships',
    'philosophy', 'everyday_life', 'fashion_and_style', 'money_and_finance',
    'shopping', 'weekend_plans', 'local_events', 'seasons', 'world_cultures'
]

# Depth levels (excluding 'all')
DEPTHS = ['basic', 'moderate', 'deep', 'profound']

# Stage (using 'all' for simplicity)
STAGE = 'all'

# Work-related categories to exclude for students
WORK_CATEGORIES = ['work_and_career', 'money_and_finance']

# Question templates for each depth level
QUESTION_TEMPLATES = {
    'basic': [
        "What is your favorite {topic}?",
        "How often do you think about {topic}?",
        "Can you describe your experience with {topic}?",
        "What comes to mind when you hear about {topic}?",
        "Have you ever tried something new related to {topic}?",
        "What's the first thing you remember about {topic}?",
        "How would you introduce {topic} to someone?"
    ],
    'moderate': [
        "How has {topic} influenced your daily life?",
        "What challenges have you faced regarding {topic}?",
        "What lessons have you learned from your experiences with {topic}?",
        "How do you balance {topic} with other aspects of your life?",
        "What would you change about your approach to {topic}?",
        "How has your perspective on {topic} evolved over time?",
        "What advice would you give someone struggling with {topic}?"
    ],
    'deep': [
        "How has {topic} shaped who you are today?",
        "What deeper meaning does {topic} hold in your life?",
        "How do your values align with your experiences in {topic}?",
        "What fears or insecurities surface when you think about {topic}?",
        "How has {topic} challenged your beliefs or assumptions?",
        "What unresolved questions do you have about {topic}?",
        "How would you describe your emotional relationship with {topic}?"
    ],
    'profound': [
        "What fundamental truth about yourself have you discovered through {topic}?",
        "How has {topic} transformed your understanding of life's purpose?",
        "What would you sacrifice for what matters most in {topic}?",
        "How does {topic} connect to your core identity and sense of self?",
        "What legacy do you hope to create through your engagement with {topic}?",
        "How has {topic} revealed the interconnectedness of your life experiences?",
        "What deeper patterns have emerged in your journey with {topic}?"
    ]
}

# Topic phrases for each category
CATEGORY_TOPICS = {
    'work_and_career': ['your career', 'your professional growth', 'workplace relationships', 
                        'your job satisfaction', 'work-life balance', 'career ambitions', 'professional challenges'],
    'hobbies_and_interests': ['your hobbies', 'your creative pursuits', 'leisure activities',
                              'your interests', 'recreational time', 'passionate activities', 'personal projects'],
    'family': ['your family', 'family traditions', 'family relationships',
               'your upbringing', 'family values', 'family dynamics', 'generational connections'],
    'friends': ['your friendships', 'social connections', 'friend groups',
                'maintaining friendships', 'friendship quality', 'social bonds', 'meaningful connections'],
    'travel': ['traveling', 'exploring new places', 'cultural experiences',
               'travel adventures', 'discovering destinations', 'journey experiences', 'wanderlust'],
    'food_and_dining': ['food', 'culinary experiences', 'dining habits',
                        'cooking', 'food culture', 'meal traditions', 'taste preferences'],
    'movies_and_tv_shows': ['films and shows', 'storytelling through media', 'entertainment choices',
                            'cinematic experiences', 'television viewing', 'media consumption', 'visual narratives'],
    'music': ['music', 'musical experiences', 'songs and melodies',
              'musical preferences', 'sound and rhythm', 'musical expression', 'auditory memories'],
    'books_and_reading': ['reading', 'literature', 'books',
                          'written stories', 'reading habits', 'literary experiences', 'knowledge through reading'],
    'sports': ['sports', 'physical activities', 'athletic pursuits',
               'competition', 'team dynamics', 'physical fitness through sports', 'sporting experiences'],
    'current_events': ['current events', 'news and world happenings', 'contemporary issues',
                       'global developments', 'societal changes', 'modern challenges', 'today\'s world'],
    'politics': ['politics', 'civic engagement', 'political beliefs',
                 'governance', 'social policies', 'political awareness', 'democratic participation'],
    'home_and_lifestyle': ['your home', 'living space', 'lifestyle choices',
                           'domestic life', 'home environment', 'daily routines', 'household dynamics'],
    'religion_and_spirituality': ['spirituality', 'faith', 'religious beliefs',
                                  'spiritual practices', 'existential questions', 'sacred experiences', 'transcendence'],
    'health_and_fitness': ['health', 'fitness', 'physical well-being',
                           'wellness practices', 'body and mind', 'healthy living', 'vitality'],
    'technology': ['technology', 'digital tools', 'technological advancement',
                   'innovation', 'digital life', 'tech experiences', 'technological impact'],
    'science': ['science', 'scientific understanding', 'natural phenomena',
                'discovery', 'scientific thinking', 'empirical knowledge', 'the natural world'],
    'education': ['learning', 'education', 'knowledge acquisition',
                  'educational experiences', 'academic growth', 'intellectual development', 'studying'],
    'art_and_culture': ['art', 'cultural experiences', 'creative expression',
                        'cultural heritage', 'artistic appreciation', 'aesthetic experiences', 'cultural identity'],
    'pets': ['pets', 'animal companionship', 'pet care',
             'animal relationships', 'pet ownership', 'creatures you love', 'animal bonds'],
    'personal_growth': ['personal growth', 'self-improvement', 'self-development',
                        'becoming better', 'inner transformation', 'self-awareness', 'evolving as a person'],
    'past_experiences': ['your past', 'previous experiences', 'memories',
                         'life history', 'formative moments', 'yesterday', 'what came before'],
    'future_plans': ['your future', 'future aspirations', 'goals ahead',
                     'tomorrow', 'future visions', 'what\'s to come', 'forward planning'],
    'relationships': ['relationships', 'intimate connections', 'romantic partnerships',
                      'love', 'relational bonds', 'emotional connections', 'partnership'],
    'philosophy': ['philosophical questions', 'life\'s meaning', 'existential thoughts',
                   'philosophical beliefs', 'deeper truths', 'wisdom', 'understanding existence'],
    'everyday_life': ['daily life', 'ordinary moments', 'routine experiences',
                      'everyday activities', 'daily rhythms', 'regular life', 'day-to-day existence'],
    'fashion_and_style': ['fashion', 'personal style', 'self-expression through clothing',
                          'fashion choices', 'aesthetic presentation', 'style preferences', 'appearance'],
    'money_and_finance': ['money', 'financial matters', 'financial well-being',
                          'finances', 'economic security', 'financial decisions', 'monetary concerns'],
    'shopping': ['shopping', 'purchasing decisions', 'consumer choices',
                 'buying experiences', 'acquisition habits', 'shopping behavior', 'marketplace interactions'],
    'weekend_plans': ['weekends', 'leisure time', 'days off',
                      'weekend activities', 'free time', 'weekend routines', 'time away from obligations'],
    'local_events': ['local events', 'community happenings', 'neighborhood activities',
                     'local culture', 'community gatherings', 'nearby experiences', 'local scene'],
    'seasons': ['seasonal changes', 'the seasons', 'seasonal rhythms',
                'seasonal experiences', 'cyclical patterns', 'seasonal transitions', 'nature\'s cycles'],
    'world_cultures': ['world cultures', 'cultural diversity', 'global traditions',
                       'international experiences', 'cross-cultural understanding', 'cultural differences', 'global perspectives']
}


def generate_questions():
    """Generate 1000+ questions and insert into database"""
    print(f"Generating questions for {len(CATEGORIES)} categories × {len(DEPTHS)} depths × 7 questions each")
    print(f"Total: {len(CATEGORIES) * len(DEPTHS) * 7} questions")
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    questions = []
    
    for category in CATEGORIES:
        topics = CATEGORY_TOPICS.get(category, [category.replace('_', ' ')])
        exclude_for_students = 1 if category in WORK_CATEGORIES else 0
        
        for depth in DEPTHS:
            templates = QUESTION_TEMPLATES[depth]
            
            for i, template in enumerate(templates):
                topic = topics[i % len(topics)]
                question_text = template.format(topic=topic)
                
                questions.append({
                    'category': category,
                    'depth': depth,
                    'stage': STAGE,
                    'question': question_text,
                    'exclude_for_students': exclude_for_students,
                    'created_at': now,
                    'updated_at': now
                })
    
    return questions


def insert_questions():
    """Insert questions into database"""
    print("Connecting to database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Generate questions
    questions = generate_questions()
    print(f"Generated {len(questions)} questions")
    
    # Clear existing questions (optional)
    response = input("Do you want to clear existing questions? (yes/no): ")
    if response.lower() == 'yes':
        cursor.execute("DELETE FROM questions")
        print("Cleared existing questions")
    
    # Insert questions
    inserted = 0
    skipped = 0
    
    for q in questions:
        try:
            cursor.execute("""
                INSERT INTO questions (category, depth, stage, question, exclude_for_students, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (q['category'], q['depth'], q['stage'], q['question'], q['exclude_for_students'], 
                  q['created_at'], q['updated_at']))
            inserted += 1
        except sqlite3.IntegrityError:
            # Question already exists
            skipped += 1
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Successfully inserted {inserted} questions")
    if skipped > 0:
        print(f"⏭️  Skipped {skipped} duplicate questions")
    
    # Display statistics
    print("\n📊 Questions by category:")
    category_counts = {}
    for q in questions:
        cat = q['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for cat, count in sorted(category_counts.items()):
        work_marker = " (hidden from students)" if cat in WORK_CATEGORIES else ""
        print(f"  {cat}: {count} questions{work_marker}")


if __name__ == "__main__":
    print("=" * 60)
    print("Question Database Population Script")
    print("=" * 60)
    insert_questions()
