# 📧🤖 Gmail Calendar Automation

An intelligent automation agent using **Google ADK** and **Gmail and Google Calendar API**.  
It can read/process your emails and automatically create or update calendar events.  

---

## ⚡ Quick Start

### 1️⃣ Clone the repo
```bash
git clone https://github.com/rymouche98/gmail_calendar_automation.git
cd gmail_calendar_automation
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Setup environment
Copy the example env file and edit it with your credentials:
```bash
cp .env.example .env
```

- `GOOGLE_API_KEY` → your Google API key  
- `CREDENTIALS` → path to `credentials.json` (downloaded from Google Cloud Console)  
- `TOKEN` → path to `token.json` (will be created at first run)  

---

### 4️⃣ Run the agent
```bash
adk web
```

This will start the ADK Web UI where you can interact with your **Gmail Calendar Agent**.
