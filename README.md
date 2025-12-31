# 🌐 Browser AI Agent

A powerful, autonomous AI agent that can control your browser to perform tasks, fill out forms, and navigate the web in real-time. Designed to be fast, visible, and secure.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Playwright](https://img.shields.io/badge/playwright-async-green)

## ✨ Features

- **🚀 Live Streaming**: Real-time visual feedback of the agent's actions (2 FPS).
- **🧠 Multi-Provider Support**: Switch between **Google Gemini (1.5 Pro/Flash, 2.0 Flash)** and local models via **LM Studio**.
- **🛠️ Autonomous Tool Use**: The agent can navigate, click, type, and scroll autonomously to achieve your goals.
- **💾 Dynamic Memory**: Saves user information (names, emails, preferences) to remember for future form-filling.
- **⚡ Optimized Vision**: Uses compressed JPEG screenshots for ultra-fast performance.
- **🔒 Secure by Design**: Local config files and API keys are automatically ignored by git.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Browser Control**: Playwright (Async)
- **Frontend**: Vanilla JS / CSS / HTML
- **WebSocket**: Real-time log and screenshot streaming

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- [LM Studio](https://lmstudio.ai/) (Optional, for local LLM use)
- Google Gemini API Key (Optional, for cloud LLM use)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/browser-agent.git
   cd browser-agent
   ```

2. **Run the One-Click Launcher:**
   ```bash
   ./run_browser_agent.command
   ```
   *This will automatically set up the virtual environment, install dependencies, and start the server.*

3. **Open the Dashboard:**
   Navigate to `http://localhost:8000` in your browser.

## ⚙️ Configuration

- **Settings**: Use the **Settings** button in the UI to switch providers and update API keys.
- **Memory**: Use the **Memory** button to manage what the agent knows about you.
- **Environment**: Set `HEADLESS=true` in your environment variables to hide the browser window.

## 🤝 Contributing

We welcome contributions! Whether it's fixing bugs, adding new tools, or improving the UI.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
*Created with ❤️ by Rene Turcios and the AI Community.*
