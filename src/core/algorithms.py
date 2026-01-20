import json
import os

from google import genai

from .models import StyleConfig, GenerationResult

MODEL_PRIORITIES = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


class TranspilerLogic:
    def __init__(self):
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        self.styles = self._load_json('data/styles.json').get("styles", {})
        self.quality = self._load_json('data/quality_tags.json')

    def _load_json(self, path):
        full_path = os.path.join(self.base_dir, path)
        if not os.path.exists(full_path): return {}
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_sync(self, api_key, user_input, style_name, nsfw):
        processed_text = user_input
        if api_key:
            processed_text = self._call_gemini(api_key, user_input, style_name)

        style = StyleConfig(
            **self.styles.get(style_name, list(self.styles.values())[0]))

        pos = f"{self.quality.get('positive', '')}, {style.prompt_payload}, {processed_text}, {', '.join(style.loras)}"
        neg = f"{self.quality.get('negative', '')}, {style.negative_payload}"
        if not nsfw:
            neg += ", nsfw, nude, naked, sex"

        return GenerationResult(
            positive=", ".join(filter(None, pos.split(", "))),
            negative=", ".join(filter(None, neg.split(", "))))

    def _call_gemini(self, key, text, style):
        client = genai.Client(api_key=key)
        prompt = f"Convert to SD tags. Style: {style}. Input: {text}. Output only comma-separated tags."
        for model in MODEL_PRIORITIES:
            try:
                response = client.models.generate_content(model=model,
                                                          contents=prompt)
                return response.text.strip()
            except:
                continue
        return text