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


def get_required_box_count(query: str, model_choice: str, api_key: str) -> int:
    """Always return 2 for standard meme format"""
    return 2  # Most memes work best with 2 boxes


def get_template_selection(
    query: str, model_choice: str, api_key: str, max_boxes: int = 2
) -> str:
    """Get template selection from LLM - only 2-box templates"""
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


def main():
    # .env file configuration
    default_claude_key = os.getenv("ANTHROPIC_API_KEY", "")
    default_openai_key = os.getenv("OPENAI_API_KEY", "")
    default_imgflip_username = os.getenv("IMGFLIP_USERNAME", "")
    default_imgflip_password = os.getenv("IMGFLIP_PASSWORD", "")
    if not default_openai_key:
        logging.warning("OPENAI_API_KEY not found in .env")

    # Set Imgflip credentials as environment variables for meme_chain
    if default_imgflip_username:
        os.environ["IMGFLIP_USERNAME"] = default_imgflip_username
    if default_imgflip_password:
        os.environ["IMGFLIP_PASSWORD"] = default_imgflip_password

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
        placeholder="Example: 'When the frontend finally fixes a bug... but it's actually a backend issue.'",
        label_visibility="collapsed",
    )

    if st.button("Generate Meme 🚀"):
        if not api_key:
            st.warning(f"Please provide the {model_choice} API key")
            st.stop()
        if not query:
            st.warning("Please enter a meme idea")
            st.stop()
        if not imgflip_username or not imgflip_password:
            st.warning("Please provide Imgflip credentials")
            st.stop()

        with st.spinner(f"🧠 {model_choice} is analyzing your meme idea..."):
            try:
                # Always use 2-box templates (standard meme format)
                required_boxes = 2
                st.info("📊 Creating standard 2-panel meme")

                # Get template selection (2-box templates only)
                with st.spinner("🎯 Selecting the best 2-box template..."):
                    template_name = get_template_selection(
                        query, model_choice, api_key, max_boxes=2
                    )

                    # Verify the selected template actually has enough boxes
                    templates_resp = requests.get(
                        "https://api.imgflip.com/get_memes"
                    ).json()
                    templates = templates_resp["data"]["memes"]
                    selected_template = next(
                        (
                            t
                            for t in templates
                            if t["name"].lower() == template_name.lower()
                        ),
                        None,
                    )

                    if selected_template:
                        actual_boxes = selected_template["box_count"]
                        st.info(
                            f"📋 Selected template: **{template_name}** (has {actual_boxes} text boxes)"
                        )
                        if actual_boxes < required_boxes:
                            st.warning(
                                f"⚠️ This template only supports {actual_boxes} boxes, but {required_boxes} were requested."
                            )
                    else:
                        st.info(f"📋 Selected template: **{template_name}**")

                # Update environment variables for meme_chain
                os.environ["IMGFLIP_USERNAME"] = imgflip_username
                os.environ["IMGFLIP_PASSWORD"] = imgflip_password

                with st.spinner(f"🎨 Generating captions for {template_name}..."):
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
                    captions = result.get("captions", [])
                    actual_box_count = result.get("box_count", 0)

                    if meme_url:
                        st.success("✅ Meme Generated Successfully!")

                        # Display actual template info
                        if actual_box_count:
                            st.info(
                                f"ℹ️ Template **{template_name}** actually supports **{actual_box_count}** text boxes"
                            )

                        # Display caption selection process
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

                        # Display the final captions
                        if captions:
                            st.write("**Final Captions:**")
                            st.write(f"Top: {captions[0]}")
                            st.write(f"Bottom: {captions[1]}")

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
