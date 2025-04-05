import os
from dotenv import load_dotenv

class Environment:
    @staticmethod
    def load_env():
        """بارگذاری متغیرهای محیطی"""
        load_dotenv()

    @staticmethod
    def get_env_variable(key: str, default: str = None) -> str:
        """
        دریافت مقدار متغیر محیطی
        Args:
            key: کلید متغیر محیطی
            default: مقدار پیش‌فرض در صورت عدم وجود متغیر
        Returns:
            str: مقدار متغیر محیطی
        """
        return os.getenv(key, default)
