import customtkinter as ctk

from .controller import ModerationController

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ModerationView(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.controller = ModerationController(self)
        self.title("テキストモデレーションツール")
        self.geometry("600x400")
        self.create_ui()

    def create_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="テキストモデレーション分析",
            font=("Helvetica", 24, "bold"),
        )
        self.title_label.pack(pady=20)

        self.status_label = ctk.CTkLabel(
            self.main_frame, text="ファイルを選択してください", font=("Helvetica", 12)
        )
        self.status_label.pack(pady=10)

        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(pady=20)

        self.upload_button = ctk.CTkButton(
            self.button_frame,
            text="ファイルを選択",
            command=self.controller.load_excel_file,
            width=200,
            height=40,
        )
        self.upload_button.pack(pady=10)

        self.analyze_button = ctk.CTkButton(
            self.button_frame,
            text="分析開始",
            command=self.controller.analyze_file_sync,
            width=200,
            height=40,
            state="disabled",
        )
        self.analyze_button.pack(pady=10)

        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="結果を保存",
            command=self.controller.save_results,
            width=200,
            height=40,
            state="disabled",
        )
        self.save_button.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame, width=400, height=20, mode="determinate"
        )
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

    def update_status(self, text: str, color: str = "white"):
        self.status_label.configure(text=text, text_color=color)

    def update_progress(self, value: float):
        self.progress_bar.set(value)
        self.update_idletasks()

    def enable_buttons(self, enable: bool):
        state = "normal" if enable else "disabled"
        self.upload_button.configure(state=state)
        self.save_button.configure(state=state)
        self.analyze_button.configure(state=state)

    def enable_analyze(self, enable: bool):
        self.analyze_button.configure(state="normal" if enable else "disabled")
        if enable:
            self.save_button.configure(state="disabled")
