import os
import json
from datetime import datetime
from perplexityai import Perplexity
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RunAnalyzer:
    def __init__(self):
        self.data_file = 'strava_activities.json'
        self.training_plan_file = 'marathon_plan.json'
        # Initialize Perplexity client
        self.perplexity = Perplexity(api_key=os.getenv('PERPLEXITY_API_KEY'))
        # Default to mixtral-8x7b model
        self.model = "mixtral-8x7b-instruct"
        # Load training plan if exists
        self.training_plan = self._load_training_plan()

    def _load_training_plan(self):
        """Load marathon training plan from file if it exists"""
        if os.path.exists(self.training_plan_file):
            try:
                with open(self.training_plan_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        return None

    def set_training_plan(self, training_plan):
        """
        Set a marathon training plan
        training_plan should be a dictionary with:
        - target_race: { date: "YYYY-MM-DD", distance: "marathon/half-marathon", goal_time: "HH:MM:SS" }
        - weekly_mileage: target weekly mileage
        - long_run_day: preferred day for long runs
        - workouts_per_week: number of quality workouts per week
        - experience_level: "beginner", "intermediate", or "advanced"
        """
        self.training_plan = training_plan
        with open(self.training_plan_file, 'w') as f:
            json.dump(training_plan, f, indent=2)

    def load_activities(self):
        """Load activities from the cached file"""
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(
                "No cached Strava data found. Please run fetch_strava.py first."
            )

        with open(self.data_file, 'r') as f:
            data = json.load(f)
            
        # Check data age
        cache_time = datetime.fromisoformat(data['timestamp'])
        age = datetime.now() - cache_time
        if age.days > 0:
            print(f"Warning: Data is {age.days} days old. Consider running fetch_strava.py to update.")
        elif age.seconds > 10800:  # 3 hours
            print(f"Warning: Data is {age.seconds // 3600} hours old. Consider running fetch_strava.py to update.")
            
        return data['activities']

    def analyze_runs(self, user_question, activities):
        # Filter only running activities and prepare data
        runs = [activity for activity in activities if activity['type'] == 'Run']
        if not runs:
            return "No recent runs found to analyze."

        # Prepare run data for LLM analysis
        runs_summary = []
        for run in runs:
            run_summary = {
                'date': datetime.fromisoformat(run['start_date'].replace('Z', '+00:00')).strftime('%Y-%m-%d'),
                'distance': round(run['distance'] / 1000, 2),  # Convert to km
                'time': round(run['moving_time'] / 60, 2),    # Convert to minutes
                'elevation': run['total_elevation_gain'],
                'average_speed': round((run['distance'] / run['moving_time']) * 3.6, 2)  # km/h
            }
            runs_summary.append(run_summary)

        # Prepare training plan context if available
        training_plan_context = ""
        if self.training_plan:
            days_to_race = (datetime.strptime(self.training_plan['target_race']['date'], '%Y-%m-%d') - datetime.now()).days
            training_plan_context = f"""
            Current Marathon Training Context:
            - Target Race: {self.training_plan['target_race']['date']} ({self.training_plan['target_race']['distance']})
            - Days until race: {days_to_race}
            - Goal Time: {self.training_plan['target_race']['goal_time']}
            - Target Weekly Mileage: {self.training_plan['weekly_mileage']} km
            - Long Run Day: {self.training_plan['long_run_day']}
            - Target Workouts per Week: {self.training_plan['workouts_per_week']}
            - Experience Level: {self.training_plan['experience_level']}
            """

        # Create base prompt with run data and training context
        base_context = f"""Recent Running Activities:
            {json.dumps(runs_summary, indent=2)}

            {training_plan_context}"""

        # Combine with user question
        full_prompt = f"""{base_context}

                Based on this information, please {user_question}

                Consider the following in your response:
                1. Training periodization and current phase
                2. Weekly mileage progression
                3. Recovery needs based on recent activity
                4. Race-specific training requirements
                5. Key workout scheduling
                6. Long run progression
                7. Injury prevention
                8. Weather and environmental factors

                Provide specific, actionable advice including:
                - Workout type and structure
                - Target distances and paces
                - Recovery guidelines
                - Alternative options if needed
                - How this fits into the larger training plan"""

        # Get response from Perplexity
        response = self.perplexity.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an experienced running coach who analyzes training patterns and provides personalized recommendations."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        )

        # Save the recommendation
        recommendation = response.text
        with open('latest_recommendation.txt', 'w') as f:
            f.write(recommendation)

        return recommendation

def main():
    try:
        analyzer = RunAnalyzer()
        
        # Load cached activities
        print("Loading cached Strava activities...")
        activities = analyzer.load_activities()
        
        # Get recommendation
        print("\nAnalyzing your recent runs...")
        recommendation = analyzer.analyze_runs(activities)
        
        print("\nRecommendation for your next run:")
        print(recommendation)
        print("\nThis recommendation has been saved to 'latest_recommendation.txt'")
        print("Run summaries have been saved to 'recent_runs_summary.json'")

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()