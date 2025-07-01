from typing import List
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from cfg import OPEN_API_KEY

def rewrite_prompt_with_feedback(original_prompt: str, user_feedback: str, visual_goal: List[str] = None) -> str:
    goal_text = "\n".join(f"- {g}" for g in (visual_goal or []))

    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.4,
        openai_api_key=OPEN_API_KEY  
    )

    messages = [
        SystemMessage(content="You are an expert visual prompt editor for Stable Diffusion. You rewrite image prompts based on user feedback to improve rendering quality."),
        HumanMessage(content=f"""
Original Prompt:
\"{original_prompt}\"

User Feedback:
\"{user_feedback}\"

Visual Goals:
{goal_text if goal_text else "None"}

Update the prompt to reflect the user's feedback. Be precise and visual. Return the final revised prompt only, no explanations or markdown.
""")
    ]

    return llm(messages).content.strip()