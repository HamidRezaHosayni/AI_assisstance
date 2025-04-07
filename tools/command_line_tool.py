import subprocess
import os
import time

class CommandLineTool:
    def process_commands(self, response: str):
        """
        پردازش و اجرای دستورات خط فرمان از پاسخ مدل
        """
        try:
            # استخراج دستورات بین %% و ذخیره آنها در فایل
            commands = self._extract_commands(response)
            if not commands:
                return "⚠️ دستوری برای اجرا یافت نشد یا قالب پاسخ نادرست است."

            # ذخیره دستورات در فایل و اجرای آن
            result = self._execute_commands_in_file(commands)
            return result
        except Exception as e:
            print(f"خطا در پردازش دستورات: {e}")
            return f"خطا در پردازش دستورات: {e}"

    def _extract_commands(self, response: str):
        """
        استخراج دستورات بین %% از پاسخ مدل
        """
        commands = []
        start = response.find("%%")
        while start != -1:
            end = response.find("%%", start + 2)
            if end == -1:
                break
            command = response[start + 2:end].strip()
            if command:  # اطمینان از اینکه دستور خالی نیست
                commands.append(command)
            start = response.find("%%", end + 2)
        return commands

    def _execute_commands_in_file(self, commands: list):
        """
        ذخیره دستورات در فایل روی دسکتاپ و اجرای آن
        """
        try:
            # تعیین نوع فایل بر اساس سیستم‌عامل
            is_windows = os.name == 'nt'
            file_extension = ".bat" if is_windows else ".sh"

            # مسیر دسکتاپ
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            script_file_path = os.path.join(desktop_path, f"temp_script{file_extension}")

            # نوشتن دستورات در فایل
            print(f"🔄 در حال ایجاد فایل اسکریپت در مسیر: {script_file_path}")
            with open(script_file_path, "w", encoding="utf-8") as f:
                if not is_windows:
                    f.write("#!/bin/bash\n")  # اضافه کردن shebang برای فایل‌های sh
                f.write("\n".join(commands))
                f.flush()  # اطمینان از نوشتن داده‌ها در فایل
                os.fsync(f.fileno())  # اطمینان از نوشتن کامل داده‌ها به دیسک

            # تنظیم مجوز اجرا برای فایل‌های sh در لینوکس/مک
            if not is_windows:
                os.chmod(script_file_path, 0o777)  # تنظیم دسترسی کامل برای فایل
                print(f"✅ مجوز ۷۷۷ برای فایل تنظیم شد.")

            # اضافه کردن تأخیر کوتاه برای اطمینان از آزاد شدن فایل
            time.sleep(0.1)

            # پرسیدن تأیید از کاربر
            while True:
                user_input = input(f"آیا فایل اسکریپت {script_file_path} اجرا شود؟ (y/n): ").strip().lower()
                if user_input == 'y':
                    break
                elif user_input == 'n':
                    print("❌ اجرای فایل لغو شد.")
                    return "❌ اجرای فایل لغو شد."

            # اجرای فایل از طریق خط فرمان
            print(f"🚀 در حال اجرای فایل: {script_file_path}")
            if is_windows:
                # اجرای فایل در ویندوز (در صورت نیاز به دسترسی مدیر)
                command = f'cmd /c "{script_file_path}"'
            else:
                # اجرای فایل در لینوکس/مک (در صورت نیاز به sudo)
                command = f'bash {script_file_path}'

            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            # حذف فایل پس از اجرا
            if os.path.exists(script_file_path):
                os.remove(script_file_path)
                print(f"🗑️ فایل {script_file_path} حذف شد.")

            # بررسی نتیجه اجرا
            if result.returncode == 0:
                print(f"✅ دستورات با موفقیت اجرا شدند:\n{result.stdout}")
                return f"✅ دستورات با موفقیت اجرا شدند:\n{result.stdout}"
            else:
                print(f"❌ خطا در اجرای دستورات:\n{result.stderr}")
                return f"❌ خطا در اجرای دستورات:\n{result.stderr}"
        except Exception as e:
            print(f"خطا در اجرای دستورات از فایل: {e}")
            return f"خطا در اجرای دستورات از فایل: {e}"
