from langgraph.graph import StateGraph, END
from langchain_core.runnables import Runnable
from typing import TypedDict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import requests
import os
from langchain_core.runnables import ConfigurableField
from dotenv import load_dotenv

load_dotenv()


def get_llm(model_choice: str, api_key: str):
    if model_choice == "Claude":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=api_key)
    return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)


llm = ChatOpenAI(
    model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
)


class MemeState(TypedDict):
    template_name: str
    box_count: int
    captions: List[str]
    meme_url: str
    query: str


def get_template_info(state: MemeState) -> MemeState:
    template_name = state["template_name"]
    templates = requests.get("https://api.imgflip.com/get_memes").json()["data"][
        "memes"
    ]
    match = next(
        (t for t in templates if t["name"].lower() == template_name.lower()), None
    )
    if not match:
        raise ValueError(f"Template '{template_name}' not found")
    state["box_count"] = match["box_count"]
    return state


def generate_captions(state: MemeState, config: dict) -> MemeState:
    # Extract configurable values from RunnableConfig
    configurable = config.get("configurable", {})
    model_choice = configurable.get("model_choice", "OpenAI")
    api_key = configurable.get("api_key", os.getenv("OPENAI_API_KEY"))
    
    llm = get_llm(model_choice, api_key)
    # Always generate exactly 2 captions for standard meme format
    prompt = f"""Generate exactly 2 short meme captions for this idea: {state['query']}. 
    
    Return ONLY a Python list with exactly 2 string elements: ["top text", "bottom text"]
    
    The first caption is typically the setup, the second is the punchline or reaction.
    Keep each caption short and punchy (under 10 words each).
    Do not include any explanatory text, just the Python list."""
    
    msg = HumanMessage(content=prompt)
    response = llm.invoke([msg])
    
    try:
        # Try to extract the list from the response
        content = response.content.strip()
        
        # Find the list in the response (between [ and ])
        import re
        list_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if list_match:
            list_str = list_match.group(0)
            # Use ast.literal_eval for safer evaluation
            import ast
            captions = ast.literal_eval(list_str)
        else:
            # Fallback: try to parse the entire content
            import ast
            captions = ast.literal_eval(content)
            
        # Ensure we have exactly 2 captions
        if len(captions) < 2:
            # Pad with empty strings if needed
            captions.extend([''] * (2 - len(captions)))
        elif len(captions) > 2:
            # Truncate to 2 if too many
            captions = captions[:2]
            
        state["captions"] = captions
    except Exception as e:
        # If all parsing fails, create default captions for 2-box meme
        state["captions"] = ["Top Text", "Bottom Text"]
        print(f"Warning: Failed to parse captions, using defaults. Error: {e}")
        print(f"Response was: {response.content}")
    
    return state


def call_imgflip_api(state: MemeState) -> MemeState:
    templates = requests.get("https://api.imgflip.com/get_memes").json()["data"][
        "memes"
    ]
    match = next(
        (t for t in templates if t["name"].lower() == state["template_name"].lower()),
        None,
    )
    if not match:
        raise ValueError(f"Template '{state['template_name']}' not found again")
    params = {
        "template_id": match["id"],
        "username": os.getenv("IMGFLIP_USERNAME"),
        "password": os.getenv("IMGFLIP_PASSWORD"),
    }
    for i, caption in enumerate(state["captions"]):
        params[f"text{i}"] = caption
    res = requests.post("https://api.imgflip.com/caption_image", params=params).json()
    if not res["success"]:
        raise RuntimeError(
            "Imgflip failed: " + res.get("error_message", "Unknown error")
        )
    state["meme_url"] = res["data"]["url"]
    return state


# Define graph
builder = StateGraph(MemeState)
builder.add_node("get_template_info", get_template_info)
builder.add_node("generate_captions", generate_captions)
builder.add_node("call_imgflip_api", call_imgflip_api)
builder.set_entry_point("get_template_info")
builder.add_edge("get_template_info", "generate_captions")
builder.add_edge("generate_captions", "call_imgflip_api")
builder.add_edge("call_imgflip_api", END)
meme_chain: Runnable = builder.compile()
