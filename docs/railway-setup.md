# Railway Environment Setup

## Workspace Information
- **Workspace Name**: `ain`
- **Purpose**: Incubation environment for AIN (AI-Native) Core.

## CLI Commands for `aia` Workspace

To ensure you are working within the correct workspace and project, use the following commands:

### 1. Login & Workspace Selection
```bash
# Login to Railway
railway login

# List all available workspaces
railway vars --workspace

# (If needed) Link to the specific project once created
railway link
```

### 2. Project Initialization
When you are ready to create the project within the `aia` workspace:
1. Go to the [Railway Dashboard](https://railway.app/).
2. Select the `aia` workspace.
3. Create a **New Project**.
4. Then, in your local terminal:
```bash
railway link [PROJECT_ID]
```

### 3. Environment Variables
The following variables must be set in the Railway project dashboard:
- `GEMINI_API_KEY`: API Key from Google AI Studio.
- `GITHUB_TOKEN`: Classic PAT with `repo` scope.
- `REPO_NAME`: `ain-lang/ain`
- `TELEGRAM_TOKEN`: Token for `@AinOverseerBot`
- `TELEGRAM_CHAT_ID`: Your personal Telegram Chat ID

---

## Communication Channel
- **Bot Name**: `@AinOverseerBot`
- **Role**: The bridge between AIN's internal thoughts and the User.

