# AI Meme Generator Agent (API-based)

This is a customized version of the original AI Meme Generator Agent. Instead of browser automation with imgflip.com, this version uses the **official Imgflip API** for meme generation.

## Features

- **Imgflip API Integration**

  - Uses official Imgflip API for generating memes
  - Avoids scraping and prevents being blocked

- **Multi-LLM Support (Customizable)**

  - Claude 3.5 Sonnet (Anthropic)
  - GPT-4o (OpenAI)
  - Easily extensible to others
  - DeepSeek support removed

- **Streamlined Meme Generation Workflow**

  - Uses your text prompts to create meme captions
  - Supports template search and caption filling
  - Automatically handles retries on failure

- **User Interface**
  - Built with Streamlit
  - Simple sidebar to manage API keys and models
  - Preview generated memes directly

## Required API Keys

- [OpenAI](https://platform.openai.com/account/api-keys) (for GPT-4o)
- [Anthropic](https://console.anthropic.com/settings/keys) (for Claude)
- [Imgflip](https://imgflip.com/api) (requires username & password)

## How to Run

1. Clone this repository

   ```bash
   git clone https://github.com/YOUR_USERNAME/AI_meme_generator.git
   cd AI_meme_generator
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app
   ```bash
   streamlit run ai_meme_generator_agent.py
   ```

## Configuration (.env)

You can store your API keys and Imgflip credentials in a .env file to avoid typing them manually every time.
Create a .env file in the project root:

```markdown
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
IMGFLIP_USERNAME=your-imgflip-username
IMGFLIP_PASSWORD=your-imgflip-password
```

Do not commit .env to version control.
Add it to your .gitignore.

If .env exists, the app will automatically load these credentials as default values in the sidebar.

## License

This project is licensed under the [Apache License 2.0](./LICENSE), based on the [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) project.
