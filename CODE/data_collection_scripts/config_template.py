"""
Configuration template for Reddit API credentials.

To use the Reddit API with authentication:
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the form:
   - Name: TrustMed AI Data Collector
   - App type: Select "script"
   - Description: Collecting health forum data for research
   - About URL: (leave blank)
   - Redirect URI: http://localhost:8080
4. Click "Create app"
5. Copy your client_id and client_secret
6. Create a file named 'config.py' with the values below

Example config.py file:
"""

# Reddit API Configuration
REDDIT_CLIENT_ID = "your_client_id_here"
REDDIT_CLIENT_SECRET = "your_client_secret_here"
REDDIT_USER_AGENT = "TrustMedAI Health Forum Collector v1.0"
