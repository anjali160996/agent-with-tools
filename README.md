# Test Question Generation System

An AI-powered system for generating test questions and answers using OpenAI's GPT models. This system provides a complete workflow from initial summary to approved questions and answers.

## Features

The system supports a 5-step workflow:

1. **Create Session**: User provides a summary/context for test question generation. The system creates a session (runId) and stores it in the database.
2. **Generate Questions**: Using OpenAI's LLM, the system generates questions based on the summary. Questions are saved to a staging table and displayed to the user.
3. **Review Questions**: User reviews each generated question and marks them as approved or rejected. This approval status is saved in the database.
4. **Generate Answers**: The system generates answers for approved questions using the LLM. Answers are saved to a staging table.
5. **Review Answers**: User reviews each generated answer and marks them as approved or rejected. Final approval status is saved in the database.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **LLM**: OpenAI GPT-3.5-turbo
- **Frontend**: HTML, CSS, JavaScript (Vanilla JS)

## Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your OpenAI API key:**
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```

3. **Initialize the database:**
   The database will be automatically created when you first run the application.

## Usage

### Starting the Server

1. **Run the FastAPI server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload
   ```

2. **Access the application:**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend UI: Open `static/index.html` in your browser (or serve it via a web server)

   **Note**: For the frontend to work properly with CORS, you should serve the static files through the FastAPI server or use a simple HTTP server.

### Serving Static Files (Optional)

To serve the static files through FastAPI, you can mount them:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

Or use a simple HTTP server:

```bash
# Python 3
python -m http.server 8080 --directory static

# Then access http://localhost:8080
```

## Database Schema

The system uses three main tables:

- **runs**: Stores session/run information with summary
- **question_staging**: Stores generated questions with approval status
- **answer_staging**: Stores generated answers with approval status

All tables are automatically created when the application starts.

## API Endpoints

### Run Management
- `POST /api/runs` - Create a new run/session
- `GET /api/runs/{run_id}` - Get run details

### Questions
- `POST /api/runs/{run_id}/generate-questions` - Generate questions using LLM
- `GET /api/runs/{run_id}/questions` - Get all questions for a run
- `PATCH /api/questions/{question_id}/approval` - Update question approval status

### Answers
- `POST /api/runs/{run_id}/generate-answers` - Generate answers for approved questions
- `GET /api/runs/{run_id}/answers` - Get all answers for a run
- `PATCH /api/answers/{answer_id}/approval` - Update answer approval status

### Health Check
- `GET /api/health` - Health check endpoint

## Project Structure

```
.
├── main.py              # FastAPI application and endpoints
├── database.py          # Database models and setup
├── models.py            # Pydantic models for request/response
├── llm_service.py       # OpenAI LLM integration
├── static/
│   ├── index.html       # Frontend UI
│   ├── style.css        # Styling
│   └── app.js           # Frontend JavaScript
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── test_questions.db   # SQLite database (created automatically)
```

## Workflow Example

1. User enters summary: "Python programming basics including variables, loops, functions"
2. Click "Create Session" → Session ID is generated
3. Click "Generate Questions" → 5 questions are generated and displayed
4. User reviews each question and marks them as Approved/Rejected
5. Click "Generate Answers" → Answers are generated for approved questions
6. User reviews each answer and marks them as Approved/Rejected
7. All data is persisted in the database throughout the process

## Configuration

You can modify the following in `llm_service.py`:

- `model`: Change the OpenAI model (default: "gpt-3.5-turbo")
- `temperature`: Adjust creativity (default: 0.7 for questions, 0.5 for answers)
- `max_tokens`: Adjust response length limits

## Troubleshooting

1. **OpenAI API errors**: Ensure your API key is correct and you have sufficient credits
2. **Database errors**: Delete `test_questions.db` to reset the database
3. **CORS errors**: Make sure CORS middleware is enabled (already configured for development)
4. **Frontend not loading**: Ensure you're accessing the frontend through a web server or the FastAPI static file mount

## License

MIT License
