import os
import json
from openai import OpenAI
from typing import List
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from cfg import OPEN_API_KEY

client = OpenAI(api_key=OPEN_API_KEY)

# 프롬포트 파싱, 정보 추출
def run_prompt_parser(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4-0613",
        messages=[
            {"role": "system", "content": "You are a parser for 3D car scene generation. Extract all vehicle objects from the scene description and structure them into JSON with category, style, position, goals, and behavior."},
            {"role": "user", "content": prompt}
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "extract_vehicle_objects",
                    "description": "Extract structured car object info from scene prompt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "vehicles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "category": {"type": "string"},
                                        "style": {"type": "string"},
                                        "count": {"type": "integer"},
                                        "position_hint": {"type": "string"},
                                        "visual_goal": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "behavior": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    },
                                    "required": ["category"]
                                }
                            }
                        },
                        "required": ["vehicles"]
                    }
                }
            }
        ],
        tool_choice={"type": "function", "function": {"name": "extract_vehicle_objects"}}
    )

    # JSON 파싱
    arguments = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(arguments)

# 차량에 대한 시각목표 생성
def plan_object_attributes(parsed_vehicle_dict: dict):
    vehicle_list = parsed_vehicle_dict["vehicles"]

    system_message = {
        "role": "system",
        "content": (
            "You are a scene object planner for 3D car generation.\n"
            "For each vehicle object, return a list of dictionaries with the following keys:\n"
            "- name (str)\n"
            "- count (int)\n"
            "- style (str)\n"
            "- visual_goal (list of str)\n"
            "- behavior (list of str)\n"
            "- constraints (list of str)\n"
            "- generation_notes (str)\n"
            "Return only valid JSON (no markdown, no explanation, no code block, no comments)."
        )
    }

    user_message = {
        "role": "user",
        "content": f"Here is the vehicle list: {vehicle_list}\n"
                   "Return a list with detailed planning for each object."
    }

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[system_message, user_message]
    )

    return json.loads(response.choices[0].message.content)

def improve_prompt_for_asset_image(bad_prompt: str, visual_goals: List[str] = None) -> str:
    if visual_goals is None:
        visual_goals = [
            "isometric perspective",
            "neutral background with soft shadows",
            "high detail for surface and texture",
            "centered object with no cropping",
            "consistent lighting from top-left"
        ]

    goal_text = "\n".join(f"- {g}" for g in visual_goals)

    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.4,
                     openai_api_key=OPEN_API_KEY)

    messages = [
        SystemMessage(content="You are an expert prompt engineer creating 2D reference images for 3D asset generation."),
        HumanMessage(content=f"""
User's Original Prompt:
\"{bad_prompt}\"

Visual Requirements:
{goal_text}

Rewrite the prompt so it generates a clean, realistic, and centered 2D image suitable for 3D asset generation.
Use Stable Diffusion prompt conventions.
""")
    ]

    return llm(messages).content.strip()

def extract_sd_prompts(objects: list) -> list:
    prompts = []
    for obj in objects:
        raw = obj.get("sd_prompt", "")
        # "Prompt: " 또는 'Prompt: "' 로 시작하는 경우 제거
        if raw.lower().startswith("prompt:"):
            prompt_cleaned = raw.split("Prompt:", 1)[1].strip().strip('"')
        else:
            prompt_cleaned = raw.strip().strip('"')
        prompts.append(prompt_cleaned)
    return prompts

def plan_and_rewrite_prompts(scene_prompt: str) -> List[dict]:
    parsed = run_prompt_parser(scene_prompt)
    planned = plan_object_attributes(parsed)

    results = []
    for obj in planned:
        # 객체 이름 + 스타일을 원래 사용자 프롬프트로 사용
        base_prompt = f"{obj['style']} {obj['name']}"
        improved_prompt = improve_prompt_for_asset_image(base_prompt, obj.get("visual_goal", []))

        results.append({
            "category": obj["name"],
            "style": obj["style"],
            "count": obj["count"],
            "position_hint": obj.get("position_hint", ""),
            "visual_goal": obj.get("visual_goal", []),
            "behavior": obj.get("behavior", []),
            "constraints": obj.get("constraints", []),
            "generation_notes": obj.get("generation_notes", ""),
            "sd_prompt": improved_prompt
        })
    prompt = extract_sd_prompts(results)
    return prompt



