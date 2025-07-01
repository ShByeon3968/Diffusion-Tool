import torch
import os
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from transformers import CLIPTokenizer
from typing import List

# OpenAI API Key 설정


device = "cuda" if torch.cuda.is_available() else "cpu"


def truncate_prompt(prompt: str, max_tokens: int = 77) -> str:
    tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
    tokens = tokenizer.tokenize(prompt)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return tokenizer.convert_tokens_to_string(tokens)

def improve_prompt_for_asset_image(bad_prompt: str, visual_goals: List[str] = None) -> str:
    """
    사용자 설명 프롬프트를 기반으로 3D 에셋 생성을 위한 고품질 2D 이미지를 얻기 위해
    프롬프트를 시각적으로 구체적이고 명확하게 개선한다.

    Args:
        bad_prompt (str): 사용자가 입력한 객체 설명 프롬프트 (예: "a wooden table")
        visual_goals (List[str], optional): 2D 이미지에 반드시 반영되어야 할 세부 시각 요소 (예: "isometric view", "realistic texture")

    Returns:
        str: Stable Diffusion 용으로 개선된 시각 중심 프롬프트
    """
    if visual_goals is None:
        visual_goals = [
            "isometric perspective",
            "neutral background with soft shadows",
            "high detail for surface and texture",
            "centered object with no cropping",
            "consistent lighting from top-left"
        ]

    goal_text = "\n".join(f"- {g}" for g in visual_goals)

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.4)

    messages = [
        SystemMessage(content="You are an expert prompt engineer creating 2D reference images for 3D asset generation. Improve user prompts to be more visually detailed, clear, and useful for rendering high-quality image-to-3D results."),
        HumanMessage(content=f"""
User's Original Prompt:
\"{bad_prompt}\"

Visual Requirements:
{goal_text}

Rewrite the prompt so it generates a clean, realistic, and centered 2D image suitable for 3D asset generation.
Use Stable Diffusion prompt conventions.
""")
    ]

    improved_prompt = llm(messages).content.strip()
    return improved_prompt