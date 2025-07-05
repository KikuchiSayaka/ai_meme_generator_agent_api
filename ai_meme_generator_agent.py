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
from meme_chain import meme_chain

# Only show warnings and errors, not debug messages
logging.basicConfig(level=logging.WARNING)
# Suppress debug logs from urllib3 and httpcore
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

load_dotenv()


def get_template_selection(query: str, model_choice: str, api_key: str) -> str:
    """Select the most appropriate 2-box meme template for the given query."""
    if model_choice == "Claude":
        llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=api_key)
    else:
        llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=api_key, temperature=0.7)

    # Get list of templates
    templates_resp = requests.get("https://api.imgflip.com/get_memes").json()
    templates = templates_resp["data"]["memes"]

    # Filter to ONLY show 2-box templates (the most common and effective format)
    template_list = []
    two_box_templates = []

    # Collect only templates with exactly 2 boxes
    for t in templates:
        if t["box_count"] == 2:  # Only 2-box templates
            two_box_templates.append(t)

    # Show the most popular 2-box templates
    for t in two_box_templates[:30]:
        template_list.append(f"- {t['name']} (2 text boxes)")

    allowed_templates = "\n".join(template_list)

    class TemplateSchema(BaseModel):
        template_name: str = Field(description="Name of the meme template to use")

    parser = PydanticOutputParser(pydantic_object=TemplateSchema)
    format_instructions = parser.get_format_instructions()

    prompt = (
        f"You are a meme generator. Given the topic '{query}', select the most appropriate meme template from the following list. "
        f"All templates have exactly 2 text boxes (top and bottom), which is the standard meme format.\n\n"
        f"Available templates (all with 2 boxes):\n{allowed_templates}\n\n"
        f"Return your output in this format:\n{format_instructions}"
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        template_data: TemplateSchema = parser.parse(response.content)
        # Clean the template name (remove box count info if included)
        template_name = template_data.template_name.split(" (")[0]
        return template_name
    except Exception as e:
        raise ValueError(f"Failed to parse template selection: {e}")


def load_environment_config():
    """Load configuration from environment variables."""
    config = {
        "claude_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "openai_key": os.getenv("OPENAI_API_KEY", ""),
        "imgflip_username": os.getenv("IMGFLIP_USERNAME", ""),
        "imgflip_password": os.getenv("IMGFLIP_PASSWORD", ""),
    }

    if not config["openai_key"]:
        logging.warning("OPENAI_API_KEY not found in .env")

    # Set Imgflip credentials as environment variables for meme_chain
    if config["imgflip_username"]:
        os.environ["IMGFLIP_USERNAME"] = config["imgflip_username"]
    if config["imgflip_password"]:
        os.environ["IMGFLIP_PASSWORD"] = config["imgflip_password"]

    return config


def setup_page_header():
    """Set up the main page title and description."""
    st.title("🤖 AI Meme Generator with LangGraph")
    st.info(
        "Generate memes using AI! This tool creates multiple caption options and selects the funniest one."
    )


def create_sidebar(config: dict) -> tuple[str, str, str, str]:
    """Create sidebar with model selection and API key inputs."""
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

        # API key input based on model choice
        if model_choice == "Claude":
            api_key = st.text_input(
                "Claude API Key",
                type="password",
                value=config["claude_key"],
                help="Get your API key from https://console.anthropic.com",
            )
        else:
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=config["openai_key"],
                help="Get your API key from https://platform.openai.com",
            )

        # Imgflip credentials
        imgflip_username = st.text_input(
            "Imgflip Username",
            value=config["imgflip_username"],
            help="Your Imgflip username for meme generation",
        )
        imgflip_password = st.text_input(
            "Imgflip Password",
            type="password",
            value=config["imgflip_password"],
            help="Your Imgflip password",
        )

    return model_choice, api_key, imgflip_username, imgflip_password


def get_user_input() -> str:
    """Get meme idea input from user."""
    st.markdown(
        '<p class="header-text">🎨 Describe Your Meme Concept</p>',
        unsafe_allow_html=True,
    )

    return st.text_input(
        "Meme Idea Input",
        placeholder="Example: 'When you fix a bug but create three new ones'",
        label_visibility="collapsed",
    )


def validate_inputs(
    api_key: str,
    query: str,
    imgflip_username: str,
    imgflip_password: str,
    model_choice: str,
) -> bool:
    """Validate all required inputs are provided."""
    if not api_key:
        st.warning(f"Please provide the {model_choice} API key")
        return False
    if not query:
        st.warning("Please enter a meme idea")
        return False
    if not imgflip_username or not imgflip_password:
        st.warning("Please provide Imgflip credentials")
        return False
    return True


def display_caption_selection_process(result: dict):
    """Display the caption selection process in an expandable section."""
    caption_proposals = result.get("caption_proposals", [])
    if caption_proposals and len(caption_proposals) >= 2:
        with st.expander("🎭 Caption Selection Process"):
            st.write("**Option 1:**")
            st.write(f"- Top: {caption_proposals[0][0]}")
            st.write(f"- Bottom: {caption_proposals[0][1]}")

            st.write("\n**Option 2:**")
            st.write(f"- Top: {caption_proposals[1][0]}")
            st.write(f"- Bottom: {caption_proposals[1][1]}")

            selected_idx = result.get("selected_caption_index", 0)
            reasoning = result.get("selection_reasoning", "")
            st.write(f"\n**Selected:** Option {selected_idx + 1}")
            st.write(f"**Reasoning:** {reasoning}")


def display_final_result(result: dict, meme_url: str):
    """Display the final meme result with captions and image."""
    captions = result.get("captions", [])

    st.success("✅ Meme Generated Successfully!")

    # Show caption selection process
    display_caption_selection_process(result)

    # Display final captions
    if captions:
        st.write("**Final Captions:**")
        st.write(f"Top: {captions[0]}")
        st.write(f"Bottom: {captions[1]}")

    # Display the meme image
    st.image(
        meme_url,
        caption="Generated Meme Preview",
        use_container_width=True,
    )

    # Provide direct link
    st.markdown(
        f"""
        **Direct Link:** [Open in ImgFlip]({meme_url})  
        **Embed URL:** `{meme_url}`
    """
    )


def generate_meme_workflow(
    query: str,
    model_choice: str,
    api_key: str,
    imgflip_username: str,
    imgflip_password: str,
):
    """Execute the complete meme generation workflow."""
    # Template selection phase
    with st.spinner("🎯 Selecting the best meme template..."):
        template_name = get_template_selection(query, model_choice, api_key)
        st.info(f"📋 Selected template: **{template_name}**")

    # Set environment variables for meme_chain
    os.environ["IMGFLIP_USERNAME"] = imgflip_username
    os.environ["IMGFLIP_PASSWORD"] = imgflip_password

    # Caption generation and meme creation phase
    with st.spinner("🎨 Generating and evaluating caption options..."):
        from langchain_core.runnables import RunnableConfig

        config = RunnableConfig(
            configurable={
                "model_choice": model_choice,
                "api_key": api_key,
            }
        )

        result = meme_chain.invoke(
            {
                "query": query,
                "template_name": template_name,
            },
            config=config,
        )

        meme_url = result.get("meme_url")

        if meme_url:
            display_final_result(result, meme_url)
        else:
            st.error(
                "❌ Failed to generate meme. Please try again with a different prompt."
            )


def main():
    """Main application entry point."""
    # Load environment configuration
    config = load_environment_config()

    # Set up page
    setup_page_header()

    # Create sidebar and get user inputs
    model_choice, api_key, imgflip_username, imgflip_password = create_sidebar(config)

    # Get meme idea from user
    query = get_user_input()

    # Generate meme when button is clicked
    if st.button("Generate Meme 🚀"):
        if not validate_inputs(
            api_key, query, imgflip_username, imgflip_password, model_choice
        ):
            st.stop()

        with st.spinner(f"🧠 {model_choice} is analyzing your meme idea..."):
            try:
                generate_meme_workflow(
                    query, model_choice, api_key, imgflip_username, imgflip_password
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
