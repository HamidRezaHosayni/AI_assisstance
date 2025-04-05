import json
from listening_and_speaking.speech_to_text import SpeechRecognizer
from listening_and_speaking.text_to_speech import TextToSpeech
from search_pdf.pdf_search import PDFSearcher
from request_ollama.ollama_api import OllamaAPI
from web_scraping.web_searcher import WebSearcher  # اضافه کردن WebSearcher
import re
from dotenv import load_dotenv  # اضافه کردن ماژول dotenv
import os
import requests
import openai  # اضافه کردن OpenAI SDK برای DeepSeek API
from request_ollama.openrouter_api import OpenRouterAPI  # تغییر از DeepSeekAPI به OpenRouterAPI


class ChatBot:
    def __init__(self, pdf_path: str = None):
        # بارگذاری متغیرهای محیطی
        load_dotenv()
        self.model = os.getenv("MODEL_NAME", "nomic-embed-text:latest")  # مدل پیش‌فرض Ollama
        self.online_model = os.getenv("ONLINE_MODEL_NAME", "mistralai/mistral-small-3.1-24b-instruct:free")  # تغییر مدل آنلاین
        self.online_api_key = os.getenv("ONLINE_API_KEY")  # خواندن کلید API از .env
        self.online_model_url = os.getenv("ONLINE_MODEL_URL")  # خواندن آدرس مدل آنلاین از .env

        # بررسی متغیرهای محیطی
        if not self.online_model:
            raise ValueError("متغیر محیطی ONLINE_MODEL_NAME تنظیم نشده است.")
        if not self.online_api_key:
            raise ValueError("متغیر محیطی ONLINE_API_KEY تنظیم نشده است.")
        if not self.online_model_url:
            raise ValueError("متغیر محیطی ONLINE_MODEL_URL تنظیم نشده است.")

        self.current_model = "ollama"  # مدل پیش‌فرض
        self.ollama_api = OllamaAPI()
        self.speech_recognizer = SpeechRecognizer()
        self.text_to_speech = TextToSpeech()
        self.pdf_searcher = None
        self.web_searcher = WebSearcher()  # نمونه‌ای از WebSearcher برای جستجوی وب
        self.search_mode = "pdf"  # حالت پیش‌فرض: جستجو در PDF
        # تعریف مجموعه حروف فارسی
        self.persian_chars = set('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')
        # تعریف الگوی کلمات فارسی
        self.word_pattern = re.compile(r'[\u0600-\u06FF\uFB8A\u067E\u0686\u06AF]+')  # جایگزینی \u06AG با \u06AF

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

    def is_persian_char(self, char: str) -> bool:
        """بررسی می‌کند که آیا کاراکتر یک حرف فارسی است"""
        return char in self.persian_chars

    def find_last_complete_word(self, text: str) -> int:
        """
        پیدا کردن آخرین کلمه کامل در متن
        Returns:
            int: موقعیت آخرین کلمه کامل
        """
        if not text:
            return 0

        # پیدا کردن آخرین فاصله
        last_space = text.rfind(' ')
        if last_space == -1:
            last_space = 0

        # بررسی کاراکتر قبل از فاصله
        if last_space > 0 and self.is_persian_char(text[last_space - 1]):
            # اگر کاراکتر قبل از فاصله فارسی است، به عقب برمی‌گردیم تا کلمه کامل پیدا کنیم
            for i in range(last_space - 1, -1, -1):
                if not self.is_persian_char(text[i]):
                    return i + 1
            return 0

        return last_space

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
                pdf_name = "1.pdf"  # نام فایل PDF
                context = self.pdf_searcher.get_relevant_context(prompt, pdf_name=pdf_name, max_chars=1000)
                if context:
                    print("\nمتن مرتبط از PDF:")
                    print("-" * 50)
                    print(context)  # فقط متن مرتبط چاپ می‌شود
                    print("-" * 50)
                else:
                    print("\nنتیجه مرتبطی در PDF یافت نشد.")
                    print("لطفاً بررسی کنید که فایل PDF حاوی متن قابل استخراج باشد.")
            elif self.search_mode == "web":
                print("\nجستجو در وب...")
                context = self.web_searcher.search(prompt)  # استفاده از WebSearcher
                if context:
                    print("\nنتایج مرتبط از وب یافت شد:")
                    print("-" * 50)
                    print(context)  # فقط متن مرتبط چاپ می‌شود
                    print("-" * 50)
                else:
                    print("\nنتیجه مرتبطی در وب یافت نشد.")

            # ساخت پرامپت با توجه به متن مرتبط
            if context:
                system_prompt = "شما یک دستیار هوشمند فارسی هستید. لطفاً به فارسی پاسخ دهید."
                system_prompt += f"\n\nمتن مرتبط با سوال شما:\n{context}"
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"

                print("\nپرامپت کامل ارسال شده به مدل:")
                print("-" * 50)
                print(full_prompt)
                print("-" * 50)

                print("\nدر حال دریافت پاسخ از مدل...")
                if self.current_model == "ollama":
                    response = self.ollama_api.generate_response(
                        prompt=full_prompt,
                        model=self.model,  # استفاده از مدل Ollama
                        options={
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "num_predict": 1000
                        }
                    )
                elif self.current_model == "online":
                    response = self.generate_response_online(
                        prompt=full_prompt,
                        model=self.online_model
                    )
                else:
                    response = "مدل آنلاین در دسترس نیست یا کلید API تنظیم نشده است."

                if response and response != "سرور Ollama در دسترس نیست.":
                    print("\nپاسخ دریافت شد. در حال پخش...")
                    self.text_to_speech.speak(response)
                else:
                    print("\nخطا: پاسخ نامعتبر از سرور دریافت شد یا سرور در دسترس نیست.")
            else:
                print("\nهیچ متن مرتبطی برای ارسال به مدل یافت نشد.")

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

    def generate_response_online(self, prompt: str, model: str = None) -> str:
        """
        ارسال درخواست به مدل آنلاین OpenRouter
        Args:
            prompt: متن ورودی
            model: نام مدل OpenRouter (اگر None باشد، از ONLINE_MODEL_NAME استفاده می‌شود)
        Returns:
            str: پاسخ مدل
        """
        if not self.openrouter_api:
            return "مدل آنلاین OpenRouter تنظیم نشده است."

        # استفاده از مدل پیش‌فرض اگر مدل مشخص نشده باشد
        model = model or self.online_model

        # تبدیل prompt به ساختار messages مناسب برای OpenRouter
        messages = [
            {"role": "system", "content": "شما یک دستیار فارسی‌زبان هستید. به فارسی پاسخ بده."},
            {"role": "user", "content": prompt}
        ]

        return self.openrouter_api.generate_response(messages, model)

    def chat(self):
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
                print(f"\nخطا: {e}")

    def toggle_search_mode(self):
        """تغییر حالت جستجو بین PDF و اینترنت"""
        if self.search_mode == "pdf":
            self.search_mode = "web"
            print("\nحالت جستجو به حالت اینترنتی تغییر کرد.")
        else:
            self.search_mode = "pdf"
            print("\nحالت جستجو به حالت PDF تغییر کرد.")


if __name__ == "__main__":
    # ایجاد نمونه از چت‌بات با مسیر PDF
    chatbot = ChatBot(pdf_path="search_pdf/pdf_files/1.pdf")  # مسیر فایل PDF را مشخص کنید
    chatbot.chat()



