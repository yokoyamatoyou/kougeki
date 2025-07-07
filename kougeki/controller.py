import asyncio
import logging
from tkinter import filedialog, messagebox

import pandas as pd

from . import services
from .models import AggressivenessResult, ModerationResult

logger = logging.getLogger(__name__)


class ModerationController:
    def __init__(self, view):
        self.view = view
        self.df: pd.DataFrame | None = None

    def load_excel_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        try:
            self.df = pd.read_excel(file_path, sheet_name=0)
            self.view.update_status(
                f"ファイルを読み込みました: {len(self.df)}件のデータ", "green"
            )
            self.view.enable_analyze(True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to load excel")
            self.view.update_status("ファイルの読み込みに失敗しました", "red")
            messagebox.showerror(
                "読み込みエラー", f"ファイルを読み込めませんでした: {exc}"
            )

    def save_results(self):
        if self.df is None:
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")]
        )
        if not save_path:
            return
        try:
            self.df.to_excel(save_path, index=False)
            self.view.update_status("結果を保存しました", "green")
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to save excel")
            self.view.update_status("保存に失敗しました", "red")
            messagebox.showerror("保存エラー", f"ファイルを保存できませんでした: {exc}")

    def analyze_file_sync(self):
        asyncio.run(self._analyze_file())

    async def _analyze_file(self):
        if self.df is None or "投稿内容" not in self.df.columns:
            self.view.update_status("「投稿内容」列が見つかりません", "red")
            return
        self.view.enable_buttons(False)
        total_rows = len(self.df)
        category_names = [
            "hate",
            "hate/threatening",
            "self-harm",
            "sexual",
            "sexual/minors",
            "violence",
            "violence/graphic",
        ]
        category_flags = {name: [] for name in category_names}
        category_scores = {name: [] for name in category_names}
        ag_scores: list[int | None] = []
        ag_reasons: list[str | None] = []
        for idx, row in self.df.iterrows():
            text = row["投稿内容"]
            mod_res: ModerationResult = await services.moderate_text(text)
            ag_res: AggressivenessResult = await services.get_aggressiveness_score(text)

            for name in category_names:
                attr = name.replace("/", "_")
                category_flags[name].append(getattr(mod_res.categories, attr))
                category_scores[name].append(getattr(mod_res.scores, attr))

            ag_scores.append(ag_res.score)
            ag_reasons.append(ag_res.reason)

            progress = (idx + 1) / total_rows
            self.view.update_progress(progress)
            self.view.update_status(f"分析中... {idx + 1}/{total_rows}")
            await asyncio.sleep(0)  # allow UI update

        for name in category_names:
            self.df[f"{name}_flag"] = category_flags[name]
            self.df[f"{name}_score"] = category_scores[name]
        self.df["aggressiveness_score"] = ag_scores
        self.df["aggressiveness_reason"] = ag_reasons
        self.view.update_status("分析が完了しました", "green")
        self.view.enable_buttons(True)
