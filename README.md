# Browser AI Agent

An open-source autonomous browser agent that can navigate websites, interact with web applications, and execute multi-step tasks using AI. This is the core browser automation engine that powers [TaskCato.com](https://taskcato.com) - the AI co-founder platform for founders and startups.

## 🎯 What Is This?

This is a **headless browser agent** controlled by AI (LLM) that can:
- Navigate websites autonomously
- Fill out forms and interact with web UIs
- Extract data and take screenshots
- Execute multi-step workflows
- Remember context across sessions
- Run multiple browser instances simultaneously

Think of it as "Selenium meets ChatGPT" - but the AI decides what to do next.

## 🆚 Open Source vs TaskCato Premium

| Feature | Open Source (This Repo) | TaskCato.com (SaaS) |
|---------|------------------------|---------------------|
| **Browser Automation** | ✅ Full access | ✅ Enhanced |
| **AI-Powered Navigation** | ✅ Yes | ✅ Yes |
| **Multi-Instance Support** | ✅ Up to 9 browsers | ✅ Unlimited |
| **Integrations** | ❌ None | ✅ 15+ (HubSpot, Gmail, etc.) |
| **Voice Calls** | ❌ No | ✅ AI phone calls |
| **Persistent Memory** | ✅ Basic | ✅ Advanced company context |
| **Team Collaboration** | ❌ No | ✅ Yes |
| **Support** | Community | Priority |
| **Hosting** | Self-hosted | Cloud-hosted |
| **Price** | Free | $49/month |

**Use this open-source version if:**
- You want to build your own automation tools
- You need browser automation for personal projects
- You're a developer who wants to customize the AI behavior
- You prefer self-hosting

**Use TaskCato.com if:**
- You're a founder who needs end-to-end business automation
- You want integrations with CRM, email, calendar, etc.
- You need AI that can make phone calls and manage your entire workflow
- You want a managed service with support

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+ (for Electron launcher)
- LM Studio or OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/CloudCorpRecords/browserboi.git
cd browserboi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running the Agent

**Option 1: Simple Terminal Launch (Mac/Linux)**
```bash
./START_BROWSER_AGENT.command
```

**Option 2: Electron App (Cross-Platform)**
```bash
cd launcher
npm install
npm start
```

**Option 3: Manual Start**
```bash
python -m uvicorn browser_agent.server.main:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser.

### Configuration

1. **Set up your LLM**:
   - Open Settings in the web UI
   - Choose LM Studio (local) or Gemini (cloud)
   - For LM Studio: Install from https://lmstudio.ai and run a model
   - For Gemini: Add your API key

2. **Give it a task**:
   ```
   "Research the top 5 AI startups and take screenshots of their homepages"
   ```

The agent will autonomously navigate, research, and complete the task.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Electron App (Optional UI)             │
│  - Dashboard                             │
│  - 9-Grid Browser View                   │
│  - Real-time Logs                        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  FastAPI Server (Port 8000)              │
│  - WebSocket for real-time updates      │
│  - Multi-instance management (1-9)      │
│  - RESTful API                           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  AI Agent Core                           │
│  - LLM Integration (Gemini/LM Studio)   │
│  - Task Planning & Execution             │
│  - Memory Management                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Browser Manager (Playwright)            │
│  - Headless Chromium                     │
│  - Screenshot Capture                    │
│  - Page Interaction                      │
└─────────────────────────────────────────┘
```

## 📚 Features

### Core Capabilities
- **Autonomous Navigation**: AI decides where to click, what to type
- **Multi-Step Workflows**: Chain complex actions together
- **Context Awareness**: Remembers previous actions and decisions
- **Screenshot Analysis**: AI "sees" the page and makes decisions
- **Text Extraction**: Reads page content for better understanding
- **Session Persistence**: Maintains cookies and login state

### Advanced Features
- **9-Instance Grid**: Run up to 9 browser agents simultaneously
- **Headless Mode**: Runs in background without visible browser
- **CDP Support**: Chrome DevTools Protocol for advanced control
- **Memory System**: Stores user preferences and company context
- **Streaming Logs**: Real-time visibility into agent actions

## 🛠️ Development

### Project Structure
```
browser_agent/
├── core/
│   ├── agent.py          # Main AI agent logic
│   ├── browser.py        # Playwright browser manager
│   ├── llm.py           # LLM integration
│   └── memory.py        # Context & memory management
├── server/
│   ├── main.py          # FastAPI server
│   └── static/          # Web UI
└── tools/               # Agent tools (click, type, etc.)

launcher/                # Electron desktop app
├── main.js             # Electron main process
├── index.html          # Loading screen
└── package.json        # Dependencies
```

### API Endpoints

**Start a task:**
```bash
curl -X POST http://localhost:8000/api/start/1 \
  -H "Content-Type: application/json" \
  -d '{"task":"Search for AI news on Hacker News"}'
```

**Stop an agent:**
```bash
curl -X POST http://localhost:8000/api/stop/1
```

**Health check:**
```bash
curl http://localhost:8000/api/diagnostic
```

### WebSocket Events
Connect to `ws://localhost:8000/ws/1` for real-time updates:
- `status` - Agent status changes
- `log` - Action logs
- `screenshot` - New screenshots
- `error` - Error messages

## 🤝 Contributing

We welcome contributions! This is an open-source project maintained by the TaskCato team.

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas We Need Help
- 🐛 Bug fixes and stability improvements
- 📝 Documentation and examples
- 🔌 New tool integrations
- 🧪 Test coverage
- 🎨 UI/UX improvements

## 📖 Use Cases

### Web Scraping
```python
"Go to ProductHunt and extract the top 10 products today"
```

### Form Automation
```python
"Fill out the contact form on example.com with my info"
```

### Research
```python
"Research the pricing pages of Stripe, Square, and PayPal"
```

### Testing
```python
"Test the login flow on staging.myapp.com"
```

### Data Collection
```python
"Find email addresses of CTOs at Series A fintech startups"
```

## ⚙️ Configuration

### Environment Variables
```bash
# LLM Provider
LLM_PROVIDER=lm_studio  # or 'gemini'
GEMINI_API_KEY=your_key_here

# Browser Settings
HEADLESS=true  # Run browser in headless mode
VIEWPORT_WIDTH=1280
VIEWPORT_HEIGHT=800

# Server
PORT=8000
HOST=0.0.0.0
```

### Settings File
Settings are stored in `browser_agent/data/settings.json`:
```json
{
  "provider": "lm_studio",
  "lm_studio_url": "http://localhost:1234/v1",
  "lm_studio_model": "qwen/qwen3-vl-8b",
  "gemini_api_key": "",
  "gemini_model": "gemini-2.0-flash-exp"
}
```

## 🔒 Security & Privacy

- **No Data Collection**: All data stays on your machine
- **Local LLM Support**: Use LM Studio for complete privacy
- **Session Isolation**: Each browser instance is isolated
- **No Telemetry**: We don't track usage

## 🐛 Known Issues

- **UI Message Display**: Agent responses may not appear in chat (check terminal logs)
- **Browser View Content**: Grid cells show blank instead of live browser content
- **Windows Support**: Electron app tested primarily on macOS

See [Issues](https://github.com/CloudCorpRecords/browserboi/issues) for full list.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🌟 About TaskCato

This browser agent is the core technology behind [TaskCato.com](https://taskcato.com) - an AI co-founder platform that helps founders automate their entire business workflow.

**TaskCato adds:**
- 15+ SaaS integrations (HubSpot, Gmail, Slack, etc.)
- AI voice calling capabilities
- Advanced persistent memory
- Team collaboration features
- Managed cloud hosting
- Priority support

**Try TaskCato free:** https://taskcato.com

## 💬 Community

- **Discord**: [Join our community](https://discord.gg/taskcato)
- **Twitter**: [@TaskCato](https://twitter.com/taskcato)
- **Issues**: [GitHub Issues](https://github.com/CloudCorpRecords/browserboi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/CloudCorpRecords/browserboi/discussions)

## 🙏 Acknowledgments

Built with:
- [Playwright](https://playwright.dev/) - Browser automation
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Electron](https://www.electronjs.org/) - Desktop app
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI capabilities
- [LM Studio](https://lmstudio.ai/) - Local LLM support

---

**Made with ❤️ by the TaskCato team**

*Building the future of autonomous work, one browser action at a time.*
