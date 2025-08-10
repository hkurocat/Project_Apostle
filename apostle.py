import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import subprocess
import datetime

# --- 設定項目 ---
# このスクリプトが存在する場所を基準にする
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
ZENN_REPO_DIR = BASE_DIR 
# --- ここまで ---

class ApostleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Apostle v1.0")
        self.geometry("800x600")

        # --- テンプレート選択 ---
        self.template_frame = ttk.LabelFrame(self, text="1. テンプレート選択")
        self.template_frame.pack(padx=10, pady=5, fill="x")

        self.templates = self.get_templates()
        self.selected_template = tk.StringVar()
        self.template_combo = ttk.Combobox(
            self.template_frame,
            textvariable=self.selected_template,
            values=self.templates,
            state="readonly"
        )
        self.template_combo.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        self.template_combo.bind("<<ComboboxSelected>>", self.load_template)

        # --- 記事内容編集 ---
        self.editor_frame = ttk.LabelFrame(self, text="2. 最終編集")
        self.editor_frame.pack(padx=10, pady=5, expand=True, fill="both")

        self.editor = scrolledtext.ScrolledText(self.editor_frame, wrap=tk.WORD, undo=True)
        self.editor.pack(expand=True, fill="both", padx=5, pady=5)

        # --- 公開実行 ---
        self.action_frame = ttk.LabelFrame(self, text="3. 公開実行")
        self.action_frame.pack(padx=10, pady=5, fill="x")
        
        self.generate_button = ttk.Button(self.action_frame, text="Zenn用記事ファイルとして生成", command=self.generate_article_file)
        self.generate_button.pack(side="left", padx=5, pady=5)
        
        self.publish_button = ttk.Button(self.action_frame, text="Zennへ公開 (Git Push)", command=self.publish_to_zenn)
        self.publish_button.pack(side="right", padx=5, pady=5)


    def get_templates(self):
        """templatesディレクトリからテンプレートファイルの一覧を取得"""
        if not os.path.exists(TEMPLATE_DIR):
            os.makedirs(TEMPLATE_DIR)
        return [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".md")]

    def load_template(self, event=None):
        """選択されたテンプレートをエディタに読み込む"""
        template_name = self.selected_template.get()
        if not template_name:
            return
        
        try:
            with open(os.path.join(TEMPLATE_DIR, template_name), 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.delete('1.0', tk.END)
            self.editor.insert('1.0', content)
            messagebox.showinfo("読み込み完了", f"'{template_name}'を読み込みました。")
        except Exception as e:
            messagebox.showerror("エラー", f"テンプレートの読み込みに失敗しました:\n{e}")

    def generate_article_file(self):
        """エディタの内容をZennの記事ファイルとして保存する"""
        content = self.editor.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "記事内容が空です。")
            return

        # Zenn CLIで新しい記事を作成
        try:
            # slugはファイル名やURLになる部分。ここではシンプルに日付から生成。
            slug = f"wsl-orchestrator-intro-{datetime.datetime.now().strftime('%Y%m%d')}"
            
            # zenn new:article コマンドを実行
            subprocess.run(
                ["zenn", "new:article", "--slug", slug, "--title", "WSL Orchestrator紹介"], 
                cwd=ZENN_REPO_DIR, 
                check=True,
                shell=True # Windowsでzenn.cmdを認識させるために必要
            )
            
            # 生成されたファイルに内容を書き込む
            filepath = os.path.join(ZENN_REPO_DIR, "articles", f"{slug}.md")
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)

            messagebox.showinfo("生成完了", f"Zennの記事ファイルを以下に生成しました:\n{filepath}\n\nプレビューで内容を確認してください。")

        except FileNotFoundError:
             messagebox.showerror("エラー", "Zenn CLIがインストールされていないか、PATHが通っていません。")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Zenn CLIエラー", f"Zenn CLIコマンドの実行に失敗しました:\n{e}")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル生成に失敗しました:\n{e}")

    def publish_to_zenn(self):
        """Gitコマンドを実行してZennに公開する (この機能はまだ実装していません)"""
        messagebox.showinfo("未実装", "Git連携による自動公開機能は、次期バージョンで実装予定です。")


if __name__ == "__main__":
    app = ApostleApp()
    app.mainloop()