from PyQt5.QtCore import QThread, pyqtSignal
from google import genai

MODEL_PRIORITIES = [
    "gemini-3-flash-preview",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
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
        try:
            client = genai.Client(api_key=self.api_key)
            instruction = (
                f"Act as a Stable Diffusion prompt engineer. Style: {self.style}. "
                f"Convert input to English tags. Output ONLY tags, comma-separated. "
                f"Input: {self.user_input}"
            )

            for model_name in MODEL_PRIORITIES:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=instruction
                    )
                    if response.text:
                        self.finished.emit(response.text.strip())
                        return
                except Exception as e:
                    print(f"Fallback: {model_name} failed. Error: {e}")
                    continue

            self.error.emit(
                "All Gemini models failed. Check connection or API quota.")
        except Exception as e:
            self.error.emit(f"SDK Error: {str(e)}")