import speech_recognition as sr
import time

class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 3000  # کاهش آستانه انرژی
        self.microphone = sr.Microphone(device_index=None)  # استفاده از میکروفون پیش‌فرض

    def listen_for_audio(self, timeout=7, phrase_time_limit=15):
        """
        گوش دادن به صدای کاربر و تبدیل آن به متن
        :param timeout: حداکثر زمان انتظار برای شروع گفتار (ثانیه)
        :param phrase_time_limit: حداکثر زمان گفتار (ثانیه)
        :return: متن تشخیص داده شده یا رشته خالی در صورت خطا
        """
        try:
            with self.microphone as source:
                print("\nدر حال گوش دادن...")
                
                # تنظیم حساسیت میکروفون برای تشخیص بهتر گفتار فارسی
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                time.sleep(0.5)  # کاهش تاخیر
                
                try:
                    # گوش دادن به صدای کاربر
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                    
                    # تشخیص گفتار فارسی
                    text = self.recognizer.recognize_google(audio, language='fa-IR')
                    print(f"شما گفتید: {text}")
                    return text
                    
                except sr.WaitTimeoutError:
                    print("زمان گوش دادن به پایان رسید.")
                    return ""
                except sr.UnknownValueError:
                    print("متوجه نشدم. لطفاً دوباره تلاش کنید.")
                    return ""
                except sr.RequestError as e:
                    print(f"خطا در سرویس تشخیص گفتار: {e}")
                    return ""
                
        except Exception as e:
            print(f"خطا در دسترسی به میکروفون: {e}")
            return ""

def main():
    """
    تابع اصلی برای تست مستقیم ماژول
    """
    print("\n=== تبدیل گفتار به متن ===")
    print("برای خروج، کلمه 'خروج' را بگویید.")
    print("="*50 + "\n")
    
    recognizer = SpeechRecognizer()
    
    while True:
        try:
            text = recognizer.listen_for_audio()
            
            if text.lower() in ['خروج', 'exit', 'quit']:
                print("\nخداحافظ!")
                break
                
            if not text:
                continue
                
        except KeyboardInterrupt:
            print("\n\nبرنامه توسط کاربر متوقف شد.")
            break
        except Exception as e:
            print(f"\nخطا: {e}")

if __name__ == "__main__":
    main() 