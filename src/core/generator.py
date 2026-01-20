import json
import os
from typing import List, Dict
from pydantic import BaseModel, ValidationError


class StyleConfig(BaseModel):
    name: str
    prompt_payload: str
    negative_payload: str
    loras: List[str]


class GenerationResult(BaseModel):
    positive_prompt: str
    negative_prompt: str
    style_used: str


class TranspilerEngine:
    """
    Core logic for assembling Stable Diffusion prompts.
    """

    def __init__(self):
        self.base_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.styles: Dict[str, StyleConfig] = {}
        self.quality_pos: str = ""
        self.quality_neg: str = ""

        self._load_data()

    def _load_data(self) -> None:
        """Loads JSON configurations with strict Pydantic validation."""
        styles_path = os.path.join(self.base_path, 'src', 'data',
                                   'styles.json')
        quality_path = os.path.join(self.base_path, 'src', 'data',
                                    'quality_tags.json')

        try:
            # 1. Load Styles
            with open(styles_path, 'r', encoding='utf-8') as f:
                raw_styles = json.load(f).get("styles", {})
                for key, data in raw_styles.items():
                    self.styles[key] = StyleConfig(**data)

            # 2. Load Quality Tags
            with open(quality_path, 'r', encoding='utf-8') as f:
                q_data = json.load(f)
                self.quality_pos = q_data.get("positive", "")
                self.quality_neg = q_data.get("negative", "")

        except (FileNotFoundError, json.JSONDecodeError, ValidationError) as e:
            print(f"WARNING: Data loading failed ({e}). Using empty defaults.")
            self.styles = {
                "No Style": StyleConfig(name="No Style", prompt_payload="",
                                        negative_payload="", loras=[])}

    def get_style_names(self) -> List[str]:
        return list(self.styles.keys())

    def process(self, user_input: str, style_name: str) -> GenerationResult:
        # 1. Fallback
        style = self.styles.get(style_name, self.styles.get("No Style"))
        if not style:
            style = StyleConfig(name="Fallback", prompt_payload="",
                                negative_payload="", loras=[])

        # 2. Construct Positive
        pos_parts = [
            self.quality_pos,
            style.prompt_payload,
            self._sanitize_input(user_input),
            ", ".join(style.loras)
        ]
        final_positive = ", ".join([p for p in pos_parts if p.strip()])

        # 3. Construct Negative
        neg_parts = [
            self.quality_neg,
            style.negative_payload
        ]
        final_negative = ", ".join([p for p in neg_parts if p.strip()])

        return GenerationResult(
            positive_prompt=final_positive,
            negative_prompt=final_negative,
            style_used=style.name
        )

    def _sanitize_input(self, text: str) -> str:
        if not text:
            return ""
        return " ".join(text.split())


engine = TranspilerEngine()