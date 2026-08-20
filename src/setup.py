"""
EazyConnecter - セットアップウィザード
配布先PCで最初に実行し、config.yaml を生成する
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os, sys, shutil, re

# ─────────────────────────────────────────────────
# デフォルト配置候補
# ─────────────────────────────────────────────────
DEFAULT_INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "EazyConnecter")

TERATERM_CANDIDATES = [
    r"C:\Program Files\teraterm\ttermpro.exe",
    r"C:\Program Files (x86)\teraterm\ttermpro.exe",
    r"C:\Program Files\TeraTerm\ttermpro.exe",
    r"C:\Program Files (x86)\TeraTerm\ttermpro.exe",
]

# ─────────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────────
def detect_op():
    """op コマンドが使えるか確認"""
    return shutil.which("op") is not None

def detect_1p_app():
    """1Password 本体アプリのインストール確認"""
    candidates = [
        r"C:\Program Files\1Password\app\8\1Password.exe",
        r"C:\Program Files\1Password 7\1Password.exe",
        r"C:\Program Files (x86)\1Password 7\1Password.exe",
    ]
    return any(os.path.exists(p) for p in candidates)

def install_op_cli():
    """winget で 1Password CLI をインストール"""
    import subprocess
    result = subprocess.run(
        ["winget", "install", "--id", "AgileBits.1Password.CLI",
         "--silent", "--accept-package-agreements", "--accept-source-agreements"],
        capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr

def install_1p_app():
    """winget で 1Password 本体をインストール"""
    import subprocess
    result = subprocess.run(
        ["winget", "install", "--id", "AgileBits.1Password",
         "--silent", "--accept-package-agreements", "--accept-source-agreements"],
        capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr

def detect_teraterm():
    for p in TERATERM_CANDIDATES:
        if os.path.exists(p):
            return p
    return ""

def detect_wt():
    return shutil.which("wt.exe") is not None

def base_dir():
    """
    実行ファイルのディレクトリを返す。
    開発時に src/ から実行している場合は一つ上のルートを返す。
    """
    d = os.path.dirname(os.path.abspath(sys.argv[0]))
    if os.path.basename(d).lower() == "src":
        return os.path.dirname(d)
    return d

def write_config(path, values):
    tt_path  = values["teraterm_path"].replace("\\", "\\\\")
    key_path = values["default_key"].replace("\\", "\\\\") if values["default_key"] else ""
    op_mode  = values.get("op_mode", "op")
    content  = f"""# ===================================================
# EazyConnecter 設定ファイル (セットアップウィザードで生成)
# ===================================================

ssh:
  default_client: {values["default_client"]}
  teraterm_path: "{tt_path}"
  default_user: "{values["default_user"]}"
  default_key: "{key_path}"
  default_port: 22

rdp:
  width: ""
  height: ""
  multimon: false

gui:
  title: "EazyConnecter"
  window_width: 760
  window_height: 560
  font_size: 10

onepassword:
  mode: {op_mode}
  connect_host: "http://localhost:8080"
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ─────────────────────────────────────────────────
# GUI ウィザード
# ─────────────────────────────────────────────────
class SetupWizard:
    CLR_BG     = "#F5F6FA"
    CLR_ACCENT = "#0078D4"
    CLR_WHITE  = "#FFFFFF"
    CLR_PANEL  = "#FFFFFF"
    CLR_OK     = "#107C10"
    CLR_WARN   = "#C84614"

    STEPS = ["ようこそ", "配置先", "SSH設定", "1Password", "確認"]

    def __init__(self, root):
        self.root  = root
        self.step  = 0

        # 値の保持
        self.var_install_dir    = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        self.var_tt_path        = tk.StringVar(value=detect_teraterm())
        self.var_default_user   = tk.StringVar(value="")
        self.var_default_key    = tk.StringVar(value="")
        self.var_ssh_client     = tk.StringVar(value="windowsterminal" if detect_wt() else
                                               "teraterm" if detect_teraterm() else "powershell")
        self.var_shortcut_desktop = tk.BooleanVar(value=True)
        self.var_shortcut_start   = tk.BooleanVar(value=True)
        self.var_op_mode      = tk.StringVar(value='op')
        self.var_install_op   = tk.BooleanVar(value=not detect_op())
        self.var_install_1p   = tk.BooleanVar(value=not detect_1p_app())

        # フォント
        fs = 10
        self.fn  = ("Meiryo UI", fs)
        self.fb  = ("Meiryo UI", fs, "bold")
        self.fs  = ("Meiryo UI", fs - 1)
        self.fh  = ("Meiryo UI", fs + 3, "bold")
        self.ft  = ("Meiryo UI", fs + 1, "bold")

        self._build_shell()
        self._show_step()

    # ── 外枠 ─────────────────────────────────────
    def _build_shell(self):
        self.root.title("EazyConnecter セットアップ")
        self.root.geometry("580x480")
        self.root.resizable(False, False)
        self.root.configure(bg=self.CLR_BG)

        # ヘッダー
        hdr = tk.Frame(self.root, bg=self.CLR_ACCENT, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  EazyConnecter セットアップ",
                 font=self.fh, bg=self.CLR_ACCENT, fg=self.CLR_WHITE,
                 anchor="w").pack(fill="both", expand=True, padx=8)

        # ステップインジケーター
        self.step_fr = tk.Frame(self.root, bg="#DDE6F0", height=32)
        self.step_fr.pack(fill="x")
        self.step_fr.pack_propagate(False)
        self.step_labels = []
        for i, name in enumerate(self.STEPS):
            lbl = tk.Label(self.step_fr, text=f"  {i+1}. {name}  ",
                           font=self.fs, bg="#DDE6F0", fg="#555")
            lbl.pack(side="left")
            self.step_labels.append(lbl)

        # コンテンツエリア（スクロール対応）
        content_outer = tk.Frame(self.root, bg=self.CLR_BG)
        content_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(content_outer, bg=self.CLR_BG,
                                 highlightthickness=0, bd=0)
        self._scrollbar = tk.Scrollbar(content_outer, orient="vertical",
                                       command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # スクロールバーは必要なときだけ表示
        self._canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self._canvas, bg=self.CLR_BG)
        self._content_id = self._canvas.create_window(
            (0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_content_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.content.bind("<MouseWheel>", self._on_mousewheel)

        # フッター（ボタン）
        footer = tk.Frame(self.root, bg=self.CLR_BG, height=52)
        footer.pack(fill="x", padx=24, pady=(0, 12))
        footer.pack_propagate(False)

        sep = tk.Frame(footer, bg="#CCC", height=1)
        sep.pack(fill="x", pady=(0, 10))

        self.btn_back = tk.Button(footer, text="← 戻る", font=self.fn,
                                  relief="flat", bd=0, padx=14,
                                  bg="#E0E0E0", fg="#333", cursor="hand2",
                                  command=self._back)
        self.btn_back.pack(side="left")

        self.btn_next = tk.Button(footer, text="次へ →", font=self.fb,
                                  relief="flat", bd=0, padx=16,
                                  bg=self.CLR_ACCENT, fg=self.CLR_WHITE,
                                  activebackground="#005A9E", cursor="hand2",
                                  command=self._next)
        self.btn_next.pack(side="right")

        tk.Button(footer, text="キャンセル", font=self.fn,
                  relief="flat", bd=0, padx=14,
                  bg="#E0E0E0", fg="#333", cursor="hand2",
                  command=self.root.destroy).pack(side="right", padx=8)

    # ── スクロール ───────────────────────────────
    def _on_content_configure(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        # コンテンツがキャンバスより小さければスクロールバーを隠す
        cw = self._canvas.winfo_height()
        fw = self.content.winfo_reqheight()
        if fw > cw:
            self._scrollbar.pack(side="right", fill="y")
        else:
            self._scrollbar.pack_forget()

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._content_id, width=event.width - 48)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _update_steps(self):
        for i, lbl in enumerate(self.step_labels):
            if i == self.step:
                lbl.config(bg=self.CLR_ACCENT, fg=self.CLR_WHITE, font=self.fb)
            elif i < self.step:
                lbl.config(bg="#A8C8E8", fg="#003060", font=self.fs)
            else:
                lbl.config(bg="#DDE6F0", fg="#555", font=self.fs)

    # ── ページ切替 ────────────────────────────────
    def _show_step(self):
        for w in self.content.winfo_children():
            w.destroy()
        self._canvas.yview_moveto(0)   # ページ切替時に先頭へ
        self._update_steps()

        pages = [self._page_welcome, self._page_install,
                 self._page_ssh,     self._page_1password, self._page_confirm]
        pages[self.step]()

        self.btn_back.config(state="normal" if self.step > 0 else "disabled")
        is_last = (self.step == len(self.STEPS) - 1)
        self.btn_next.config(text="セットアップ実行" if is_last else "次へ →",
                             bg=self.CLR_OK if is_last else self.CLR_ACCENT)

    def _next(self):
        if not self._validate(): return
        if self.step == len(self.STEPS) - 1:
            self._run_setup()
        else:
            self.step += 1
            self._show_step()

    def _back(self):
        if self.step > 0:
            self.step -= 1
            self._show_step()

    # ── パス補完 ─────────────────────────────────
    def _normalize_install_dir(self):
        """末尾が EazyConnecter でなければ自動補完する"""
        d = self.var_install_dir.get().strip()
        if not d:
            return
        # パス末尾のフォルダ名が EazyConnecter でなければ補完
        if os.path.basename(d).lower() != "eazyconnecter":
            d = os.path.join(d, "EazyConnecter")
            self.var_install_dir.set(d)

    # ── バリデーション ────────────────────────────
    def _validate(self):
        if self.step == 1:  # 配置先
            self._normalize_install_dir()   # EazyConnecter を自動補完
            d = self.var_install_dir.get().strip()
            if not d:
                messagebox.showwarning("入力エラー", "配置先フォルダを指定してください。")
                return False
        if self.step == 2:  # SSH設定
            if self.var_ssh_client.get() == "teraterm":
                tt = self.var_tt_path.get().strip()
                if not tt or not os.path.exists(tt):
                    if not messagebox.askyesno("確認",
                        "TeraTerm の実行ファイルが見つかりません。\nこのまま続けますか？"):
                        return False
        return True

    # ─────────────────────────────────────────────
    # ページ定義
    # ─────────────────────────────────────────────
    def _section(self, title):
        tk.Label(self.content, text=title, font=self.ft,
                 bg=self.CLR_BG, fg=self.CLR_ACCENT,
                 anchor="w").pack(fill="x", pady=(0, 8), padx=24)

    def _note(self, text, color="#555"):
        tk.Label(self.content, text=text, font=self.fs,
                 bg=self.CLR_BG, fg=color,
                 anchor="w", justify="left", wraplength=490).pack(fill="x", padx=24)

    # ── Step 0: ようこそ ──────────────────────────
    def _page_welcome(self):
        tk.Label(self.content, text="ようこそ", font=self.fh,
                 bg=self.CLR_BG, fg="#1A1A1A").pack(anchor="w", pady=(16, 4), padx=24)
        self._note("このウィザードは EazyConnecter の初期設定を行います。\n"
                   "設定内容は config.yaml として保存されます。")
        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=16, padx=24)
        self._section("このウィザードで設定する項目")
        for item in ["配置先フォルダの選択",
                     "TeraTerm インストールパスの確認",
                     "SSH 接続のデフォルトクライアント選択",
                     "SSH 接続のデフォルトユーザー名"]:
            tk.Label(self.content, text=f"    ✓  {item}", font=self.fn,
                     bg=self.CLR_BG, fg="#333", anchor="w").pack(fill="x", pady=1, padx=24)

    # ── Step 1: 配置先 ────────────────────────────
    def _page_install(self):
        self._section("配置先フォルダの選択")
        self._note("EazyConnecter.exe / config.yaml / servers.yaml を配置するフォルダを指定します。")
        tk.Frame(self.content, bg=self.CLR_BG, height=8).pack(padx=24)

        row = tk.Frame(self.content, bg=self.CLR_BG)
        row.pack(fill="x", padx=24)
        ent = tk.Entry(row, textvariable=self.var_install_dir,
                       font=self.fn, relief="solid", bd=1)
        ent.pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Button(row, text="参照...", font=self.fn,
                  relief="flat", bd=0, padx=10,
                  bg="#E0E0E0", fg="#333", cursor="hand2",
                  command=self._browse_install).pack(side="right")

        tk.Frame(self.content, bg=self.CLR_BG, height=12).pack(padx=24)
        self._note("※ フォルダが存在しない場合は自動作成されます。", "#888")

        # 既存インストール検出
        d = self.var_install_dir.get()
        if os.path.exists(os.path.join(d, "config.yaml")):
            self._note("⚠  既存の config.yaml が見つかりました。上書きされます。", self.CLR_WARN)

    def _browse_install(self):
        d = filedialog.askdirectory(title="配置先フォルダを選択",
                                    initialdir=self.var_install_dir.get())
        if d:
            self.var_install_dir.set(d.replace("/", "\\"))
            self._normalize_install_dir()   # 選択直後に補完
            self._show_step()

    # ── Step 2: SSH設定 ───────────────────────────
    def _page_ssh(self):
        self._section("SSH クライアントの選択")
        clients = [
            ("windowsterminal", "Windows Terminal  （推奨）"),
            ("teraterm",        "TeraTerm"),
            ("powershell",      "PowerShell"),
        ]
        for val, label in clients:
            tk.Radiobutton(self.content, text=label, variable=self.var_ssh_client,
                           value=val, font=self.fn, bg=self.CLR_BG,
                           activebackground=self.CLR_BG,
                           command=self._show_step).pack(anchor="w", pady=2, padx=24)

        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=10, padx=24)

        # TeraTerm パス
        self._section("TeraTerm 実行ファイルのパス")
        tt_detected = detect_teraterm()
        if tt_detected:
            self._note(f"✓  自動検出: {tt_detected}", self.CLR_OK)
        else:
            self._note("自動検出されませんでした。手動で指定してください。", self.CLR_WARN)

        row2 = tk.Frame(self.content, bg=self.CLR_BG)
        row2.pack(fill="x", pady=(4, 0), padx=24)
        tk.Entry(row2, textvariable=self.var_tt_path,
                 font=self.fn, relief="solid", bd=1,
                 state="normal" if self.var_ssh_client.get() == "teraterm" else "disabled"
                 ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Button(row2, text="参照...", font=self.fn,
                  relief="flat", bd=0, padx=10,
                  bg="#E0E0E0", fg="#333", cursor="hand2",
                  command=self._browse_tt).pack(side="right")

        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=10, padx=24)

        # デフォルトユーザー
        self._section("SSH デフォルトユーザー名")
        self._note("省略時はサーバーごとの設定、または接続時に手動入力します。")
        tk.Entry(self.content, textvariable=self.var_default_user,
                 font=self.fn, relief="solid", bd=1,
                 width=24).pack(anchor="w", pady=(4, 12), padx=24)

    def _browse_tt(self):
        p = filedialog.askopenfilename(
            title="ttermpro.exe を選択",
            initialdir=r"C:\Program Files",
            filetypes=[("実行ファイル", "*.exe"), ("すべて", "*.*")])
        if p:
            self.var_tt_path.set(p.replace("/", "\\"))

    # ── Step 3: 1Password ──────────────────────────
    def _page_1password(self):
        CLR_OP = "#1A7F4B"
        self._section("1Password 連携設定")

        # op CLI の検出状態
        op_ok = detect_op()
        app_ok = detect_1p_app()

        # op CLI ステータス
        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=(0,8), padx=24)
        self._section("1Password CLI (op コマンド)")
        if op_ok:
            self._note("✓  op コマンドが検出されました。インストール不要です。", CLR_OP)
        else:
            self._note("✗  op コマンドが見つかりません。", self.CLR_WARN)
            tk.Checkbutton(self.content,
                           text="winget で 1Password CLI をインストールする",
                           variable=self.var_install_op,
                           font=self.fn, bg=self.CLR_BG,
                           activebackground=self.CLR_BG
                           ).pack(anchor="w", padx=32, pady=2)

        # 1Password 本体ステータス（op モード時のみ必要）
        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=8, padx=24)
        self._section("1Password 本体アプリ")
        self._note("op CLI を通常モードで使う場合、1Password 本体アプリによるロック解除が必要です。\n"
                   "Service Account / Connect モードでは本体アプリ不要です。", "#555")
        if app_ok:
            self._note("✓  1Password 本体アプリが検出されました。", CLR_OP)
        else:
            self._note("✗  1Password 本体アプリが見つかりません。", self.CLR_WARN)
            tk.Checkbutton(self.content,
                           text="winget で 1Password 本体アプリをインストールする",
                           variable=self.var_install_1p,
                           font=self.fn, bg=self.CLR_BG,
                           activebackground=self.CLR_BG
                           ).pack(anchor="w", padx=32, pady=2)

        # 連携モード選択
        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=8, padx=24)
        self._section("連携モード")
        modes = [
            ("op",              "op CLI（Individual/Families/Teams/Business）"),
            ("service_account", "Service Account（Business・op CLI +トークン認証）"),
            ("connect",         "1Password Connect（Business・REST API・op 不要）"),
        ]
        for val, label in modes:
            tk.Radiobutton(self.content, text=label,
                           variable=self.var_op_mode, value=val,
                           font=self.fn, bg=self.CLR_BG,
                           activebackground=self.CLR_BG
                           ).pack(anchor="w", padx=32, pady=2)

        tk.Frame(self.content, bg=self.CLR_BG, height=4).pack()
        self._note("※ Service Account / Connect モードのトークン設定は\n"
                   "  EazyConnecter 起動後に「認証」ボタンから行ってください。", "#888")

    # ── Step 4: 確認 ─────────────────────────────
    def _page_confirm(self):
        self._section("設定内容の確認")
        self._note("以下の設定で config.yaml を生成し、ファイルを配置します。")
        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=10, padx=24)

        mode_labels = {
            "op":              "op CLI",
            "service_account": "Service Account",
            "connect":         "1Password Connect",
        }
        items = [
            ("配置先フォルダ",       self.var_install_dir.get()),
            ("SSH クライアント",     self.var_ssh_client.get()),
            ("TeraTerm パス",        self.var_tt_path.get() or "（未設定）"),
            ("デフォルトユーザー名", self.var_default_user.get() or "（未設定）"),
            ("1Password モード",     mode_labels.get(self.var_op_mode.get(), self.var_op_mode.get())),
        ]
        for label, value in items:
            row = tk.Frame(self.content, bg=self.CLR_BG)
            row.pack(fill="x", pady=3, padx=24)
            tk.Label(row, text=f"{label}:", font=self.fb,
                     bg=self.CLR_BG, fg="#333", width=20, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=self.fn,
                     bg=self.CLR_BG, fg="#555", anchor="w").pack(side="left")

        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=10, padx=24)

        # 配置されるファイル一覧
        self._note("配置されるファイル:", "#333")
        src = base_dir()
        files = ["EazyConnecter.exe", "servers.yaml"]
        dst = self.var_install_dir.get()
        for fname in files:
            src_path = os.path.join(src, fname)
            exists = "✓" if os.path.exists(src_path) else "✗ 見つかりません"
            color  = "#333" if os.path.exists(src_path) else self.CLR_WARN
            tk.Label(self.content, text=f"    {exists}  {fname}  →  {dst}",
                     font=self.fs, bg=self.CLR_BG, fg=color,
                     anchor="w").pack(fill="x")
        tk.Label(self.content,
                 text=f"    ✓  config.yaml  →  {dst}  （新規生成）",
                 font=self.fs, bg=self.CLR_BG, fg="#333", anchor="w").pack(fill="x", padx=24)

        tk.Frame(self.content, bg="#CCC", height=1).pack(fill="x", pady=10, padx=24)
        self._note("ショートカットの作成:", "#333")
        tk.Checkbutton(self.content, text="デスクトップにショートカットを作成する",
                       variable=self.var_shortcut_desktop,
                       font=self.fn, bg=self.CLR_BG, activebackground=self.CLR_BG
                       ).pack(anchor="w", padx=32, pady=2)
        tk.Checkbutton(self.content, text="スタートメニューにショートカットを作成する",
                       variable=self.var_shortcut_start,
                       font=self.fn, bg=self.CLR_BG, activebackground=self.CLR_BG
                       ).pack(anchor="w", padx=32, pady=2)

    # ─────────────────────────────────────────────
    # セットアップ実行
    # ─────────────────────────────────────────────
    def _run_setup(self):
        dst = self.var_install_dir.get().strip()
        src_dir = base_dir()

        try:
            # 1Password CLI インストール
            if self.var_install_op.get() and not detect_op():
                self.root.update()
                ok, log = install_op_cli()
                if not ok:
                    messagebox.showwarning("警告",
                        f"1Password CLI のインストールに失敗しました。\n\n{log[:300]}\n\n"
                        "手動でインストールしてください:\n"
                        "winget install AgileBits.1Password.CLI")

            # 1Password 本体インストール
            if self.var_install_1p.get() and not detect_1p_app():
                self.root.update()
                ok, log = install_1p_app()
                if not ok:
                    messagebox.showwarning("警告",
                        f"1Password のインストールに失敗しました。\n\n{log[:300]}\n\n"
                        "手動でインストールしてください:\n"
                        "winget install AgileBits.1Password")

            os.makedirs(dst, exist_ok=True)

            # ファイルコピー（setup.exe自身と同じフォルダにあるファイルを配置）
            for fname in ["EazyConnecter.exe", "servers.yaml"]:
                s = os.path.join(src_dir, fname)
                if os.path.exists(s):
                    shutil.copy2(s, os.path.join(dst, fname))

            # config.yaml 生成
            write_config(os.path.join(dst, "config.yaml"), {
                "default_client": self.var_ssh_client.get(),
                "teraterm_path":  self.var_tt_path.get().strip(),
                "default_user":   self.var_default_user.get().strip(),
                "default_key":    self.var_default_key.get().strip(),
                "op_mode":        self.var_op_mode.get(),
            })

            # ショートカット作成
            if self.var_shortcut_desktop.get():
                self._create_shortcut(dst, target="desktop")
            if self.var_shortcut_start.get():
                self._create_shortcut(dst, target="startmenu")

            messagebox.showinfo("完了",
                f"セットアップが完了しました。\n\n配置先:\n{dst}\n\n"
                f"EazyConnecter.exe を起動してください。")
            self.root.destroy()

        except Exception as e:
            messagebox.showerror("エラー", f"セットアップに失敗しました。\n\n{e}")

    def _create_shortcut(self, dst, target="desktop"):
        """WSH経由でショートカットを作成（target: 'desktop' or 'startmenu'）"""
        import subprocess, tempfile
        exe = os.path.join(dst, "EazyConnecter.exe")

        if target == "desktop":
            lnk_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        else:
            # スタートメニュー: Programs フォルダ配下に EazyConnecter フォルダを作成
            programs = os.path.join(
                os.environ.get("APPDATA", ""),
                r"Microsoft\Windows\Start Menu\Programs")
            lnk_dir = os.path.join(programs, "EazyConnecter")
            os.makedirs(lnk_dir, exist_ok=True)

        lnk = os.path.join(lnk_dir, "EazyConnecter.lnk")
        vbs = f"""
Set ws = CreateObject("WScript.Shell")
Set sc = ws.CreateShortcut("{lnk}")
sc.TargetPath = "{exe}"
sc.WorkingDirectory = "{dst}"
sc.Description = "EazyConnecter - Server Connection Launcher"
sc.Save
"""
        with tempfile.NamedTemporaryFile("w", suffix=".vbs",
                                         delete=False, encoding="utf-8") as f:
            f.write(vbs)
            tmp = f.name
        subprocess.run(["cscript", "//nologo", tmp], capture_output=True)
        os.unlink(tmp)


# ─────────────────────────────────────────────────
# エントリーポイント
# ─────────────────────────────────────────────────
def main():
    root = tk.Tk()
    SetupWizard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
