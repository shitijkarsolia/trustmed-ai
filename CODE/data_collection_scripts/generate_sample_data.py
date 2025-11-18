#!/usr/bin/env python3
"""
Generate sample health forum discussion data for demonstration purposes.
This creates realistic sample data matching the expected format from Reddit collection.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import random
import os

OUTPUT_DIR = '/home/user/trustmed-ai/data_collection/data'

# Sample data templates
DIABETES_POSTS = [
    {
        'title': 'Recently diagnosed with Type 2 Diabetes - where do I start?',
        'body': 'I was just diagnosed with T2D last week. My A1C is 8.2 and my fasting glucose was 165. My doctor prescribed Metformin 500mg twice daily. I\'m feeling overwhelmed. What should I focus on first? Diet? Exercise? Any tips from experienced folks?',
        'keywords': ['diagnosed', 'type 2', 'a1c', 'metformin', 'diet', 'exercise']
    },
    {
        'title': 'Metformin side effects - is this normal?',
        'body': 'I\'ve been on Metformin 1000mg twice daily for 3 weeks now. Experiencing stomach upset and diarrhea. Doctor says this is normal but it\'s really affecting my daily life. Does it get better? Should I talk to my doctor about alternatives?',
        'keywords': ['metformin', 'side effects', 'stomach', 'medication']
    },
    {
        'title': 'What foods have you found that don\'t spike your blood sugar?',
        'body': 'I\'m trying to figure out my diet. I test my blood sugar before and 2 hours after meals. Looking for meal ideas that work well. What are your go-to foods that keep blood sugar stable?',
        'keywords': ['blood sugar', 'diet', 'foods', 'meals']
    },
    {
        'title': 'Exercise and blood sugar - confused about timing',
        'body': 'When I exercise in the morning fasting, my blood sugar goes UP not down. When I exercise after eating, it goes down. Is this normal? What\'s the best time to exercise for blood sugar control?',
        'keywords': ['exercise', 'blood sugar', 'timing', 'control']
    },
    {
        'title': 'Success story - A1C went from 9.1 to 5.8 in 6 months',
        'body': 'Just wanted to share my progress. Through diet changes (low carb), regular exercise (30 min walks daily), and Metformin, I\'ve gotten my A1C from 9.1 down to 5.8. It\'s possible! Happy to answer questions.',
        'keywords': ['success', 'a1c', 'low carb', 'exercise', 'metformin']
    },
    {
        'title': 'Dealing with diabetes burnout',
        'body': 'I\'ve had T2D for 5 years. Lately I\'m just tired of constantly thinking about food, testing blood sugar, taking medications. Anyone else experience this? How do you cope?',
        'keywords': ['burnout', 'mental health', 'management']
    },
    {
        'title': 'Best glucose meter recommendations?',
        'body': 'My current meter seems inaccurate - getting wildly different readings minutes apart. What meters do you all recommend? Looking for accuracy and affordability.',
        'keywords': ['glucose meter', 'testing', 'equipment']
    },
    {
        'title': 'Going from Metformin to Insulin - advice needed',
        'body': 'My doctor says Metformin isn\'t controlling my blood sugar well enough (A1C 8.9) and wants to start basal insulin. I\'m nervous about starting insulin. Is it as hard as I think?',
        'keywords': ['metformin', 'insulin', 'medication change']
    },
    {
        'title': 'Prediabetes to full diabetes - what changed?',
        'body': 'I was prediabetic for 2 years (A1C 6.1-6.3), now diagnosed with diabetes (A1C 7.2). I didn\'t think I changed much, but looking back I let my diet slip and stopped exercising. Take prediabetes seriously folks!',
        'keywords': ['prediabetes', 'progression', 'prevention']
    },
    {
        'title': 'Nighttime blood sugar drops - waking up with lows',
        'body': 'I keep waking up at 3am feeling shaky and sweating. Blood sugar is in the 60s. It\'s scary. I\'m on Metformin and Glipizide. Should I call my doctor?',
        'keywords': ['hypoglycemia', 'nighttime', 'low blood sugar', 'medication']
    }
]

HEART_DISEASE_POSTS = [
    {
        'title': 'Just diagnosed with hypertension - blood pressure 160/95',
        'body': 'My doctor just told me I have high blood pressure. It\'s been consistently 155-165/90-100. He prescribed Lisinopril 10mg. Should I be worried? What lifestyle changes helped you most?',
        'keywords': ['hypertension', 'blood pressure', 'lisinopril', 'diagnosis']
    },
    {
        'title': 'Best time to take blood pressure medication?',
        'body': 'I\'m on Amlodipine 5mg. Doctor said take it once daily but didn\'t specify when. Morning or evening? Does it matter? What works best for you?',
        'keywords': ['medication', 'amlodipine', 'timing', 'blood pressure']
    },
    {
        'title': 'High blood pressure + high cholesterol - managing both',
        'body': 'Recently diagnosed with BP 150/92 and cholesterol 240. Doctor prescribed Lisinopril and Atorvastatin. Feeling overwhelmed with two conditions. Any advice on managing both?',
        'keywords': ['blood pressure', 'cholesterol', 'multiple conditions', 'statin']
    },
    {
        'title': 'How much does diet really affect blood pressure?',
        'body': 'I\'ve been on medication for 6 months. BP still not great (138/88). How much can diet changes really help? Is DASH diet worth it? What foods should I avoid?',
        'keywords': ['diet', 'dash', 'blood pressure', 'management']
    },
    {
        'title': 'Exercise with high blood pressure - is it safe?',
        'body': 'BP is 145/90 even with medication. Doctor says exercise will help but I\'m worried about having a heart attack while exercising. What exercises are safe? How intense should I go?',
        'keywords': ['exercise', 'safety', 'blood pressure', 'heart health']
    },
    {
        'title': 'Blood pressure medication side effects - swollen ankles',
        'body': 'I\'ve been on Amlodipine for 2 months and my ankles are really swollen. Is this normal? Should I ask to switch medications? What worked for you?',
        'keywords': ['side effects', 'amlodipine', 'swelling', 'medication']
    },
    {
        'title': 'White coat hypertension vs real hypertension',
        'body': 'At the doctor my BP is always 150/95+. At home it\'s 125/80. Doctor wants to start medication but I think it\'s just white coat syndrome. Should I push back?',
        'keywords': ['white coat', 'home monitoring', 'diagnosis']
    },
    {
        'title': 'Success reducing BP through weight loss',
        'body': 'Lost 30 pounds over 4 months. BP went from 145/92 to 118/75. Still on medication but doctor reduced dosage. Weight loss really does work!',
        'keywords': ['weight loss', 'success', 'blood pressure', 'lifestyle']
    },
    {
        'title': 'Family history of heart disease - how worried should I be?',
        'body': 'Dad had heart attack at 52, grandfather at 48. I\'m 35 with BP 135/85. Doctor says I\'m prehypertensive. What preventive measures should I take seriously?',
        'keywords': ['family history', 'prevention', 'heart disease', 'risk factors']
    },
    {
        'title': 'Stress and blood pressure - breaking the cycle',
        'body': 'My BP spikes whenever I\'m stressed at work. Can go from 120/75 to 150/95. How do you manage stress to keep BP down? Meditation? Therapy?',
        'keywords': ['stress', 'blood pressure', 'management', 'mental health']
    }
]

COMMENTS_POOL = {
    'diabetes': [
        'I went through the same thing. Metformin side effects get better after 4-6 weeks. Hang in there!',
        'My doctor recommended taking Metformin with food to reduce stomach issues. Game changer for me.',
        'Talk to your doctor about extended release Metformin. Much easier on the stomach.',
        'I found that cutting carbs helped more than anything else. Check out low carb diet resources.',
        'Walking after meals has been huge for my blood sugar control. Even just 10-15 minutes helps.',
        'Have you tried testing different foods to see what spikes your blood sugar? Everyone is different.',
        'Stress can really affect blood sugar too. Don\'t forget the mental health aspect.',
        'My A1C was 9.2 when diagnosed. Now it\'s 6.1 after 8 months of lifestyle changes and medication.',
        'Get a CGM if you can afford it. Continuous glucose monitoring is so helpful for understanding patterns.',
        'The diabetes subreddit wiki has great resources for newly diagnosed folks.',
    ],
    'heart_disease': [
        'I had the same ankle swelling on Amlodipine. Doctor switched me to Lisinopril and it resolved.',
        'Reducing sodium has helped my BP more than I expected. Check labels - it\'s in everything!',
        'I take my BP meds at night. Studies show it may reduce heart attack risk vs morning dosing.',
        'DASH diet really works. My BP dropped 12 points in 6 weeks just from diet changes.',
        'Get a home BP monitor and track it daily. Helps you see patterns and what affects it.',
        'Exercise was scary at first but starting slow with walking really helped. BP is much better now.',
        'Lost 25 pounds and my doctor cut my medication dose in half. Weight loss is powerful.',
        'White coat syndrome is real but you should still monitor at home to be sure.',
        'Stress management through meditation dropped my BP by 10 points. Don\'t underestimate it.',
        'Family history is a risk factor but lifestyle matters more than genetics for many people.',
    ]
}

def generate_sample_thread(post_template, disease_area, thread_number):
    """Generate a single realistic thread."""

    # Generate timestamp (random date in last 6 months)
    days_ago = random.randint(0, 180)
    created_date = datetime.now() - timedelta(days=days_ago)

    # Generate author
    author = f"user_{random.randint(1000, 9999)}"

    # Generate engagement metrics
    score = random.randint(5, 250)
    num_comments = random.randint(3, 45)
    upvote_ratio = round(random.uniform(0.75, 0.98), 2)

    # Generate comments
    comments = []
    comment_pool = COMMENTS_POOL[disease_area]

    for i in range(min(num_comments, len(comment_pool))):
        comment_date = created_date + timedelta(hours=random.randint(1, 48))
        comments.append({
            'author': f"user_{random.randint(1000, 9999)}",
            'body': random.choice(comment_pool),
            'score': random.randint(1, 50),
            'created_utc': comment_date.isoformat()
        })

    # Determine subreddit
    subreddit_map = {
        'diabetes': ['diabetes', 'diabetes_t2', 'type2diabetes'],
        'heart_disease': ['hypertension', 'HeartDisease']
    }
    subreddit = random.choice(subreddit_map[disease_area])

    thread_id = f"sample_{disease_area}_{thread_number:04d}"

    thread = {
        'id': thread_id,
        'title': post_template['title'],
        'author': author,
        'subreddit': subreddit,
        'created_utc': created_date.isoformat(),
        'score': score,
        'num_comments': num_comments,
        'url': f"https://reddit.com/r/{subreddit}/comments/{thread_id}/",
        'selftext': post_template['body'],
        'upvote_ratio': upvote_ratio,
        'comments': comments,
        'keywords': post_template['keywords'],
        'collected_at': datetime.now().isoformat()
    }

    return thread

def generate_dataset(disease_area, posts_templates, target_count=500):
    """Generate a complete dataset for a disease area."""
    threads = []

    # Generate threads by cycling through templates and variations
    while len(threads) < target_count:
        for template in posts_templates:
            if len(threads) >= target_count:
                break

            thread = generate_sample_thread(template, disease_area, len(threads) + 1)
            threads.append(thread)

    return threads

def save_data(threads, disease_name):
    """Save generated data to JSON and CSV files."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save as JSON
    json_filename = f"{OUTPUT_DIR}/{disease_name}_threads_sample_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(threads, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved JSON: {json_filename}")

    # Save as CSV
    csv_data = []
    for thread in threads:
        csv_row = {
            'id': thread['id'],
            'title': thread['title'],
            'author': thread['author'],
            'subreddit': thread['subreddit'],
            'created_utc': thread['created_utc'],
            'score': thread['score'],
            'num_comments': thread['num_comments'],
            'url': thread['url'],
            'selftext': thread['selftext'][:500],
            'upvote_ratio': thread['upvote_ratio'],
            'num_collected_comments': len(thread['comments']),
            'keywords': ', '.join(thread['keywords'])
        }
        csv_data.append(csv_row)

    df = pd.DataFrame(csv_data)
    csv_filename = f"{OUTPUT_DIR}/{disease_name}_threads_sample_{timestamp}.csv"
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"✓ Saved CSV: {csv_filename}")

    return json_filename, csv_filename

def main():
    """Generate sample data for both disease areas."""
    print("=" * 70)
    print("TrustMed AI - Sample Data Generator")
    print("=" * 70)
    print("\nGenerating sample health forum discussion threads...")
    print("Note: This is demonstration data for development purposes.\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = {}

    # Generate diabetes data
    print("Generating Type II Diabetes threads...")
    diabetes_threads = generate_dataset('diabetes', DIABETES_POSTS, target_count=500)
    json_file, csv_file = save_data(diabetes_threads, 'diabetes')
    all_results['diabetes'] = {
        'count': len(diabetes_threads),
        'json_file': json_file,
        'csv_file': csv_file
    }
    print(f"  Generated {len(diabetes_threads)} threads\n")

    # Generate heart disease data
    print("Generating Heart Disease/Hypertension threads...")
    heart_threads = generate_dataset('heart_disease', HEART_DISEASE_POSTS, target_count=500)
    json_file, csv_file = save_data(heart_threads, 'heart_disease')
    all_results['heart_disease'] = {
        'count': len(heart_threads),
        'json_file': json_file,
        'csv_file': csv_file
    }
    print(f"  Generated {len(heart_threads)} threads\n")

    # Print summary
    print("=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)
    total = sum(r['count'] for r in all_results.values())
    print(f"\nTotal threads generated: {total}")

    for disease_name, results in all_results.items():
        print(f"\n{disease_name.upper().replace('_', ' ')}:")
        print(f"  - Threads: {results['count']}")
        print(f"  - JSON: {results['json_file']}")
        print(f"  - CSV: {results['csv_file']}")

    print("\n" + "=" * 70)
    print("Sample data generation complete!")
    print("=" * 70)
    print("\nIMPORTANT: This is sample data for demonstration purposes.")
    print("For production use, collect real data using the Reddit API scripts.")
    print("See data_collection/README.md for instructions.\n")

if __name__ == "__main__":
    main()
