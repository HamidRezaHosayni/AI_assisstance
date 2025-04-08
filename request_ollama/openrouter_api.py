import requests
import json

class OpenRouterAPI:
    def __init__(self, api_key: str, base_url: str):
        """
        کلاس برای ارتباط با OpenRouter API
        Args:
            api_key: کلید API برای احراز هویت
            base_url: آدرس پایه API OpenRouter
        """
        if not api_key:
            raise ValueError("کلید API تنظیم نشده است.")
        if not base_url:
            raise ValueError("آدرس پایه API تنظیم نشده است.")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # حذف اسلش انتهایی در صورت وجود

    def generate_response(self, messages: list, model: str = "deepseek/deepseek-v3-base:free") -> str:
        """
        ارسال درخواست به OpenRouter API و دریافت پاسخ
        Args:
            messages: لیست پیام‌ها شامل system, user، و assistant
            model: نام مدل (مثلاً: deepseek/deepseek-v3-base:free)
        Returns:
            str: پاسخ تولیدشده توسط مدل
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "MyChatbot"
            }

            payload = {
                "model": model,
                "messages": messages  # ارسال تاریخچه مکالمه
            }

            url = f"{self.base_url}/chat/completions"
            response = requests.post(url, headers=headers, json=payload)

            # بررسی وضعیت پاسخ
            if response.status_code != 200:
                print(f"❌ وضعیت HTTP: {response.status_code}")
                print(f"🧾 پاسخ سرور: {response.text}")
                return "خطا در دریافت پاسخ از مدل آنلاین."

            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "پاسخی دریافت نشد.")

        except requests.exceptions.RequestException as req_err:
            print(f"⛔ خطای اتصال به OpenRouter: {req_err}")
            return "خطای اتصال به OpenRouter."

        except Exception as e:
            print(f"❌ خطای کلی: {e}")
            return "خطای کلی در ارتباط با OpenRouter API."
