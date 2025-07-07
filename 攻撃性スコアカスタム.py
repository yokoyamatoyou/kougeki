import os
import time
from openai import OpenAI
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox

# テーマとカラーモードの設定
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# OpenAI クライアントの初期化
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

if client.api_key is None:
    raise ValueError("OpenAI APIキーが設定されていません。環境変数 'OPENAI_API_KEY' を設定してください。")

class ModerationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # ウィンドウの基本設定
        self.title("テキストモデレーションツール")
        self.geometry("600x400")
        
        # データフレームの初期化
        self.df = None
        
        # UIの作成
        self.create_ui()
        
    def create_ui(self):
        # メインフレーム
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # タイトル
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="テキストモデレーション分析",
            font=("Helvetica", 24, "bold")
        )
        self.title_label.pack(pady=20)
        
        # ステータス表示
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="ファイルを選択してください",
            font=("Helvetica", 12)
        )
        self.status_label.pack(pady=10)
        
        # ボタンフレーム
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(pady=20)
        
        # アップロードボタン
        self.upload_button = ctk.CTkButton(
            self.button_frame,
            text="ファイルを選択",
            command=self.load_excel_file,
            width=200,
            height=40
        )
        self.upload_button.pack(pady=10)
        
        # 分析ボタン
        self.analyze_button = ctk.CTkButton(
            self.button_frame,
            text="分析開始",
            command=self.analyze_file,
            width=200,
            height=40,
            state="disabled"
        )
        self.analyze_button.pack(pady=10)
        
        # 保存ボタン
        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="結果を保存",
            command=self.save_results,
            width=200,
            height=40,
            state="disabled"
        )
        self.save_button.pack(pady=10)
        
        # プログレスバー
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            width=400,
            height=20,
            mode="determinate"
        )
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        
    def load_excel_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
            
        try:
            self.df = pd.read_excel(file_path, sheet_name=0)
            self.status_label.configure(
                text=f"ファイルを読み込みました: {len(self.df)}件のデータ",
                text_color="green"
            )
            self.analyze_button.configure(state="normal")
            
        except Exception as e:
            self.status_label.configure(
                text="ファイルの読み込みに失敗しました",
                text_color="red"
            )
            messagebox.showerror("読み込みエラー", f"ファイルを読み込めませんでした: {e}")
            
    def moderate_text(self, text):
        response = client.moderations.create(
            input=text,
            model="omni-moderation-latest"
        )
        categories = response.results[0].categories
        category_scores = response.results[0].category_scores
        return categories, category_scores
        
    def get_aggressiveness_score(self, text, max_retries=3):
        prompt = f"""
あなたはソーシャルメディアの投稿を分析し、その攻撃性を評価する専門家です。
以下の基準に従って、与えられた文章の攻撃性スコアを決定し、その理由を説明してください。

評価基準:
0: 攻撃性なし。中立的で誰に対しても敵意が感じられない。
1～2: 非常に軽度の攻撃性。配慮に欠ける表現だが、攻撃意図が明確ではない。
3～4: 軽度の攻撃性。間接的な批判や皮肉が含まれている。
5～6: 中程度の攻撃性。明確な批判や侮辱的な表現が見られる。
7～8: 高度の攻撃性。強い侮辱や敵意を伴う表現。
9: 極度の攻撃性。暴力的な脅迫や人権侵害を伴うような非常に攻撃的な内容。

評価の際は以下の点を考慮してください：
1. 文脈：文章全体の意味を考慮してください。
2. 意図：書き手の意図（冗談、皮肉、純粋な質問など）を推測してください。
3. 対象：攻撃性が特定の個人やグループに向けられているかを確認してください。
4. 影響：その表現が読み手に与える可能性のある影響を考慮してください。
5. 文化的背景：可能な限り、文化的な文脈を考慮してください。

分析対象の文章: {text}

以下の形式で回答してください：
スコア: [0-9の整数]
理由: [40-60文字で、なぜそのスコアを付けたのかを具体的に説明]
"""

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini-2024-07-18",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes text for aggressiveness."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=1.0,
                    top_p=0.9
                )

                response_text = response.choices[0].message.content.strip()
                
                lines = response_text.split('\n')
                score = None
                reason = None
                
                for line in lines:
                    if line.startswith('スコア:'):
                        score_str = line.replace('スコア:', '').strip()
                        if score_str.isdigit():
                            score = int(score_str)
                    elif line.startswith('理由:'):
                        reason = line.replace('理由:', '').strip()

                if score is not None and reason is not None and 0 <= score <= 9:
                    return score, reason

                print(f"無効な回答（試行 {attempt + 1}/{max_retries}）: {response_text}")
            except Exception as e:
                print(f"エラーが発生しました（試行 {attempt + 1}/{max_retries}）: {str(e)}")

            time.sleep(1)

        return None, None

    def analyze_file(self):
        if '投稿内容' not in self.df.columns:
            self.status_label.configure(
                text="「投稿内容」列が見つかりません",
                text_color="red"
            )
            return
            
        self.analyze_button.configure(state="disabled")
        self.upload_button.configure(state="disabled")
        self.status_label.configure(text="分析を実行中...")
        
        category_names = ["hate", "hate/threatening", "self-harm", "sexual", 
                         "sexual/minors", "violence", "violence/graphic"]
        category_flags = {name: [] for name in category_names}
        category_scores = {name: [] for name in category_names}
        aggressiveness_scores = []
        aggressiveness_reasons = []
        
        total_rows = len(self.df)
        
        for index, row in self.df.iterrows():
            text = row['投稿内容']
            categories, scores = self.moderate_text(text)
            
            for name in category_names:
                category_flags[name].append(getattr(categories, name.replace("/", "_"), False))
                category_scores[name].append(getattr(scores, name.replace("/", "_"), 0.0))
                
            score, reason = self.get_aggressiveness_score(text)
            aggressiveness_scores.append(score)
            aggressiveness_reasons.append(reason)
            
            progress = (index + 1) / total_rows
            self.progress_bar.set(progress)
            self.status_label.configure(text=f"分析中... {index + 1}/{total_rows}")
            self.update()
            
        for name in category_names:
            self.df[f'{name}_flag'] = category_flags[name]
            self.df[f'{name}_score'] = category_scores[name]
            
        self.df['aggressiveness_score'] = aggressiveness_scores
        self.df['aggressiveness_reason'] = aggressiveness_reasons
        
        self.status_label.configure(
            text="分析が完了しました",
            text_color="green"
        )
        self.save_button.configure(state="normal")
        self.upload_button.configure(state="normal")
        self.analyze_button.configure(state="normal")
        
    def save_results(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if not save_path:
            return
            
        try:
            self.df.to_excel(save_path, index=False)
            self.status_label.configure(
                text="結果を保存しました",
                text_color="green"
            )
        except Exception as e:
            self.status_label.configure(
                text="保存に失敗しました",
                text_color="red"
            )
            messagebox.showerror("保存エラー", f"ファイルを保存できませんでした: {e}")

if __name__ == "__main__":
    app = ModerationApp()
    app.mainloop()