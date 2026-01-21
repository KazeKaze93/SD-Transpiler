import json
import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any

from pydantic import BaseModel, ValidationError, Field


# --- Models ---
class LoraConfig(BaseModel):
    name: str
    weight: float = 1.0


class GenSettings(BaseModel):
    steps: int = 20
    cfg: float = 7.0


class StyleConfig(BaseModel):
    name: str
    base_model: str  # 'standard', 'pony', 'flux'
    quality_mode: str = "default"  # 'default', 'creative', 'explicit'
    prompt_payload: str
    negative_payload: str
    loras: List[LoraConfig] = []
    settings: GenSettings = Field(default_factory=GenSettings)


class GenerationResult(BaseModel):
    positive_prompt: str
    negative_prompt: str
    style_used: str
    loras: List[Dict[str, Any]]
    settings: Dict[str, Any]


# --- Engine ---
class TranspilerEngine:
    def __init__(self):
        self.app_name = "SD-Transpiler"
        self.internal_data_dir = self._get_internal_data_path()
        self.user_data_dir = Path(os.getenv('APPDATA')) / self.app_name

        self.styles: Dict[str, StyleConfig] = {}
        # Structure: presets[base_model][mode] -> {positive: str, negative: str}
        self.quality_presets: Dict[str, Dict[str, Dict[str, str]]] = {}

        self._ensure_user_config()
        self._load_data()

    def _get_internal_data_path(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys._MEIPASS) / 'data'
        return Path(__file__).parent.parent / 'data'

    def _ensure_user_config(self):
        if not self.user_data_dir.exists():
            try:
                self.user_data_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                return

        files_to_copy = ['styles.json', 'quality_tags.json']
        for filename in files_to_copy:
            target = self.user_data_dir / filename
            source = self.internal_data_dir / filename
            if not target.exists() and source.exists():
                try:
                    shutil.copy2(source, target)
                except Exception as e:
                    print(
                        f"Warning: Could not copy default config {filename}: {e}")

    def _load_data(self) -> None:
        styles_path = self.user_data_dir / 'styles.json'
        quality_path = self.user_data_dir / 'quality_tags.json'

        if not styles_path.exists(): styles_path = self.internal_data_dir / 'styles.json'
        if not quality_path.exists(): quality_path = self.internal_data_dir / 'quality_tags.json'

        try:
            # 1. Load Styles
            if styles_path.exists():
                with open(styles_path, 'r', encoding='utf-8') as f:
                    raw_styles = json.load(f).get("styles", {})
                    for key, data in raw_styles.items():
                        try:
                            if "quality_mode" not in data: data[
                                "quality_mode"] = "default"
                            if "loras" in data and data[
                                "loras"] and isinstance(data["loras"][0], str):
                                data[
                                    "loras"] = []

                            self.styles[key] = StyleConfig(**data)
                        except ValidationError as e:
                            print(f"Style validation error for {key}: {e}")
                            continue

            # 2. Load Quality Presets
            if quality_path.exists():
                with open(quality_path, 'r', encoding='utf-8') as f:
                    q_data = json.load(f)
                    self.quality_presets = q_data.get("presets", {})

        except Exception as e:
            print(f"Config Load Error: {e}")
            self.styles = {
                "Error": StyleConfig(name="Error", base_model="standard",
                                     prompt_payload="", negative_payload="")}

    def get_style_names(self) -> List[str]:
        return list(self.styles.keys())

    def process(self, user_input: str, style_name: str,
                nsfw_enabled: bool) -> GenerationResult:
        style = self.styles.get(style_name)
        if not style:
            style = list(self.styles.values())[
                0] if self.styles else StyleConfig(
                name="Fallback", base_model="standard", prompt_payload="",
                negative_payload="")

        # 1. Resolve Quality Preset
        # Logic: base_model -> quality_mode. If mode none, Fallback on default
        model_presets = self.quality_presets.get(style.base_model, {})

        target_mode = style.quality_mode
        if target_mode not in model_presets:
            target_mode = "default"

        q_tags = model_presets.get(target_mode,
                                   {"positive": "", "negative": ""})

        # 2. Construct Positive Prompt
        # Order: Quality -> Style Payload -> User Input -> Rating (if pony)
        pos_segments = [
            q_tags.get("positive", ""),
            style.prompt_payload,
            self._sanitize_input(user_input)
        ]

        # Special logic for Pony Rating if not present
        if style.base_model == "pony":
            rating_tag = "rating_explicit" if nsfw_enabled else "rating_safe"
            current_str = "".join(pos_segments).lower()
            if "rating_" not in current_str and "score_" in q_tags.get(
                    "positive", ""):
                pos_segments.insert(1, rating_tag)

        final_positive = self._compile_prompt(pos_segments)

        # 3. Construct Negative Prompt
        neg_segments = [q_tags.get("negative", ""), style.negative_payload]

        if not nsfw_enabled and style.base_model != "pony":
            neg_segments.append(
                "nsfw, nude, naked, sex, pornography, 18+, censored")

        final_negative = self._compile_prompt(neg_segments)

        return GenerationResult(
            positive_prompt=final_positive,
            negative_prompt=final_negative,
            style_used=style.name,
            loras=[l.model_dump() for l in style.loras],
            settings=style.settings.model_dump()
        )

    def _sanitize_input(self, text: str) -> str:
        if not text: return ""
        return " ".join(text.split())

    def _compile_prompt(self, segments: List[str]) -> str:
        """
        Deduplicates tags, removes empty strings, preserves order.
        """
        seen = set()
        final_tags = []

        for seg in segments:
            if not seg: continue
            # Split by comma, strip whitespace
            tags = [t.strip() for t in seg.split(',')]
            for tag in tags:
                tag_lower = tag.lower()
                if not tag_lower: continue

                # Simple deduplication
                if tag_lower not in seen:
                    seen.add(tag_lower)
                    final_tags.append(tag)

        return ", ".join(final_tags)


engine = TranspilerEngine()