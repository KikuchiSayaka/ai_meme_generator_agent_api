from langgraph.graph import StateGraph, END
from langchain_core.runnables import Runnable
from typing import TypedDict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import requests
import os
from dotenv import load_dotenv

load_dotenv()


def get_llm(model_choice: str, api_key: str):
    """Create LLM instance based on model choice."""
    if model_choice == "Claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=api_key)
    return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)




class MemeState(TypedDict):
    template_name: str
    box_count: int
    captions: List[str]
    meme_url: str
    query: str
    caption_proposals: List[List[str]]  # Multiple caption options
    selected_caption_index: int  # Which caption was selected
    selection_reasoning: str  # Why this caption was chosen


def get_template_info(state: MemeState) -> MemeState:
    """Fetch template information from Imgflip API."""
    template_name = state["template_name"]
    templates = requests.get("https://api.imgflip.com/get_memes").json()["data"]["memes"]
    
    match = next(
        (t for t in templates if t["name"].lower() == template_name.lower()), None
    )
    if not match:
        raise ValueError(f"Template '{template_name}' not found")
    
    state["box_count"] = match["box_count"]
    return state


def generate_multiple_captions(state: MemeState, config: dict) -> MemeState:
    """Generate 2 different caption proposals for the template."""
    configurable = config.get("configurable", {})
    model_choice = configurable.get("model_choice", "OpenAI")
    api_key = configurable.get("api_key", os.getenv("OPENAI_API_KEY"))
    
    llm = get_llm(model_choice, api_key)
    proposals = []
    
    # Generate 2 different caption sets
    for i in range(2):
        prompt = f"""Generate meme captions (version {i+1}) for this idea: {state['query']}
        
{'Create a unique and funny take on this idea.' if i == 0 else 'Create a different version - try another angle or style of humor.'}
        
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
                captions.extend([''] * (2 - len(captions)))
            elif len(captions) > 2:
                captions = captions[:2]
                
            proposals.append(captions)
        except Exception as e:
            # If parsing fails, create default captions
            proposals.append([f"Top Text {i+1}", f"Bottom Text {i+1}"])
            # Log errors silently to avoid console spam
    
    state["caption_proposals"] = proposals
    return state


def select_best_caption(state: MemeState, config: dict) -> MemeState:
    """Use LLM to evaluate and select the funniest caption set."""
    configurable = config.get("configurable", {})
    model_choice = configurable.get("model_choice", "OpenAI")
    api_key = configurable.get("api_key", os.getenv("OPENAI_API_KEY"))
    
    llm = get_llm(model_choice, api_key)
    
    prompt = f"""Evaluate these two meme caption options for the idea: '{state['query']}'
    
Option 1:
- Top: "{state['caption_proposals'][0][0]}"
- Bottom: "{state['caption_proposals'][0][1]}"

Option 2:
- Top: "{state['caption_proposals'][1][0]}"
- Bottom: "{state['caption_proposals'][1][1]}"

Which option is funnier and why? Consider:
- Comedic timing
- Cleverness/wit
- How well it fits the meme format
- Overall humor impact

Return a JSON object:
{{
    "selected": 1 or 2,
    "reasoning": "Brief explanation (1-2 sentences)"
}}
"""
    
    msg = HumanMessage(content=prompt)
    response = llm.invoke([msg])
    
    try:
        import json
        import re
        content = response.content.strip()
        
        # Find JSON in response
        json_match = re.search(r'\{.*?\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
        else:
            result = json.loads(content)
        
        selected_idx = result.get("selected", 1) - 1
        if selected_idx not in [0, 1]:
            selected_idx = 0
            
        state["selected_caption_index"] = selected_idx
        state["selection_reasoning"] = result.get("reasoning", "Selected as the funnier option.")
        state["captions"] = state["caption_proposals"][selected_idx]
    except Exception as e:
        # Default to first option if parsing fails
        state["selected_caption_index"] = 0
        state["selection_reasoning"] = "Selected first option by default."
        state["captions"] = state["caption_proposals"][0]
        # Log errors silently
    
    return state


def call_imgflip_api(state: MemeState) -> MemeState:
    """Generate final meme image using Imgflip API."""
    templates = requests.get("https://api.imgflip.com/get_memes").json()["data"]["memes"]
    
    match = next(
        (t for t in templates if t["name"].lower() == state["template_name"].lower()),
        None,
    )
    if not match:
        raise ValueError(f"Template '{state['template_name']}' not found")
    
    # Prepare API parameters
    params = {
        "template_id": match["id"],
        "username": os.getenv("IMGFLIP_USERNAME"),
        "password": os.getenv("IMGFLIP_PASSWORD"),
    }
    
    # Add captions as text parameters
    for i, caption in enumerate(state["captions"]):
        params[f"text{i}"] = caption
    
    # Make API call
    res = requests.post("https://api.imgflip.com/caption_image", params=params).json()
    
    if not res["success"]:
        raise RuntimeError(
            "Imgflip API failed: " + res.get("error_message", "Unknown error")
        )
    
    state["meme_url"] = res["data"]["url"]
    return state


# Define LangGraph workflow
builder = StateGraph(MemeState)

# Add workflow nodes
builder.add_node("get_template_info", get_template_info)
builder.add_node("generate_multiple_captions", generate_multiple_captions)
builder.add_node("select_best_caption", select_best_caption)
builder.add_node("call_imgflip_api", call_imgflip_api)

# Define workflow edges
builder.set_entry_point("get_template_info")
builder.add_edge("get_template_info", "generate_multiple_captions")
builder.add_edge("generate_multiple_captions", "select_best_caption")
builder.add_edge("select_best_caption", "call_imgflip_api")
builder.add_edge("call_imgflip_api", END)

# Compile the workflow
meme_chain: Runnable = builder.compile()
