import customtkinter as ctk
import json
import os
import time
import threading
import tkinter as tk
from datetime import datetime, timedelta

# 字體優化設定
UI_FONT_FAMILY = "Segoe UI"
TECH_FONT_FAMILY = "Segoe UI Black"
ZH_FONT_FAMILY = "Microsoft JhengHei"

class RocketNotification(ctk.CTkToplevel):
    """最上層火箭動畫通知視窗"""
    def __init__(self, task_text, callback=None):
        super().__init__()
        self.task_text = task_text
        self.callback = callback
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "black")
        self.config(bg="black")
        
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.win_width = 500
        self.win_height = 250
        
        self.current_x = -self.win_width
        self.target_x = (self.screen_width - self.win_width) // 2
        self.y_pos = (self.screen_height - self.win_height) // 2
        
        self.geometry(f"{self.win_width}x{self.win_height}+{self.current_x}+{self.y_pos}")
        self.setup_ui()
        self.animate_in()

    def setup_ui(self):
        self.container = ctk.CTkFrame(self, fg_color="#1a1a2e", border_width=2, border_color="#00d2ff", corner_radius=20)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.rocket_label = ctk.CTkLabel(self.container, text="🚀", font=(UI_FONT_FAMILY, 60))
        self.rocket_label.pack(pady=(20, 0))
        
        self.title_label = ctk.CTkLabel(self.container, text="任務提醒", font=(ZH_FONT_FAMILY, 18, "bold"), text_color="#00d2ff")
        self.title_label.pack()
        
        self.task_label = ctk.CTkLabel(self.container, text=self.task_text, font=(ZH_FONT_FAMILY, 16), wraplength=400)
        self.task_label.pack(pady=10)
        
        self.ok_button = ctk.CTkButton(self.container, text="我知道了", fg_color="#00d2ff", hover_color="#0099cc", 
                                      text_color="black", font=(ZH_FONT_FAMILY, 14, "bold"),
                                      command=self.animate_out)
        self.ok_button.pack(pady=(0, 20))

    def animate_in(self):
        if self.current_x < self.target_x:
            step = (self.target_x - self.current_x) / 10 + 2
            self.current_x += int(step)
            self.geometry(f"{self.win_width}x{self.win_height}+{self.current_x}+{self.y_pos}")
            self.after(10, self.animate_in)
        else:
            self.current_x = self.target_x
            self.geometry(f"{self.win_width}x{self.win_height}+{self.current_x}+{self.y_pos}")

    def animate_out(self):
        if self.current_x < self.screen_width:
            step = (self.current_x - self.target_x) / 10 + 15
            self.current_x += int(step)
            self.geometry(f"{self.win_width}x{self.win_height}+{self.current_x}+{self.y_pos}")
            self.after(10, self.animate_out)
        else:
            if self.callback:
                self.callback()
            self.destroy()

class EditDialog(ctk.CTkToplevel):
    """編輯任務與設定時間的對話框"""
    def __init__(self, parent, task_data, on_save):
        super().__init__(parent)
        self.title("編輯任務")
        self.geometry("400x350")
        self.on_save = on_save
        self.task_data = task_data
        self.configure(fg_color="#0f0f1a")
        self.setup_ui()
        self.grab_set()

    def setup_ui(self):
        label = ctk.CTkLabel(self, text="編輯科技任務", font=(ZH_FONT_FAMILY, 20, "bold"), text_color="#00d2ff")
        label.pack(pady=20)
        
        self.entry = ctk.CTkEntry(self, width=300, height=40, fg_color="#1a1a2e", border_color="#00d2ff", font=(ZH_FONT_FAMILY, 14))
        self.entry.insert(0, self.task_data["text"])
        self.entry.pack(pady=10)
        
        time_label = ctk.CTkLabel(self, text="設定提醒時間 (格式: HH:MM)", font=(ZH_FONT_FAMILY, 14))
        time_label.pack(pady=(10, 0))
        
        self.time_entry = ctk.CTkEntry(self, width=300, height=40, placeholder_text="例如 14:30", fg_color="#1a1a2e", border_color="#00d2ff", font=(UI_FONT_FAMILY, 14))
        if self.task_data.get("remind_time"):
            self.time_entry.insert(0, self.task_data["remind_time"])
        self.time_entry.pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        save_btn = ctk.CTkButton(btn_frame, text="儲存更新", fg_color="#00d2ff", text_color="black", hover_color="#0099cc", font=(ZH_FONT_FAMILY, 14, "bold"), command=self.save)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="取消", fg_color="#333333", font=(ZH_FONT_FAMILY, 14), command=self.destroy)
        cancel_btn.pack(side="left", padx=10)

    def save(self):
        new_text = self.entry.get()
        new_time = self.time_entry.get()
        if new_text.strip():
            self.on_save(new_text, new_time)
            self.destroy()

class TodoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NEON TODO - 科技待辦系統")
        self.geometry("550x700")
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="#0f0f1a")

        self.db_path = "tasks.json"
        self.tasks = self.load_tasks()
        
        self.setup_ui()
        self.refresh_tasks()
        
        self.check_thread_running = True
        self.check_thread = threading.Thread(target=self.check_reminders, daemon=True)
        self.check_thread.start()

    def setup_ui(self):
        # 標題區域
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=30, fill="x", padx=30)

        self.title_label = ctk.CTkLabel(self.header_frame, text="CYBERPUNK TODO", 
                                       font=ctk.CTkFont(family=TECH_FONT_FAMILY, size=32),
                                       text_color="#00d2ff")
        self.title_label.pack(side="left")

        # 全部清空按鈕 (置於右上角)
        self.clear_all_btn = ctk.CTkButton(self.header_frame, text="CLEAR ALL", width=100, height=30, 
                                          fg_color="#ff3333", hover_color="#cc0000",
                                          text_color="white", font=(UI_FONT_FAMILY, 12, "bold"),
                                          command=self.clear_all_tasks)
        self.clear_all_btn.pack(side="right")

        # 輸入區域
        self.input_frame = ctk.CTkFrame(self, fg_color="#1a1a2e", border_width=1, border_color="#00d2ff")
        self.input_frame.pack(padx=30, fill="x")

        self.task_entry = ctk.CTkEntry(self.input_frame, placeholder_text="輸入新任務指令...", 
                                      height=45, fg_color="transparent", border_width=0,
                                      font=(ZH_FONT_FAMILY, 15))
        self.task_entry.pack(side="left", padx=10, fill="x", expand=True)
        self.task_entry.bind("<Return>", lambda event: self.add_task())

        self.add_button = ctk.CTkButton(self.input_frame, text="DEPLOY", width=100, height=35, 
                                       fg_color="#00d2ff", text_color="black", font=(TECH_FONT_FAMILY, 14),
                                       command=self.add_task)
        self.add_button.pack(side="right", padx=5)

        # 任務列表
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="ACTIVE TASKS", 
                                                 fg_color="#0f0f1a", label_text_color="#00d2ff",
                                                 border_width=1, border_color="#333333",
                                                 label_font=(TECH_FONT_FAMILY, 14))
        self.scroll_frame.pack(padx=30, pady=30, fill="both", expand=True)

    def load_tasks(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_tasks(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    def add_task(self):
        text = self.task_entry.get()
        if text.strip():
            self.tasks.append({"text": text, "completed": False, "remind_time": "", "notified": False})
            self.save_tasks()
            self.task_entry.delete(0, "end")
            self.refresh_tasks()

    def edit_task(self, index):
        def on_save(new_text, new_time):
            self.tasks[index]["text"] = new_text
            self.tasks[index]["remind_time"] = new_time
            self.tasks[index]["notified"] = False
            self.save_tasks()
            self.refresh_tasks()
            
        EditDialog(self, self.tasks[index], on_save)

    def delete_task(self, index):
        self.tasks.pop(index)
        self.save_tasks()
        self.refresh_tasks()

    def clear_all_tasks(self):
        """全部清空功能"""
        # 使用自定義對話框確認
        dialog = ctk.CTkInputDialog(text="輸入 'CLEAR' 以確認清空所有任務:", title="確認清空")
        response = dialog.get_input()
        if response and response.upper() == "CLEAR":
            self.tasks = []
            self.save_tasks()
            self.refresh_tasks()

    def toggle_task(self, index):
        self.tasks[index]["completed"] = not self.tasks[index]["completed"]
        self.save_tasks()
        self.refresh_tasks()

    def refresh_tasks(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for i, task in enumerate(self.tasks):
            item_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#1a1a2e", corner_radius=10)
            item_frame.pack(fill="x", pady=5, padx=5)

            cb = ctk.CTkCheckBox(item_frame, text=task["text"], 
                                font=(ZH_FONT_FAMILY, 15),
                                border_color="#00d2ff", checkmark_color="#00d2ff",
                                command=lambda idx=i: self.toggle_task(idx))
            if task["completed"]:
                cb.select()
                cb.configure(text_color="gray")
            cb.pack(side="left", padx=10, pady=10, fill="x", expand=True)
            
            if task.get("remind_time"):
                time_label = ctk.CTkLabel(item_frame, text=f"⏰ {task['remind_time']}", 
                                         font=(UI_FONT_FAMILY, 11), text_color="#00d2ff")
                time_label.pack(side="left", padx=5)

            edit_btn = ctk.CTkButton(item_frame, text="EDIT", width=50, height=25, 
                                    fg_color="transparent", border_width=1, border_color="#00d2ff",
                                    text_color="#00d2ff", hover_color="#1a3a4e",
                                    font=(UI_FONT_FAMILY, 11, "bold"),
                                    command=lambda idx=i: self.edit_task(idx))
            edit_btn.pack(side="left", padx=5)

            del_btn = ctk.CTkButton(item_frame, text="DEL", width=50, height=25, 
                                   fg_color="#ff4d4d", hover_color="#cc0000",
                                   text_color="white", font=(UI_FONT_FAMILY, 11, "bold"),
                                   command=lambda idx=i: self.delete_task(idx))
            del_btn.pack(side="right", padx=10)

    def check_reminders(self):
        while self.check_thread_running:
            now = datetime.now().strftime("%H:%M")
            changed = False
            for task in self.tasks:
                if task.get("remind_time") == now and not task.get("notified", False) and not task["completed"]:
                    task["notified"] = True
                    changed = True
                    self.after(0, lambda t=task["text"]: RocketNotification(t))
            
            if changed:
                self.save_tasks()
            
            time.sleep(30)

if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
