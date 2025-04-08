import json
import os  # اضافه کردن import برای رفع خطای 'os' is not defined
from listening_and_speaking.speech_to_text import SpeechRecognizer
from listening_and_speaking.text_to_speech import TextToSpeech
from search_pdf.pdf_search import PDFSearcher
from request_ollama.ollama_api import OllamaAPI
from web_scraping.web_searcher import WebSearcher
from request_ollama.openrouter_api import OpenRouterAPI
from utils.text_processing import TextProcessor
from utils.environment import Environment
from tools.tool_manager import ToolManager


class ChatBot:
    def __init__(self, pdf_path: str = None):
        # بارگذاری متغیرهای محیطی
        Environment.load_env()
        self.model = Environment.get_env_variable("MODEL_NAME", "nomic-embed-text:latest")
        self.online_model = Environment.get_env_variable("ONLINE_MODEL_NAME", "mistralai/mistral-small-3.1-24b-instruct:free")
        self.online_api_key = Environment.get_env_variable("ONLINE_API_KEY")
        self.online_model_url = Environment.get_env_variable("ONLINE_MODEL_URL")
        self.system_prompt = Environment.get_env_variable("SYSTEM_PROMPT", "شما یک دستیار هوشمند فارسی هستید. لطفاً به فارسی پاسخ دهید.")
        self.SYSTEM_USER = Environment.get_env_variable("SYSTEM_USER", "کاربر از سیستم لینوکس استفاده میکند.")

        # بررسی متغیرهای محیطی
        if not self.online_model:
            raise ValueError("متغیر محیطی ONLINE_MODEL_NAME تنظیم نشده است.")
        if not self.online_api_key:
            raise ValueError("متغیر محیطی ONLINE_API_KEY تنظیم نشده است.")
        if not self.online_model_url:
            raise ValueError("متغیر محیطی ONLINE_MODEL_URL تنظیم نشده است.")

        self.current_model = "ollama"
        self.ollama_api = OllamaAPI()
        self.speech_recognizer = SpeechRecognizer()
        self.text_to_speech = TextToSpeech()
        self.pdf_searcher = None
        self.web_searcher = WebSearcher()
        self.search_mode = "pdf"
        self.tool_manager = ToolManager()  # اضافه کردن مدیریت ابزار
        self.conversation_history = []  # اضافه کردن لیست برای ذخیره تاریخچه مکالمه

        # راه‌اندازی جستجوگر PDF اگر مسیر مشخص شده باشد
        if pdf_path:
            try:
                self.pdf_searcher = PDFSearcher()
                pdf_name = os.path.basename(pdf_path)
                print(f"در حال پردازش فایل PDF: {pdf_name}...")
                self.pdf_searcher.process_pdf(pdf_name)
                print(f"عمل embedding برای فایل {pdf_name} با موفقیت انجام شد.")
            except Exception as e:
                print(f"خطا در پردازش PDF: {e}")

        # ایجاد نمونه از OpenRouterAPI اگر کلید API تنظیم شده باشد
        if self.online_api_key:
            self.openrouter_api = OpenRouterAPI(api_key=self.online_api_key, base_url=self.online_model_url)
        else:
            self.openrouter_api = None

    def log_response(self, response: str):
        """
        لاگ گرفتن از پاسخ مدل در یک فایل متنی
        """
        try:
            log_file = "model_responses.log"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"پاسخ مدل:\n{response}\n{'='*50}\n")
            print(f"✅ پاسخ مدل در فایل {log_file} ذخیره شد.")
        except Exception as e:
            print(f"⚠️ خطا در ذخیره پاسخ مدل: {e}")

    def send_request(self, prompt: str) -> None:
        try:
            # بررسی دستور تغییر حالت جستجو
            if "تغییر سرچ" in prompt.lower() or "تغییر جستجو" in prompt.lower():
                self.toggle_search_mode()
                self.text_to_speech.speak(f"حالت جستجو به حالت {self.search_mode} تغییر کرد.")
                return

            # بررسی دستور تغییر مدل
            if "تغییر مدل" in prompt.lower():
                self.toggle_model()
                self.text_to_speech.speak(f"مدل به {self.current_model} تغییر کرد.")
                return

            # جستجو در PDF یا اینترنت بر اساس حالت فعلی
            context = ""
            if self.search_mode == "pdf" and self.pdf_searcher:
                pdf_name = "1.pdf"
                context = self.pdf_searcher.get_relevant_context(prompt, pdf_name=pdf_name, max_chars=1000)
                if context:
                    print("\nمتن مرتبط از PDF:")
                    print("-" * 50)
                    print(context)
                    print("-" * 50)
                else:
                    print("\nنتیجه مرتبطی در PDF یافت نشد.")
                    print("لطفاً بررسی کنید که فایل PDF حاوی متن قابل استخراج باشد.")
            elif self.search_mode == "web":
                print("\nجستجو در وب...")
                context = self.web_searcher.search(prompt)
                if context:
                    print("\nنتایج مرتبط از وب یافت شد:")
                    print("-" * 50)
                    print(context)
                    print("-" * 50)
                else:
                    print("\nنتیجه مرتبطی در وب یافت نشد.")

            # اضافه کردن پیام کاربر به تاریخچه مکالمه
            self.conversation_history.append({"role": "user", "content": prompt})

            # محدود کردن تاریخچه مکالمه به ۵ پیام آخر
            limited_history = self.conversation_history[-5:]

            # ساخت پیام‌ها با توجه به تاریخچه محدودشده
            messages = [{"role": "system", "content": self.system_prompt}]
            if context:
                messages.append({"role": "system", "content": f"متن مرتبط با سوال شما:\n{context}"})
            messages.extend(limited_history)

            print("\nپرامپت کامل ارسال شده به مدل:")
            print("-" * 50)
            for msg in messages:
                print(f"{msg['role']}: {msg['content']}")
            print("-" * 50)

            print("\nدر حال دریافت پاسخ از مدل...")
            if self.current_model == "ollama":
                response = self.ollama_api.generate_response(
                    prompt="\n".join([f"{msg['role']}: {msg['content']}" for msg in messages]),
                    model=self.model,
                    options={
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 1000
                    }
                )
            elif self.current_model == "online":
                response = self.generate_response_online(
                    messages=messages,
                    model=self.online_model
                )
            else:
                response = "مدل آنلاین در دسترس نیست یا کلید API تنظیم نشده است."

            # اضافه کردن پاسخ مدل به تاریخچه مکالمه
            self.conversation_history.append({"role": "assistant", "content": response})

            # لاگ گرفتن از پاسخ مدل
            self.log_response(response)

            # بررسی پاسخ برای دستورات ابزار
            if "%%" in response:
                print("\nپاسخ شامل دستور ابزار است. ارسال به مدیریت ابزار...")
                results = self.tool_manager.process_response(response)

                if "موفقیت" in results:
                    print("\n✅ دستورات با موفقیت اجرا شدند.")
                    self.text_to_speech.speak("دستورات با موفقیت اجرا شدند.")
                else:
                    print("\n❌ مشکلی در اجرای دستورات وجود داشت.")
                    self.text_to_speech.speak("مشکلی در اجرای دستورات وجود داشت.")
            else:
                # پاک‌سازی پاسخ از کاراکترهای غیرمجاز و پخش آن
                cleaned_response = TextProcessor.clean_response(response)
                print("\nپاسخ دریافت شد. در حال پخش...")
                print(f"پاسخ: {cleaned_response}")
                self.text_to_speech.speak(cleaned_response)

        except Exception as e:
            print(f"\nخطای ناشناخته: {e}")

    def toggle_model(self):
        """تغییر مدل اصلی بین Ollama و مدل آنلاین"""
        if self.current_model == "ollama" and self.online_api_key:
            self.current_model = "online"
            print("\nمدل به مدل آنلاین تغییر کرد.")
        else:
            self.current_model = "ollama"
            print("\nمدل به Ollama تغییر کرد.")

    def toggle_search_mode(self):
        """تغییر حالت جستجو بین PDF و اینترنت"""
        if self.search_mode == "pdf":
            self.search_mode = "web"
            print("\nحالت جستجو به حالت اینترنتی تغییر کرد.")
        else:
            self.search_mode = "pdf"
            print("\nحالت جستجو به حالت PDF تغییر کرد.")

    def generate_response_online(self, messages: list, model: str = None) -> str:
        """
        ارسال درخواست به مدل آنلاین OpenRouter
        Args:
            messages: لیست پیام‌ها شامل تاریخچه مکالمه
            model: نام مدل OpenRouter (اگر None باشد، از ONLINE_MODEL_NAME استفاده می‌شود)
        Returns:
            str: پاسخ مدل
        """
        if not self.openrouter_api:
            raise ValueError("مدل آنلاین OpenRouter تنظیم نشده است.")

        # استفاده از مدل پیش‌فرض اگر مدل مشخص نشده باشد
        model = model or self.online_model

        return self.openrouter_api.generate_response(messages, model)

    def chat(self):
        """
        متد اصلی برای شروع چت با کاربر
        """
        print("\n=== ربات چت فارسی با هوش مصنوعی (ورودی صوتی و خروجی صوتی) ===")
        print("برای خروج، کلمه 'خروج' را بگویید.")
        print("برای تغییر حالت جستجو بین PDF و اینترنت، عبارت 'تغییر سرچ' را بگویید.")
        print("برای تغییر مدل بین Ollama و مدل آنلاین، عبارت 'تغییر مدل' را بگویید.")
        print("حالت پیش‌فرض: جستجو در PDF")
        print("=" * 50 + "\n")

        while True:
            try:
                user_input = self.speech_recognizer.listen_for_audio()

                if user_input.lower() in ['خروج', 'exit', 'quit']:
                    print("\nخداحافظ!")
                    break

                if not user_input:
                    continue

                self.send_request(user_input)

            except KeyboardInterrupt:
                print("\n\nبرنامه توسط کاربر متوقف شد.")
                break
            except Exception as e:
                print(f"\nخطای ناشناخته: {e}")


if __name__ == "__main__":
    chatbot = ChatBot(pdf_path="search_pdf/pdf_files/1.pdf")
    chatbot.chat()



