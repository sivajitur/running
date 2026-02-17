# Running Analytics 🏃

A modular, production-ready Python application for analyzing Strava running data with AI insights.

## 📁 Project Structure

```
running_analytics/
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py        # Centralized settings and environment variables
│
├── data/                  # Data collection and processing
│   ├── __init__.py
│   ├── strava_client.py   # Strava API client
│   └── data_processor.py  # Data transformation and utilities
│
├── analysis/              # Analysis and AI
│   ├── __init__.py
│   ├── analyzer.py        # Running data analytics
│   └── ai_client.py       # Perplexity AI integration
│
└── ui/                    # User interface (Streamlit)
    ├── __init__.py
    ├── app.py             # Main Streamlit application
    └── components/        # Reusable UI components
        ├── __init__.py
        ├── metrics.py     # Metric display components
        ├── charts.py      # Chart and visualization components
        └── ai_tab.py      # AI assistant tab
```

## 🏗️ Architecture

### **Config Layer** (`config/`)
Centralized configuration management for all API keys and settings.
- Single source of truth for environment variables
- Easy to extend with new settings

### **Data Layer** (`data/`)
Handles all data collection and processing operations.
- `StravaClient`: OAuth token management and API communication
- `DataProcessor`: Unit conversions, DataFrame creation, CSV/JSON export

### **Analysis Layer** (`analysis/`)
Business logic for analyzing running data and AI interactions.
- `RunningAnalyzer`: Statistical analysis and filtering
- `PerplexityClient`: AI assistant integration

### **UI Layer** (`ui/`)
Streamlit-based user interface with modular components.
- `StreamlitApp`: Main application orchestration
- Reusable components for metrics, charts, and AI tab

## 🚀 Quick Start

### Installation

```bash
# Clone and navigate to the project
cd running_mcp

# Install dependencies
pip install -r requirements.txt
```

### Configuration

The app supports multiple deployment-friendly configuration methods:

#### Option 1: Using `.streamlit/secrets.toml` (Recommended)

1. Copy the example file:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

2. Edit `.streamlit/secrets.toml` and add your credentials:
```toml
STRAVA_CLIENT_ID = "your_client_id"
STRAVA_CLIENT_SECRET = "your_client_secret"
PERPLEXITY_API_KEY = "your_api_key"  # Optional
```

3. Run the app - no code changes needed!

#### Option 2: Environment Variables

```bash
export STRAVA_CLIENT_ID="your_client_id"
export STRAVA_CLIENT_SECRET="your_client_secret"
export PERPLEXITY_API_KEY="your_api_key"  # Optional
streamlit run app.py
```

#### Option 3: Manual Setup in App

- Just run the app and you'll see an interactive setup page
- Enter your credentials through the UI
- No configuration files needed!

### Getting Strava Credentials

1. Go to https://www.strava.com/settings/apps
2. Click "Create New App"
3. Fill in:
   - **Name**: Running Analytics
   - **Category**: Training
   - **Website**: http://localhost:8501 (or your deployment URL)
   - **Authorization Callback Domain**: localhost
4. Copy your **Client ID** and **Client Secret**

### Run the Application

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

## 📊 Features

### Data Collection
- OAuth-based Strava API authentication
- Automatic token refresh
- Pagination support for large datasets

### Analysis
- Daily, weekly, and monthly statistics
- Filtering by date range, day of week, and distance
- Comprehensive performance metrics

### AI Insights
- Perplexity integration for personalized coaching
- Context-aware questions about your running
- Pre-built example prompts

### Visualization
- Interactive charts with Plotly
- Distance trends over time
- Heart rate vs distance correlation
- Distance distribution analysis

## 🔌 Integration Points

### Adding New Data Sources
1. Create a new client in `data/` (e.g., `garmin_client.py`)
2. Implement the same interface as `StravaClient`
3. Add configuration to `config/settings.py`

### Adding New Analysis
1. Add methods to `analysis/analyzer.py`
2. Create new visualization component in `ui/components/charts.py`
3. Add tab to main app in `ui/app.py`

### Customizing UI
- Modify `ui/components/` for visual changes
- Update `ui/app.py` for layout changes
- Edit `config/settings.py` for styling preferences

## 🧪 Usage Examples

### Programmatic Usage

```python
from src.data import StravaClient, DataProcessor
from src.analysis import RunningAnalyzer

# Fetch data
client = StravaClient()
activities = client.get_activities(months_back=6)

# Process data
df = DataProcessor.convert_activities_to_dataframe(activities)
DataProcessor.save_csv(df)

# Analyze
analyzer = RunningAnalyzer(df)
stats = analyzer.get_summary_stats()
print(stats)
```

### Querying AI

```python
from src.analysis import PerplexityClient, RunningAnalyzer
from src.data import DataProcessor

df = DataProcessor.load_csv()
analyzer = RunningAnalyzer(df)
context = PerplexityClient.create_context(df, analyzer)

client = PerplexityClient()
response = client.query("What's my average pace?", context)
print(response)
```

## 📦 Dependencies

- **streamlit**: Web UI framework
- **pandas**: Data manipulation
- **plotly**: Interactive visualizations
- **requests**: HTTP client for APIs
- **python-dotenv**: Environment variable management

## 🔒 Security

- API keys stored in `.env` (never commit this file)
- OAuth token refresh handled automatically
- Environment variables validated on startup

## � Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to https://streamlit.io/cloud
3. Click "New app" and select your repo
4. Click "Advanced settings" → "Secrets"
5. Add your credentials:
```toml
STRAVA_CLIENT_ID = "your_client_id"
STRAVA_CLIENT_SECRET = "your_client_secret"
```
6. Deploy!

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

# Set credentials as environment variables
ENV STRAVA_CLIENT_ID=your_client_id
ENV STRAVA_CLIENT_SECRET=your_client_secret

CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t running-analytics .
docker run -p 8501:8501 \
  -e STRAVA_CLIENT_ID=your_id \
  -e STRAVA_CLIENT_SECRET=your_secret \
  running-analytics
```

### Heroku

```bash
# Set config variables
heroku config:set STRAVA_CLIENT_ID="your_client_id"
heroku config:set STRAVA_CLIENT_SECRET="your_client_secret"

# Deploy
git push heroku main
```

### Key Point: No Source Code Changes Needed

All deployment methods use environment variables or secrets - **no .env file or source code modifications required**!

## �📝 Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Docstring every function/class

### Adding Features
1. Create in appropriate module (config/data/analysis/ui)
2. Add unit tests
3. Update README
4. Import/export in `__init__.py`

### File Organization
- Keep modules single-responsibility
- Use `__init__.py` for clean imports
- Export public API in module `__init__.py`

## 🤝 Contributing

When modifying the code:
1. Maintain the modular structure
2. Keep dependencies between layers unidirectional
3. Add docstrings for public methods
4. Update this README if adding new features

## 📄 License

MIT License

## 🆘 Troubleshooting

**401 Unauthorized Error**: Check that your PERPLEXITY_API_KEY is valid
**Strava API Error**: Verify your Strava credentials and refresh token
**Data not loading**: Ensure `strava_activities.csv` exists or fetch fresh data
