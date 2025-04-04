import subprocess
import time

class TextToSpeech:
    """
    کلاس تبدیل متن به گفتار با استفاده از espeak
    این کلاس امکان تبدیل متن فارسی به گفتار را فراهم می‌کند.
    """
    
    def __init__(self, speed=140, pitch=70, volume=100, gap=2, emphasis=4, sentence_break=1):
        """
        مقداردهی اولیه کلاس
        
        Args:
            speed (int): سرعت گفتار (پیش‌فرض: 140)
            pitch (int): زیر و بمی صدا (پیش‌فرض: 70)
            volume (int): بلندی صدا (پیش‌فرض: 100)
            gap (int): فاصله بین کلمات (پیش‌فرض: 2)
            emphasis (int): تأکید روی کلمات (پیش‌فرض: 4)
            sentence_break (int): مکث بین جملات (پیش‌فرض: 1)
        """
        self.speed = speed
        self.pitch = pitch
        self.volume = volume
        self.gap = gap
        self.emphasis = emphasis
        self.sentence_break = sentence_break
        
        try:
            subprocess.run(['espeak', '--version'], capture_output=True, check=True)
            print("موتور تبدیل متن به گفتار با موفقیت راه‌اندازی شد.")
        except FileNotFoundError:
            print("خطا: espeak نصب نشده است. لطفاً با دستور زیر نصب کنید:")
            print("sudo apt-get install espeak")
            raise
        except Exception as e:
            print(f"خطا در راه‌اندازی موتور تبدیل متن به گفتار: {e}")
            raise
    
    def speak(self, text: str) -> bool:
        """
        تبدیل متن به گفتار و پخش آن
        
        Args:
            text (str): متن مورد نظر برای تبدیل به گفتار
            
        Returns:
            bool: True اگر موفقیت‌آمیز باشد, False در غیر این صورت
        """
        if not text:
            print("متن خالی است!")
            return False
            
        try:
            print(f"\nدر حال پخش: {text}")
            command = [
                'espeak',
                '-v', 'fa+m2',
                '-s', str(self.speed),
                '-p', str(self.pitch),
                '-a', str(self.volume),
                '-g', str(self.gap),
                '-k', str(self.emphasis),
                '-b', str(self.sentence_break),
                '--punct=",.!?؟"',
                text
            ]
            
            process = subprocess.run(command, capture_output=True, text=True)
            if process.returncode == 0:
                return True
            else:
                print(f"خطا در اجرای espeak: {process.stderr}")
                return False
            
        except Exception as e:
            print(f"خطا در تبدیل متن به گفتار: {e}")
            return False
    
    def set_speed(self, speed: int):
        """تنظیم سرعت گفتار"""
        self.speed = speed
    
    def set_pitch(self, pitch: int):
        """تنظیم زیر و بمی صدا"""
        self.pitch = pitch
    
    def set_volume(self, volume: int):
        """تنظیم بلندی صدا"""
        self.volume = volume
    
    def set_gap(self, gap: int):
        """تنظیم فاصله بین کلمات"""
        self.gap = gap
    
    def set_emphasis(self, emphasis: int):
        """تنظیم تأکید روی کلمات"""
        self.emphasis = emphasis
    
    def set_sentence_break(self, break_time: int):
        """تنظیم مکث بین جملات"""
        self.sentence_break = break_time

def main():
    """
    تابع اصلی برای خواندن متن از ورودی کاربر
    """
    try:
        print("\n=== تبدیل متن به گفتار (پشتیبانی از فارسی) ===")
        print("برای خروج، کلمه 'خروج' را وارد کنید.")
        print("="*50 + "\n")
        
        # ایجاد نمونه از کلاس TextToSpeech
        tts = TextToSpeech()
        
        while True:
            # دریافت متن از کاربر
            text = input("\nلطفاً متن مورد نظر را وارد کنید: ")
            
            # بررسی درخواست خروج
            if text.lower() in ['خروج', 'exit', 'quit']:
                print("\nبرنامه به درخواست کاربر خاتمه یافت.")
                break
            
            # خواندن متن
            if text:
                if tts.speak(text):
                    print("\nمتن با موفقیت خوانده شد.")
                else:
                    print("\nخطا در خواندن متن!")
            
    except KeyboardInterrupt:
        print("\n\nبرنامه با فشردن Ctrl+C متوقف شد.")
    except Exception as e:
        print(f"\nخطای کلی در برنامه: {e}")
    finally:
        print("\nبرنامه به پایان رسید.")

if __name__ == "__main__":
    main()