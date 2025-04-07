from tools.command_line_tool import CommandLineTool

class ToolManager:
    def __init__(self):
        # ابزارهای موجود را اینجا تعریف کنید
        self.tools = {
            "خط فرمان": CommandLineTool()
        }

    def process_response(self, response: str):
        """
        پردازش پاسخ مدل و ارسال آن به ابزار مناسب
        """
        try:
            # استخراج خط اول برای شناسایی ابزار
            first_line = response.splitlines()[0].strip()
            if "اجرا در خط فرمان" in first_line or "اجرادرخطفرمان" in first_line:
                # ارسال کل پاسخ به ابزار خط فرمان
                return self.tools["خط فرمان"].process_commands(response)
            else:
                print("⚠️ ابزار مناسب برای این پاسخ یافت نشد یا قالب پاسخ نادرست است.")
                return "⚠️ ابزار مناسب یافت نشد یا قالب پاسخ نادرست است."
        except Exception as e:
            print(f"خطا در پردازش پاسخ: {e}")
            return f"خطا در پردازش پاسخ: {e}"
