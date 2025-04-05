import re

class TextProcessor:
    @staticmethod
    def is_persian_char(char: str) -> bool:
        """بررسی می‌کند که آیا کاراکتر یک حرف فارسی است"""
        persian_chars = set('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')
        return char in persian_chars

    @staticmethod
    def find_last_complete_word(text: str) -> int:
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
        if last_space > 0 and TextProcessor.is_persian_char(text[last_space - 1]):
            # اگر کاراکتر قبل از فاصله فارسی است، به عقب برمی‌گردیم تا کلمه کامل پیدا کنیم
            for i in range(last_space - 1, -1, -1):
                if not TextProcessor.is_persian_char(text[i]):
                    return i + 1
            return 0

        return last_space

    @staticmethod
    def clean_response(response: str) -> str:
        """
        حذف کاراکترهای غیر از حروف فارسی، انگلیسی، فاصله و برخی علامت‌ها از پاسخ
        Args:
            response: متن پاسخ
        Returns:
            str: متن پاک‌سازی‌شده
        """
        # فقط حروف فارسی، انگلیسی، فاصله و علامت‌های . , ! را نگه می‌دارد
        return re.sub(r'[^\u0600-\u06FFa-zA-Z\s.,!]', '', response)
