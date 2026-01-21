import time

from PyQt6.QtCore import QThread, pyqtSignal
from google import genai
from google.api_core import exceptions as google_exceptions

MODEL_PRIORITIES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-3-flash-preview"
]


class GeminiWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_key: str, user_input: str, style: str):
        super().__init__()
        self.api_key = api_key
        self.user_input = user_input
        self.style = style

    def run(self):
        if not self.api_key:
            self.error.emit("API Key is missing.")
            return

        client = None
        try:
            client = genai.Client(api_key=self.api_key)
        except Exception as e:
            self.error.emit(f"Init Error: {str(e)}")
            return

        sys_instr = (
            "Role: Expert Stable Diffusion Prompt Engineer (Danbooru/e621 format).\n"
            "Task: Translate and expand user input into a detailed, comma-separated list of English tags.\n"
            "Rules:\n"
            "1. TRANSLATE everything to English.\n"
            "2. OUTPUT FORMAT: tag1, tag2, tag3. NO markdown, NO explanations, NO dictionaries.\n"
            "3. STRUCTURE: Subject -> Appearance/Clothing -> Pose/Action -> Environment -> Lighting/Camera.\n"
            "4. IMPORTANT: DO NOT add quality score tags (e.g. 'masterpiece', 'best quality', 'score_9') - system adds them automatically.\n"
            "5. CREATIVITY: If input is simple, logically fill in missing visual details (texture, background, mood).\n"
            "\n"
            "Example Input: 'рыжая девушка в лесу'\n"
            "Example Output: 1girl, solo, orange hair, long hair, detailed eyes, casual clothes, standing, forest, trees, nature, sunlight, dappled lighting, depth of field, soft focus"
        )

        prompt = f"Style Context: {self.style}. \nUser Request: {self.user_input}"

        last_error = ""

        for model_name in MODEL_PRIORITIES:
            try:

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=sys_instr,
                        temperature=0.4
                    )
                )

                if response.text:
                    self.finished.emit(response.text.strip())
                    return

            except google_exceptions.ResourceExhausted:
                print(f"Model {model_name} hit Rate Limit (429). Switching...")
                last_error = "Rate Limit Exceeded. Please wait a bit."
                time.sleep(2)
                continue

            except google_exceptions.ServiceUnavailable:
                print(f"Model {model_name} is Overloaded (503). Switching...")
                last_error = "Google Servers are overloaded."
                time.sleep(1)
                continue

            except google_exceptions.NotFound:
                print(
                    f"Model {model_name} not found (deprecated?). Switching...")
                continue

            except Exception as e:
                print(f"Model {model_name} failed: {e}")
                last_error = str(e)
                continue

        if "Rate Limit" in last_error:
            self.error.emit("Quota Exceeded (429). Google asks to wait ~30s.")
        else:
            self.error.emit(f"All AI models failed. Last error: {last_error}")
