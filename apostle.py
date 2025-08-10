import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import subprocess
import datetime
import configparser
import requests
import re
import json

# --- 定数 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")

class ApostleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Apostle v2.1") # バージョンを更新
        # 1. 起動時のウィンドウサイズを縦に拡大
        self.geometry("800x700")
        # 2. ウィンドウの最小サイズを初期サイズとして設定
        self.minsize(800, 700)

        self.api_key = self.load_config()

        # --- ターゲット選択 ---
        self.target_frame = ttk.LabelFrame(self, text="1. 公開先を選択")
        self.target_frame.pack(padx=10, pady=5, fill="x")
        
        self.target_var = tk.StringVar(value="Zenn")
        
        self.zenn_radio = ttk.Radiobutton(self.target_frame, text="Zenn", variable=self.target_var, value="Zenn", command=self.update_ui)
        self.zenn_radio.pack(side="left", padx=5, pady=5)
        
        self.devto_radio = ttk.Radiobutton(self.target_frame, text="Dev.to", variable=self.target_var, value="Dev.to", command=self.update_ui)
        self.devto_radio.pack(side="left", padx=5, pady=5)

        # --- テンプレート選択 ---
        self.template_frame = ttk.LabelFrame(self, text="2. テンプレートを選択")
        self.template_frame.pack(padx=10, pady=5, fill="x")
        self.templates = self.get_templates()
        self.selected_template = tk.StringVar()
        self.template_combo = ttk.Combobox(
            self.template_frame, textvariable=self.selected_template, values=self.templates, state="readonly"
        )
        self.template_combo.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        self.template_combo.bind("<<ComboboxSelected>>", self.load_template)

        # --- 記事内容編集 ---
        self.editor_frame = ttk.LabelFrame(self, text="3. 最終編集")
        self.editor_frame.pack(padx=10, pady=5, expand=True, fill="both")
        self.editor = scrolledtext.ScrolledText(self.editor_frame, wrap=tk.WORD, undo=True)
        self.editor.pack(expand=True, fill="both", padx=5, pady=5)

        # --- 公開実行 ---
        self.action_frame = ttk.LabelFrame(self, text="4. 実行")
        self.action_frame.pack(padx=10, pady=5, fill="x")
        self.publish_button = ttk.Button(self.action_frame, text="公開", command=self.publish)
        self.publish_button.pack(padx=5, pady=5)
        
        self.update_ui()

    def load_config(self):
        config = configparser.ConfigParser()
        if not os.path.exists(CONFIG_FILE):
            messagebox.showerror("設定エラー", f"{CONFIG_FILE} が見つかりません。")
            self.destroy()
            return None
        config.read(CONFIG_FILE, encoding='utf-8-sig')
        return config.get("DEVTO", "API_KEY", fallback=None)

    def update_ui(self):
        target = self.target_var.get()
        self.publish_button.config(text=f"{target}へ公開")

    def get_templates(self):
        if not os.path.exists(TEMPLATE_DIR):
            os.makedirs(TEMPLATE_DIR)
        return [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".md")]

    def load_template(self, event=None):
        template_name = self.selected_template.get()
        if not template_name: return
        try:
            with open(os.path.join(TEMPLATE_DIR, template_name), 'r', encoding='utf-8') as f:
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', f.read())
        except Exception as e:
            messagebox.showerror("エラー", f"テンプレートの読み込み失敗:\n{e}")

    def parse_markdown(self, content):
        """MarkdownからFront Matterと本文を分離する"""
        match = re.match(r'---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            return None, content

        front_matter_str, body = match.groups()
        front_matter = {}
        for line in front_matter_str.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                front_matter[key.strip()] = value.strip()
        return front_matter, body

    def publish(self):
        target = self.target_var.get()
        if target == "Zenn":
            self.publish_to_zenn()
        elif target == "Dev.to":
            self.publish_to_devto()

    def publish_to_zenn(self):
        if not messagebox.askyesno("Zenn公開確認", "Git経由でZennに公開しますか？\n(add, commit, pushが実行されます)"):
            return
        try:
            subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
            commit_message = f"docs: publish new article via Apostle {datetime.datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(["git", "commit", "-m", commit_message], cwd=BASE_DIR, check=True)
            subprocess.run(["git", "push"], cwd=BASE_DIR, check=True)
            messagebox.showinfo("Zenn公開完了", "Zennへの公開処理(push)が完了しました。")
        except Exception as e:
            messagebox.showerror("Gitエラー", f"Gitコマンドの実行に失敗:\n{e}")

    def publish_to_devto(self):
        if not self.api_key:
            messagebox.showerror("設定エラー", "Dev.toのAPIキーがconfig.iniに設定されていません。")
            return
            
        content = self.editor.get('1.0', tk.END).strip()
        front_matter, body = self.parse_markdown(content)

        if not front_matter:
            messagebox.showerror("フォーマットエラー", "Dev.to用のFront Matterが見つかりません。")
            return

        payload = {
            "article": {
                "title": front_matter.get("title", "No Title").replace('"', ''),
                "body_markdown": content,
                "published": "true" if front_matter.get("published") == "true" else "false",
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        if not messagebox.askyesno("Dev.to公開確認", f"以下のタイトルでDev.toに投稿しますか？\n\n{payload['article']['title']}"):
            return
            
        try:
            response = requests.post("https://dev.to/api/articles", headers=headers, data=json.dumps(payload))
            response.raise_for_status() # エラーがあれば例外を発生
            
            result = response.json()
            messagebox.showinfo("Dev.to公開完了", f"記事が正常に投稿されました。\nURL: {result['url']}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("APIエラー", f"Dev.toへの投稿に失敗しました:\n{e}\n\n{e.response.text if e.response else ''}")


if __name__ == "__main__":
    app = ApostleApp()
    app.mainloop()