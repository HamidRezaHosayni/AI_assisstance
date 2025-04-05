import requests
import json

class OllamaAPI:
    def __init__(self, base_url: str = "http://localhost:11434"):
        """راه‌اندازی کلاس ارتباط با Ollama API"""
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        self.embeddings_url = f"{base_url}/api/embeddings"

    def generate_response(self, prompt: str, model: str = "llama3.1:8b", **kwargs) -> str:
        """
        دریافت پاسخ از مدل
        Args:
            prompt: متن ورودی
            model: نام مدل
            **kwargs: تنظیمات اضافی مانند temperature, top_p و غیره
        Returns:
            str: پاسخ مدل
        """
        try:
            default_options = {
                "keep_alive": "30m",
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 1000
            }
            
            # ترکیب تنظیمات پیش‌فرض با تنظیمات ورودی
            options = {**default_options, **kwargs.get('options', {})}
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": options
            }
            
            response = requests.post(self.generate_url, json=payload)  # حذف پروکسی و SSLContext
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            print(f"خطا در دریافت پاسخ از مدل: {e}")
            return "خطا در دریافت پاسخ از مدل."

    def get_embedding(self, text: str, model: str = "nomic-embed-text") -> list:
        """
        دریافت embedding برای متن
        Args:
            text: متن ورودی
            model: نام مدل embedding
        Returns:
            list: بردار embedding
        """
        try:
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = requests.post(self.embeddings_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("embedding", [])
            
        except Exception as e:
            print(f"خطا در دریافت embedding: {e}")
            return []