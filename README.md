# AI Meme Generator with LangGraph

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://github.com/KikuchiSayaka/ai_meme_generator_agent_api)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/🦜🔗-LangChain-green.svg)](https://github.com/langchain-ai/langchain)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> An intelligent meme generator powered by **Streamlit**, **LangChain**, and **LangGraph** that creates multiple caption options and uses AI to select the funniest one!

<div align="center">
  <img src="assets/demo_img.png" alt="AI Meme Generator Demo" width="700">
</div>

## Live Demo

Try the app here:
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ai-meme-generator-with-langchain.streamlit.app/)

## Required API Keys

1. **[OpenAI](https://platform.openai.com/account/api-keys)** or **[Anthropic](https://console.anthropic.com/settings/keys)**
   - For AI-powered caption generation and selection
2. **[Imgflip](https://imgflip.com/api)**
   - Free account required
   - Uses official API (no scraping)

## Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/KikuchiSayaka/ai_meme_generator_agent_api.git
   cd ai_meme_generator_agent_api
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional)

   Create a `.env` file in the project root:

   ```
   OPENAI_API_KEY=your-openai-key-here
   ANTHROPIC_API_KEY=your-anthropic-key-here
   IMGFLIP_USERNAME=your-imgflip-username
   IMGFLIP_PASSWORD=your-imgflip-password
   ```

4. **Run the application**

   ```bash
   streamlit run ai_meme_generator_agent.py
   ```

5. **Open your browser**
   - Navigate to `http://localhost:8501`
   - Enter your API keys in the sidebar (if not using .env)
   - Type your meme idea and click "Generate Meme 🚀"

### Example Workflow

```
User Input: "When you fix a bug but create three new ones"
↓
AI selects: Drake Hotline Bling template
↓
Generates Option 1:
- Top: "Fixing one bug cleanly"
- Bottom: "Creating three new bugs while fixing"
↓
Generates Option 2:
- Top: "Writing bug-free code"
- Bottom: "My code spawning bugs like rabbits"
↓
AI Selection: Option 2 (more vivid and relatable humor)
↓
Final meme created!
```

## Technical Stack

### Core Technologies

- **[Streamlit](https://streamlit.io/)** - Build and deploy data apps in minutes
- **[LangChain](https://python.langchain.com/)** - Framework for developing LLM applications
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Build stateful, multi-actor applications with LLMs
- **[Anthropic Claude](https://www.anthropic.com/)** & **[OpenAI](https://openai.com/)** - State-of-the-art language models
- **[Imgflip API](https://imgflip.com/api)** - Programmatic meme generation

### Architecture Highlights

```
Streamlit UI
    ↓
LangGraph Orchestration
    ↓
LangChain LLM Calls → Multiple AI Models
    ↓
Imgflip API → Final Meme
```

## Security Notes

- API keys are never stored permanently
- `.env` file is gitignored by default
- All API calls use HTTPS
- No browser automation or scraping

## License

This project is licensed under the [Apache License 2.0](./LICENSE), based on the [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) project.

## Contributing

Contributions are welcome! Feel free to:

- Add support for new LLMs
- Improve caption generation prompts
- Enhance the UI/UX
- Add new features

<details>
  <summary>Keywords</summary>

`streamlit`, `langchain`, `langgraph`, `llm`, `ai`, `meme-generator`, `claude`, `gpt`, `python`, `prompt-engineering`, `workflow-orchestration`

</details>
