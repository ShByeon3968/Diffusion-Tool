from typing import List
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from cfg import OPEN_API_KEY


def rewrite_prompt_for_omnigen_editing(original_prompt: str, user_feedback: str) -> str:
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.4,
        openai_api_key=OPEN_API_KEY
    )

    # Step 1: Visual Goal 추론 (OmniGen 스타일에 맞게 시각적 편집 목표 생성)
    goal_generation_messages = [
        SystemMessage(content="You are a visual editing goal generator for an advanced multi-modal image editing system called OmniGen. Your job is to extract 3–5 detailed visual editing objectives from user feedback. Focus on elements like scene composition, subject attributes, lighting, camera angle, style, or spatial relationships."),
        HumanMessage(content=f"""
Original Prompt:
\"{original_prompt}\"

User Feedback:
\"{user_feedback}\"

Output only a numbered list of visual editing goals (e.g., 1. Add sunlight from left, 2. Make character expression angry, 3. Replace background with forest, etc.)
""")
    ]

    visual_goal_response = llm(goal_generation_messages).content.strip()

    # Parse: 숫자 리스트를 '-' bullet list로 변환
    goal_lines = visual_goal_response.splitlines()
    visual_goal_list = [line.lstrip("1234567890. ").strip() for line in goal_lines if line.strip()]
    goal_text = "\n".join(f"- {goal}" for goal in visual_goal_list)

    # Step 2: Prompt 재작성 (OmniGen 편집 목적에 맞게 고품질 편집 프롬프트 생성)
    messages = [
        SystemMessage(content="You are a prompt editing agent for OmniGen, a high-quality multi-modal image editing model. Rewrite the original image prompt to reflect the user feedback and visual goals. Be precise, visual, and ensure the prompt is clearly focused on editing intent. Return only the final prompt."),
        HumanMessage(content=f"""
Original Prompt:
\"{original_prompt}\"

User Feedback:
\"{user_feedback}\"

Visual Editing Goals:
{goal_text}

Rewrite the prompt so it reflects these visual editing goals with clarity and control. Keep the style compatible with advanced generative models like OmniGen. Do not include explanations.
""")
    ]

    revised_prompt = llm(messages).content.strip()
    return revised_prompt