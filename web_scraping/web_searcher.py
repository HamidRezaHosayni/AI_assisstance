from request_ollama import OllamaAPI  # وارد کردن کلاس OllamaAPI به صورت ماژولار
import requests
from bs4 import BeautifulSoup
import time
import random
from dotenv import load_dotenv
import os

class WebSearcher:
    def __init__(self):
        # بارگذاری متغیرهای محیطی از فایل .env
        load_dotenv()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
            'Connection': 'keep-alive',
        }
        # خواندن مقادیر از متغیرهای محیطی
        self.api_key = os.getenv("GOOGLE_API_KEY")  # کلید API گوگل
        self.cx = os.getenv("GOOGLE_CX")  # شناسه موتور جستجوی سفارشی
        self.ollama_api = OllamaAPI()  # نمونه‌ای از کلاس OllamaAPI برای استفاده از مدل زبانی
        self.embedding_model = "nomic-embed-text"  # مدل مخصوص Web Search

    def search(self, query: str, max_results: int = 2) -> str:
        """
        جستجو در وب و استخراج متن‌های مرتبط با استفاده از مدل زبانی
        """
        if self.api_key and self.cx:
            return self._search_with_api(query, max_results)
        else:
            return self._search_with_scraping(query, max_results)

    def _extract_relevant_text(self, full_text: str, query: str) -> str:
        """
        استخراج متن‌های مرتبط با سوال کاربر با استفاده از مدل زبانی
        Args:
            full_text: متن کامل استخراج‌شده از وب‌سایت
            query: سوال کاربر
        Returns:
            str: متن‌های مرتبط
        """
        try:
            # ارسال متن کامل و سوال به مدل زبانی
            embedding = self.ollama_api.get_embedding(query, model=self.embedding_model)  # ارسال مدل مخصوص
            sentences = full_text.split(". ")  # تقسیم متن به جملات
            relevant_sentences = []

            for sentence in sentences:
                sentence_embedding = self.ollama_api.get_embedding(sentence, model=self.embedding_model)  # ارسال مدل مخصوص
                # محاسبه شباهت بین embedding سوال و جمله
                similarity = sum(a * b for a, b in zip(embedding, sentence_embedding))
                if similarity > 0.5:  # کاهش آستانه شباهت برای استخراج متن‌های بیشتر
                    relevant_sentences.append(sentence)

            # افزایش تعداد کاراکترهای پردازش‌شده
            return ". ".join(relevant_sentences[:50])  # محدود کردن به 50 جمله مرتبط
        except Exception as e:
            print(f"خطا در استخراج متن‌های مرتبط: {e}")
            return ""

    def _search_with_api(self, query: str, max_results: int) -> str:
        """
        جستجو با استفاده از Google Custom Search JSON API
        """
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'q': query,
                'key': self.api_key,
                'cx': self.cx,
                'num': max_results,
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'items' not in data:
                return "متاسفانه نتیجه‌ای یافت نشد. لطفاً سوال خود را به شکل دیگری مطرح کنید."

            results_text = ""
            for i, item in enumerate(data['items'], 1):
                snippet = item.get('snippet', 'بدون توضیح')
                # افزایش طول توضیحات به 500 کاراکتر
                if len(snippet) > 500:
                    snippet = snippet[:500] + "..."
                results_text += f"نتیجه {i}:\nمحتوا: {snippet}\n\n"  # حذف لینک از خروجی

            return results_text.strip()

        except Exception as e:
            print(f"خطا در جستجوی وب با API: {e}")
            return "خطا در جستجوی وب با API. لطفاً دوباره تلاش کنید."

    def _search_with_scraping(self, query: str, max_results: int) -> str:
        """
        جستجو با استفاده از روش scraping و استخراج متن‌های مرتبط
        """
        try:
            # ارسال درخواست به گوگل
            url = f"https://www.google.com/search?q={query}&num={max_results}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # بررسی پاسخ نامعتبر از گوگل
            if "did not match any documents" in response.text or "captcha" in response.text:
                return "گوگل درخواست شما را مسدود کرده است یا نتیجه‌ای یافت نشد. لطفاً دوباره تلاش کنید یا از یک سرویس جایگزین استفاده کنید."
            
            # پردازش HTML صفحه نتایج جستجو
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            
            for link in soup.select('a'):
                href = link.get('href')
                if href and "/url?q=" in href:
                    # استخراج لینک واقعی
                    actual_url = href.split("/url?q=")[1].split("&")[0]
                    search_results.append(actual_url)
                    if len(search_results) >= max_results:
                        break
            
            if not search_results:
                return (
                    "متاسفانه نتیجه‌ای یافت نشد. لطفاً سوال خود را به شکل دیگری مطرح کنید "
                    "یا از یک API رسمی مانند Google Custom Search JSON API استفاده کنید."
                )
            
            # استخراج متن از لینک‌ها
            results_text = ""
            for i, url in enumerate(search_results, 1):
                try:
                    # تأخیر تصادفی بین درخواست‌ها
                    time.sleep(random.uniform(2, 5))
                    
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # حذف اسکریپت‌ها و استایل‌ها
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # استخراج متن اصلی
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    full_text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # حذف لینک‌ها و استخراج متن‌های مرتبط
                    relevant_text = self._extract_relevant_text(full_text, query)
                    
                    results_text += f"نتیجه {i}:\nمحتوا: {relevant_text}\n\n"
                
                except Exception as e:
                    print(f"خطا در پردازش لینک {url}: {e}")
                    continue
            
            return results_text.strip() if results_text else (
                "متاسفانه نتیجه‌ای یافت نشد. لطفاً سوال خود را به شکل دیگری مطرح کنید "
                "یا از یک API رسمی مانند Google Custom Search JSON API استفاده کنید."
            )
        
        except Exception as e:
            print(f"خطا در جستجوی وب: {e}")
            return "خطا در جستجوی وب. لطفاً دوباره تلاش کنید."



