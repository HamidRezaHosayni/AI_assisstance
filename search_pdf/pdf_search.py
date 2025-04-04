import os
import json
import numpy as np
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor
from request_ollama.ollama_api import OllamaAPI

class PDFSearcher:
    def __init__(self, pdf_folder: str = "search_pdf/pdf_files", embeddings_folder: str = "search_pdf/embeddings"):
        """
        مقداردهی اولیه کلاس جستجوگر PDF
        """
        self.pdf_folder = os.path.abspath(pdf_folder)
        self.embeddings_folder = os.path.abspath(embeddings_folder)
        os.makedirs(self.pdf_folder, exist_ok=True)
        os.makedirs(self.embeddings_folder, exist_ok=True)

        self.ollama_api = OllamaAPI()
        self.embedding_model = "nomic-embed-text:latest"  # اطمینان از استفاده از مدل مورد نظر
        self.pdf_embeddings = {}

    def process_pdf(self, pdf_name: str):
        """
        پردازش یک فایل PDF و ذخیره embedding‌ها در فایل JSON
        """
        pdf_path = os.path.join(self.pdf_folder, pdf_name)
        embeddings_file = os.path.join(self.embeddings_folder, f"{os.path.splitext(pdf_name)[0]}.json")

        if os.path.exists(embeddings_file):
            print(f"Embedding‌های فایل {pdf_name} قبلاً ذخیره شده‌اند.")
            return

        reader = PdfReader(pdf_path)
        chunks = []

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()
                if text and text.strip():
                    sentences = [s.strip() for s in text.split('.') if s.strip()]
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) < 500:
                            current_chunk += " " + sentence
                        else:
                            chunks.append({'text': current_chunk.strip(), 'page': page_num})
                            current_chunk = sentence
                    if current_chunk:
                        chunks.append({'text': current_chunk.strip(), 'page': page_num})
                else:
                    print(f"هشدار: صفحه {page_num} از فایل {pdf_name} حاوی متن قابل استخراج نیست.")
            except Exception as e:
                print(f"خطا در استخراج متن از صفحه {page_num} فایل {pdf_name}: {e}")

        if chunks:
            chunk_embeddings = self._compute_embeddings_parallel(chunks)
            embeddings_to_save = {chunk['text']: embedding for chunk, embedding in zip(chunks, chunk_embeddings)}

            with open(embeddings_file, "w") as f:
                json.dump(embeddings_to_save, f, ensure_ascii=False, indent=4)
                print(f"Embedding‌های فایل {pdf_name} ذخیره شدند.")
        else:
            print(f"هشدار: فایل {pdf_name} حاوی متن قابل استخراج نیست.")

    def _compute_embeddings_parallel(self, chunks):
        """
        محاسبه Embedding‌ها به صورت موازی
        """
        embeddings = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self.ollama_api.get_embedding, chunk['text'], self.embedding_model): chunk for chunk in chunks}
            for future in futures:
                chunk = futures[future]
                try:
                    embedding = future.result()
                    if embedding:
                        embeddings.append(embedding)
                    else:
                        print(f"هشدار: embedding برای متن زیر تولید نشد:\n{chunk['text'][:100]}...")
                        embeddings.append([0] * 384)  # مقدار پیش‌فرض برای embedding ناموفق
                except Exception as e:
                    print(f"خطا در محاسبه embedding برای متن زیر:\n{chunk['text'][:100]}...\nخطا: {e}")
                    embeddings.append([0] * 384)
        return embeddings

    def load_embeddings(self, pdf_name: str):
        """
        بارگذاری embedding‌ها از فایل JSON
        """
        embeddings_file = os.path.join(self.embeddings_folder, f"{os.path.splitext(pdf_name)[0]}.json")
        if not os.path.exists(embeddings_file):
            print(f"فایل embedding برای {pdf_name} یافت نشد. در حال پردازش PDF...")
            self.process_pdf(pdf_name)

        try:
            with open(embeddings_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"خطا در بارگذاری فایل {embeddings_file}: {e}")
            return {}

    def search(self, query: str, pdf_name: str, top_k: int = 5, similarity_threshold: float = 0.7) -> list:
        """
        جستجوی معنایی در یک فایل PDF و بازگرداندن فقط بخش‌های مرتبط
        """
        query_embedding = self.ollama_api.get_embedding(query, self.embedding_model)
        embeddings = self.load_embeddings(pdf_name)

        results = []
        for text, embedding in embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity >= similarity_threshold:  # بررسی آستانه شباهت
                results.append({'context': text, 'similarity': similarity})

        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]  # فقط `top_k` نتیجه بازگردانده می‌شود

    def get_relevant_context(self, query: str, pdf_name: str, max_chars: int = 1000) -> str:
        """
        دریافت متن مرتبط با سوال کاربر با محدود کردن تعداد کاراکترهای خروجی
        """
        results = self.search(query, pdf_name, top_k=5, similarity_threshold=0.7)  # مقدار شباهت تنظیم شده

        context = ""
        total_chars = 0  # شمارش تعداد کاراکترها برای جلوگیری از ارسال بیش از حد داده

        if results:
            print("\nمتن‌های مرتبط یافت شده:")
            for result in results:
                text_chunk = result['context']
                similarity = result['similarity']

                if total_chars + len(text_chunk) <= max_chars:  # بررسی محدودیت
                    context += text_chunk + "\n"
                    total_chars += len(text_chunk)

                    print(f"📌 متن مرتبط (Similarity: {similarity:.2f}): {text_chunk[:100]}...")  # نمایش پیش‌نمایش
                else:
                    break
        else:
            print("\n⚠️ نتیجه مرتبطی یافت نشد.")

        return context.strip()  # حذف فاصله‌های اضافی و بازگشت فقط متن‌های مهم

    @staticmethod
    def _cosine_similarity(vec1, vec2):
        """
        محاسبه شباهت کسینوسی
        """
        vec1, vec2 = np.array(vec1), np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))