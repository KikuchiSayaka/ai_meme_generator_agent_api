import asyncio
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import requests
from langchain_core.messages import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import logging


logging.basicConfig(level=logging.DEBUG)
load_dotenv()


async def generate_meme(
    query: str,
    model_choice: str,
    api_key: str,
    imgflip_username: str,
    imgflip_password: str,
) -> str | None:
    if model_choice == "Claude":
        llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=api_key)
    else:
        llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=api_key, temperature=0.7)

    # Get list of templates BEFORE generating prompt
    templates_resp = requests.get("https://api.imgflip.com/get_memes").json()
    templates = templates_resp["data"]["memes"]
    template_map = {t["name"].lower(): t["id"] for t in templates}
    allowed_templates = "\n".join(f"- {t}" for t in sorted(template_map.keys())[:50])

    class MemeSchema(BaseModel):
        template_name: str = Field(description="Name of the meme template")
        top_text: str = Field(description="Top caption text")
        bottom_text: str = Field(description="Bottom caption text")

    parser = PydanticOutputParser(pydantic_object=MemeSchema)
    format_instructions = parser.get_format_instructions()

    prompt = (
        f"You are a meme generator. Given the topic '{query}', generate a meme using one of the following official Imgflip meme templates ONLY. "
        f"Do not make up any new template names. Choose strictly from this list:\n{allowed_templates}\n"
        f"Return your output in this format:\n{format_instructions}"
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    try:
        meme_data: MemeSchema = parser.parse(response.content)
    except Exception as e:
        raise ValueError(
            f"Failed to parse meme JSON: {e}\n\nLLM Output:\n{response.content}"
        )

    template_name = meme_data.template_name
    top_text = meme_data.top_text
    bottom_text = meme_data.bottom_text

    # template name validation
    templates_resp = requests.get("https://api.imgflip.com/get_memes").json()
    templates = templates_resp["data"]["memes"]
    template_map = {t["name"].lower(): t["id"] for t in templates}
    normalized_name = template_name.strip().lower()
    if normalized_name not in template_map:
        raise ValueError(
            f"Template not found: '{template_name}' (normalized: '{normalized_name}')"
        )
    template_id = template_map[normalized_name]

    # Imgflip API call to caption the image
    params = {
        "template_id": template_id,
        "username": imgflip_username,
        "password": imgflip_password,
        "text0": top_text,
        "text1": bottom_text,
    }
    caption_resp = requests.post(
        "https://api.imgflip.com/caption_image", params=params
    ).json()
    if not caption_resp["success"]:
        raise RuntimeError(
            "Imgflip API failed: " + caption_resp.get("error_message", "unknown error")
        )

    return caption_resp["data"]["url"]


def main():
    # .env file configuration
    default_claude_key = os.getenv("ANTHROPIC_API_KEY", "")
    default_openai_key = os.getenv("OPENAI_API_KEY", "")
    default_imgflip_username = os.getenv("IMGFLIP_USERNAME", "")
    default_imgflip_password = os.getenv("IMGFLIP_PASSWORD", "")
    if not default_openai_key:
        logging.warning("OPENAI_API_KEY not found in .env")

    st.title("AI Meme Generator Agent (API-based)")
    st.info(
        "This is a customized version of the original AI Meme Generator Agent. Instead of browser automation with imgflip.com, this version uses the **official Imgflip API** for meme generation."
    )

    # Sidebar configuration
    with st.sidebar:
        st.markdown(
            '<p class="sidebar-header">⚙️ Model Configuration</p>',
            unsafe_allow_html=True,
        )

        # Model selection
        model_choice = st.selectbox(
            "Select AI Model",
            ["Claude", "OpenAI"],
            index=0,
            help="Choose which LLM to use for meme generation",
        )

        # API key input
        if model_choice == "Claude":
            api_key = st.text_input(
                "Claude API Key",
                type="password",
                value=default_claude_key,
                help="Get your API key from https://console.anthropic.com",
            )
        else:
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=default_openai_key,
                help="Get your API key from https://platform.openai.com",
            )

        imgflip_username = st.text_input(
            "Imgflip Username",
            value=default_imgflip_username,
            help="Your Imgflip username obtained from Settings",
        )
        imgflip_password = st.text_input(
            "Imgflip Password",
            type="password",
            value=default_imgflip_password,
            help="Your Imgflip password (set in Settings)",
        )

    # Main content area
    st.markdown(
        '<p class="header-text">🎨 Describe Your Meme Concept</p>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Meme Idea Input",
        placeholder="Example: 'Frontend vs Backend developers arguing about naming conventions.'",
        label_visibility="collapsed",
    )

    if st.button("Generate Meme 🚀"):
        if not api_key:
            st.warning(f"Please provide the {model_choice} API key")
            st.stop()
        if not query:
            st.warning("Please enter a meme idea")
            st.stop()

        with st.spinner(f"🧠 {model_choice} is generating your meme..."):
            try:
                meme_url = asyncio.run(
                    generate_meme(
                        query, model_choice, api_key, imgflip_username, imgflip_password
                    )
                )

                if meme_url:
                    st.success("✅ Meme Generated Successfully!")
                    st.image(
                        meme_url,
                        caption="Generated Meme Preview",
                        use_container_width=True,
                    )
                    st.markdown(
                        f"""
                        **Direct Link:** [Open in ImgFlip]({meme_url})  
                        **Embed URL:** `{meme_url}`
                    """
                    )
                else:
                    st.error(
                        "❌ Failed to generate meme. Please try again with a different prompt."
                    )

            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
