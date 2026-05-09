Context:
I am starting a brand new project from scratch. Nothing exists yet.
I have a copilot-instructions.md file in my .github folder that describes
the folder structure and tech stack I want to use.

Goal:
Set up the empty project structure for both the frontend and backend.
I don't want any feature code yet — just the scaffolding and config.

For the backend (Python + FastAPI):
- Create the folder structure described in copilot-instructions.md
- Create a main entry point file for the FastAPI app
- Create a config file that reads settings from a .env file
- Create a requirements.txt with all the libraries I'll need for the full project
- Create a .env.example file that lists all the environment variables I'll need,
  with the values left blank

For the frontend (React + TypeScript + Tailwind CSS):
- Set up a new React project using Vite
- Create a file for making API calls to the backend
- Create a file for shared TypeScript types (empty for now)

Rules:
- No feature code — structure and config files only
- API keys and secrets must never be written directly in code files,
  only loaded from environment variables
- The frontend should be configured to talk to the backend on localhost

Output:
The full folder structure with empty or minimal files in place,
ready for feature development to begin.

