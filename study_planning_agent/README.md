---- STUDY PLANNING AGENT SETUP ----

-- REQUIREMENTS --

- Python 3.x
- A Gemini API key
- Dependencies listed in requirements.txt

-- CONFIGURATION --

Create a .env file in the project root and add the Gemini API key:
GOOGLE_API_KEY=your_api_key_here

-- INSTALLING DEPENDENCIES --

From the project directory in your terminal, install the required packages with:
pip install -r requirements.txt

-- RUNNING THE APPLICATION --

Start the FastAPI application using Uvicorn:
uvicorn main:app --reload

The application will be available at:
http://127.0.0.1:8000

The Swagger interface can be accessed at:
http://127.0.0.1:8000/docs

-- API ENDPOINT --

The main agent endpoint is:
POST /api/agent/study-plan

It accepts the student's available study time.
Example request:
{
    "available_hours": 5
}

The endpoint returns a structured recommendation containing:
- Assessment name
- Priority
- Reason
- Suggested action

-- RUNNING TESTS --

Run the complete automated test suite with:
pytest -v

-- ASSESSMENT DATA --

The application currently uses stored assessment data defined in:
services/assessment_service.py

The stored assessments are used by the lookup_assessments() LangChain tool when the agent needs current assessment information.

-- STATE MANAGEMENT --

The application maintains an AgentState object containing information about recent agent activity, including:
- Last recommendation
- Last tool call
- Action history
- Error count
- Last available study hours
- Last error

State transitions are logged during agent execution.

-- ERROR HANDLING --

If the agent encounters an error while processing a request, the application uses a fallback Recommendation rather than allowing the failure to propagate to the user.

The fallback response indicates that no recommendation is available and advises the user to review their stored assessments manually.