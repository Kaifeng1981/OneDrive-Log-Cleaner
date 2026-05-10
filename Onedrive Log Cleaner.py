import os
import shutil
import subprocess
import sys
import threading
import time
import json
import traceback
import winreg
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ================= 真正的绿色便携路径绑定 =================
# 绝对锁定程序本体 (.py 或打包后的 .exe) 所在的同级真实物理目录 (用于保存配置和历史)
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_FILE = os.path.join(BASE_DIR, "app_config.json")
HISTORY_LOG_FILE = os.path.join(BASE_DIR, "execution_history.log")
ERROR_LOG_FILE = os.path.join(BASE_DIR, "error_log.txt")

# ================= 专属资源解压路径映射引擎 (专治 EXE 图标丢失) =================
def resource_path(relative_path):
    """
    智能双轨路径定位：
    如果是本地 .py 运行，直接返回同级目录下的资源；
    如果是 PyInstaller 打包的 .exe 运行，自动去系统的 _MEIxxxx 临时解压包里提取嵌好的资源。
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(BASE_DIR, relative_path)

# ================= 安全防御白名单 (全量覆盖 OneDrive 日志扩展名) =================
# 涵盖 OneDrive 专属的二进制调试日志及遥测缓存碎片
SAFE_EXTS = (
    ".log", ".etl", ".dat", ".bak", ".tmp",
    ".odl", ".odlgz", ".odlsent", ".aold",
    ".otc", ".session", ".txt", ".keystore"
)

# ================= 全局防闪退与精准异常留痕引擎 =================
def global_exception_handler(exc_type, exc_value, exc_traceback):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 致命拦截:\n{err_msg}")
    except: pass
    messagebox.showerror("程序遇到异常 (已平稳拦截)", f"底层运行遇到阻碍，日志已保存在所在目录下:\n\n{err_msg}")

sys.excepthook = global_exception_handler

# ================= 后台英文记录本 =================
class SimpleLogger:
    def __init__(self):
        if not os.path.exists(HISTORY_LOG_FILE):
            try:
                with open(HISTORY_LOG_FILE, "w", encoding="utf-8") as f:
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] | INIT | PROGRAM_STARTED\n")
            except: pass

    def add_record(self, action_type, freed_gb=0.0, file_count=0, details=""):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if action_type == "PURGE":
            line = f"[{timestamp}] | PURGE | FREED_GB: {freed_gb:.4f} | FILES: {file_count}\n"
        elif action_type == "RESET":
            line = f"[{timestamp}] | RESET | ONEDRIVE_RESET | STATUS: {details}\n"
        elif action_type == "REDIRECT":
            line = f"[{timestamp}] | REDIRECT | MOVED_TO: {details}\n"
        else:
            line = f"[{timestamp}] | {action_type} | {details}\n"
        try:
            with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e: self._log_internal_error(f"写入历史记录失败: {e}")

    def get_totals(self):
        total_freed, purge_count = 0.0, 0
        if not os.path.exists(HISTORY_LOG_FILE): return {"count": 0, "freed_gb": 0.0}
        try:
            with open(HISTORY_LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if " | PURGE | " in line:
                        purge_count += 1
                        try:
                            parts = line.split("|")
                            for p in parts:
                                if "FREED_GB:" in p:
                                    total_freed += float(p.replace("FREED_GB:", "").strip())
                        except: pass
        except: pass
        return {"count": purge_count, "freed_gb": total_freed}

    def open_text(self):
        try: os.system(f'notepad "{HISTORY_LOG_FILE}"')
        except Exception as e: messagebox.showwarning("提示", f"无法打开日志文件: {e}")

    def _log_internal_error(self, msg):
        try:
            with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 内部错误: {msg}\n")
        except: pass

# ================= 纯净大白话多语言库 =================
LANG_DICT = {
    "zh": {
        "title": "OneDrive Log Cleaner",
        "lbl_accumulated": "当前堆积垃圾",
        "btn_clean": "清除Onedrive log文件", 
        "btn_scan": "手动刷新",
        "btn_reset": "重置Onedrive", 
        "btn_move": "迁移至其他盘...",
        "chk_monitor": "自动清理 (超过阈值自动默默清理，并开机启动)",
        "threshold_lbl": "自动清理阈值:",
        "reset_confirm_t": "温馨提示：重置前请务必看清",
        "reset_confirm_m": "重置会让 OneDrive 重新核对一遍本地的文件账本。\n\n⚠️ 重要预告：\n如果您平时存的工作小文件非常多（几百GB以上），重置后右下角的 OneDrive 图标可能会转圈 30 到 60 分钟，并提示“正在处理更改”。\n\n请千万别慌！它绝对没有在重新下载或删除文件，只是在默默比对文件指纹，核对完就彻底顺畅了。\n\n确定现在要重置吗？",
        "move_select_t": "请选择要挪到的目标盘 (比如直接选 D盘 或 E盘)",
        "move_err_c": "目标位置依然在 C 盘！这样挪没有意义，请选其他盘。",
        "move_success": "大功告成！垃圾文件以后都会自动存到这个盘: {d}",
        "h_summary": "历史清理: {c}次 | 共释放: {g:.2f} GB",
        "btn_view_log": "日志",  
        "theme_prefix": "", "lang": "EN",
        "btn_help": "帮助说明",
        "help_title": "OneDrive Log Cleaner 说明文档",
        "help_content": "【软件工作原理】\n本工具专注于安全清理 OneDrive 长期运行积累在 AppData 下的调试日志 (无需担心，绝对不会触碰或删除您的任何实际工作文件与云端数据)。\n\n【核心功能提示】\n1. 清除文件：瞬间终结积压的废旧日志流，收回宝贵的 C 盘空间。\n2. 重置功能：当遇到同步长期卡死时使用，系统会静默重建本地哈希账本。\n3. 自动清理：勾选后，工具将常驻托盘默默检测，超过阈值自动清空，做到完全免打扰。\n\n【本地便携说明】\n本程序为纯绿色便携软件，您的配置文件与执行日志会永远自动保存在程序本体的同级目录下。",
        "ready": "就绪。常驻自动刷新中。",
        "cleaning": "正在精准抹除底层日志碎片，请稍候...",
        "clean_done": "清理成功！本次腾出 {size:.2f} GB 空间。",
        "auto_purged": "检测到超过阈值 {t}GB，已静默全自动清理！",
        "monitor_locked": "自动清理中。后台正盯着空间，手动按钮已临时锁定。",
        "monitor_unlocked": "自动清理已停止，手动操作已恢复。",
        "notify_title": "后台自动清理中",
        "notify_msg": "OneDrive Log Cleaner 正在后台默默帮您盯着磁盘空间。",
        "theme_auto": "自动"
    },
    "en": {
        "title": "OneDrive Log Cleaner",
        "lbl_accumulated": "Accumulated Junk",
        "btn_clean": "Clean Onedrive log files", 
        "btn_scan": "Refresh",
        "btn_reset": "Reset Onedrive", 
        "btn_move": "Move Drive...",
        "chk_monitor": "Auto Clean (Purge when above threshold & Auto-boot)",
        "threshold_lbl": "Auto-Clean Threshold:",
        "reset_confirm_t": "Important Note Before Resetting",
        "reset_confirm_m": "Resetting forces OneDrive to re-check your local file index.\n\n⚠️ Heads Up:\nIf you have hundreds of GBs of tiny work files, OneDrive might spin for 30-60 minutes showing 'Processing changes'.\n\nDon't worry! It is NOT re-downloading or deleting files. It's just comparing file fingerprints to fix errors.\n\nAre you sure you want to proceed?",
        "move_select_t": "Select a drive (like D: or E:)",
        "move_err_c": "That is still on the C drive! Please select a different drive.",
        "move_success": "Done! Junk files will now go to: {d}",
        "h_summary": "Cleaned: {c} times | Reclaimed: {g:.2f} GB",
        "btn_view_log": "Log",  
        "theme_prefix": "", "lang": "中",
        "btn_help": "Help",
        "help_title": "OneDrive Log Cleaner Documentation",
        "help_content": "[How It Works]\nThis tool securely purges debug logs accumulated by OneDrive in AppData (Rest assured, your actual work files and cloud data are NEVER touched).\n\n[Core Features]\n1. Clean Up: Instantly reclaims physical disk space by removing dead logs.\n2. Reset: Use when synchronization is stuck. Rebuilds the local sync index safely.\n3. Auto Clean: Monitors space silently in the system tray and auto-purges without annoying pop-ups.\n\n[Portable Storage]\nThis is a 100% portable app. All configurations and logs are saved directly next to the program file.",
        "ready": "Ready. Auto-refreshing.",
        "cleaning": "Purging log fragments securely, please wait...",
        "clean_done": "Purge successful! Reclaimed {size:.2f} GB.",
        "auto_purged": "Exceeded threshold {t}GB. Auto-purged silently!",
        "monitor_locked": "Auto Clean active. Manual buttons locked securely.",
        "monitor_unlocked": "Auto Clean stopped. Manual buttons unlocked.",
        "notify_title": "Monitoring Active",
        "notify_msg": "OneDrive Log Cleaner is silently monitoring your disk space.",
        "theme_auto": "Auto"
    }
}

THEMES = {
    "dark": {"bg": "#1A1A1A", "card": "#262626", "fg": "#FFFFFF", "sub_fg": "#999999", "accent": "#00A86B", "accent_active": "#008B58", "btn_bg": "#333333", "btn_active": "#404040", "con_bg": "#141414", "bar_base": "#3D3D3D", "name_zh": "暗色", "name_en": "Dark"},
    "light": {"bg": "#F5F5F5", "card": "#FFFFFF", "fg": "#1A1A1A", "sub_fg": "#666666", "accent": "#008B58", "accent_active": "#00A86B", "btn_bg": "#E6E6E6", "btn_active": "#CCCCCC", "con_bg": "#FFFFFF", "bar_base": "#E0E0E0", "name_zh": "亮色", "name_en": "Light"}
}

class OneDriveCleanerVertical:
    def __init__(self, root):
        self.root = root
        self.is_processing = False
        self.monitor_running = False
        
        self.db = SimpleLogger()
        self.local_app_data = os.environ.get("LOCALAPPDATA", "")
        self.logs_dir = os.path.join(self.local_app_data, "Microsoft", "OneDrive", "logs")
        self.drive_letter = os.path.splitdrive(self.logs_dir)[0] if self.logs_dir else "C:"
        self.onedrive_exe = self.find_program()

        self.config = {"lang": "zh", "theme_mode": "auto", "autostart": False, "threshold_gb": 10}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f: self.config.update(json.load(f))
            except Exception as e: self.db._log_internal_error(f"读取JSON配置失败: {e}")
        
        self.current_theme = self.get_system_theme()
        totals = self.db.get_totals()
        self.history_count, self.history_freed_gb = totals["count"], totals["freed_gb"]

        self.curr_log_gb, self.curr_file_count = 0.0, 0
        self.drive_total_gb, self.drive_used_gb = 0.0, 0.0

        self.lbl_s_v = None; self.lbl_dt_v = None; self.lbl_du_v = None; self.lbl_dl_v = None
        self.canvas = None; self.lbl_h_summary = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing_window)

        self.build_modern_vertical_ui()
        self.apply_theme()
        self.refresh_text()
        
        # 完美调用资源解压映射引擎，无论在哪都能精准拿到 logo.ico
        ico_path = resource_path("logo.ico")
        if os.path.exists(ico_path):
            try: self.root.iconbitmap(ico_path)
            except: pass

        self.check_size_now()
        self.setup_tray_icon()
        self.start_auto_refresh()

        if "--hidden-boot" in sys.argv or self.config["autostart"]:
            self.chk_var.set(True)
            self.monitor_running = True
            self.update_button_states()
            threading.Thread(target=self._monitor_loop, daemon=True).start()
            if "--hidden-boot" in sys.argv:
                self.root.after(100, self.root.withdraw)

    def find_program(self):
        paths = [
            os.path.join(self.local_app_data, "Microsoft", "OneDrive", "onedrive.exe"),
            os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Microsoft OneDrive", "onedrive.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "Microsoft OneDrive", "onedrive.exe")
        ]
        return next((p for p in paths if os.path.exists(p)), "")

    def get_system_theme(self):
        if self.config["theme_mode"] != "auto": return self.config["theme_mode"]
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if val == 1 else "dark"
        except: return "light"

    def save_settings(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(self.config, f)
        except Exception as e: self.db._log_internal_error(f"保存JSON配置失败: {e}")

    def update_autostart(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "OneDriveLogCleanerRefined"
        exe_path = f'"{sys.executable}"' if getattr(sys, 'frozen', False) else f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
        boot_cmd = f'{exe_path} --hidden-boot'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                if self.config["autostart"]:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, boot_cmd)
                else:
                    try: winreg.DeleteValue(key, app_name)
                    except: pass
        except Exception as e: self.db._log_internal_error(f"设置开机启动注册表失败: {e}")

    def setup_tray_icon(self):
        try:
            from PIL import Image, ImageDraw
            import pystray

            logo_path = resource_path("logo.ico")

            def get_icon_image():
                if os.path.exists(logo_path):
                    try: return Image.open(logo_path)
                    except: pass
                
                img = Image.new('RGB', (64, 64), color='#252525')
                draw = ImageDraw.Draw(img)
                draw.rectangle((12, 12, 52, 52), fill='#00A86B')
                return img

            menu = pystray.Menu(
                pystray.MenuItem("打开主界面" if self.config["lang"]=="zh" else "Show Dashboard", self.wake_window_from_tray, default=True),
                pystray.MenuItem("彻底退出程序" if self.config["lang"]=="zh" else "Exit Program", self.quit_program_completely)
            )
            
            self.tray_icon = pystray.Icon("ODLCleaner", get_icon_image(), "OneDrive Log Cleaner", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            self.has_tray = True
        except Exception as e:
            self.has_tray = False
            self.show_tip("托盘模块未完全开启。")

    def wake_window_from_tray(self, icon=None, item=None):
        self.root.after(0, self._restore_window_ui)

    def _restore_window_ui(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_closing_window(self):
        if self.monitor_running:
            self.root.withdraw()
            if getattr(self, 'has_tray', False) and self.tray_icon:
                try:
                    t = LANG_DICT[self.config["lang"]]
                    self.tray_icon.notify(t["notify_msg"], t["notify_title"])
                except: pass
        else:
            self.quit_program_completely()

    def quit_program_completely(self, icon=None, item=None):
        self.monitor_running = False
        if getattr(self, 'has_tray', False) and self.tray_icon:
            try: self.tray_icon.stop()
            except: pass
        self.root.quit()
        sys.exit(0)

    # ================= 极简垂直一体化 UI 构建 =================
    def build_modern_vertical_ui(self):
        self.root.geometry("420x540")
        self.root.resizable(False, False)
        
        style = ttk.Style()
        style.theme_use("clam")

        self.top_bar = tk.Frame(self.root, height=36)
        self.top_bar.pack(fill=tk.X, side=tk.TOP, padx=12, pady=(6, 0))
        
        self.lbl_title = tk.Label(self.top_bar, font=("Microsoft YaHei", 10, "bold"))
        self.lbl_title.pack(side=tk.LEFT, pady=4)
        
        self.btn_lang = tk.Button(self.top_bar, relief=tk.FLAT, font=("Microsoft YaHei", 8, "bold"), cursor="hand2", command=self.switch_lang)
        self.btn_lang.pack(side=tk.RIGHT, padx=(4, 0))
        
        self.btn_theme = tk.Button(self.top_bar, relief=tk.FLAT, font=("Microsoft YaHei", 8), cursor="hand2", command=self.switch_color)
        self.btn_theme.pack(side=tk.RIGHT, padx=4)

        self.btn_help = tk.Button(self.top_bar, relief=tk.FLAT, font=("Microsoft YaHei", 8), cursor="hand2", command=self.show_help_dialog)
        self.btn_help.pack(side=tk.RIGHT)

        self.card_main = tk.Frame(self.root)
        self.card_main.pack(fill=tk.X, padx=12, pady=(8, 6))
        
        self.lbl_s_t = tk.Label(self.card_main, font=("Microsoft YaHei", 9))
        self.lbl_s_t.pack(anchor=tk.CENTER, pady=(12, 2))
        
        self.lbl_s_v = tk.Label(self.card_main, text="---", font=("Consolas", 18, "bold"))
        self.lbl_s_v.pack(anchor=tk.CENTER, pady=(0, 10))

        self.card_disk = tk.Frame(self.root)
        self.card_disk.pack(fill=tk.X, padx=12, pady=6)
        
        self.lbl_dt_v = tk.Label(self.card_disk, font=("Microsoft YaHei", 9))
        self.lbl_dt_v.pack(anchor=tk.W, padx=12, pady=(8, 2))
        self.lbl_du_v = tk.Label(self.card_disk, font=("Microsoft YaHei", 9))
        self.lbl_du_v.pack(anchor=tk.W, padx=12, pady=2)
        
        self.lbl_dl_v = tk.Label(self.card_disk, font=("Microsoft YaHei", 9))
        self.lbl_dl_v.pack(anchor=tk.W, padx=12, pady=(2, 2))

        self.canvas = tk.Canvas(self.card_disk, height=22, relief=tk.FLAT, highlightthickness=0)
        self.canvas.pack(fill=tk.X, padx=12, pady=(4, 12))

        self.btn_box = tk.Frame(self.root)
        self.btn_box.pack(fill=tk.X, padx=12, pady=4)
        
        self.btn_clean = tk.Button(self.btn_box, font=("Microsoft YaHei", 10, "bold"), relief=tk.FLAT, cursor="hand2", command=lambda: self.do_task(self.clean_junk))
        self.btn_clean.pack(fill=tk.X, pady=3, ipady=4)
        
        self.sub_grid = tk.Frame(self.btn_box)
        self.sub_grid.pack(fill=tk.X, pady=2)
        self.btn_scan = tk.Button(self.sub_grid, font=("Microsoft YaHei", 9), relief=tk.FLAT, cursor="hand2", command=lambda: self.do_task(self.check_size_now))
        self.btn_scan.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        self.btn_reset = tk.Button(self.sub_grid, font=("Microsoft YaHei", 9), relief=tk.FLAT, cursor="hand2", command=lambda: self.do_task(self.reset_onedrive))
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 3))
        self.btn_move = tk.Button(self.sub_grid, font=("Microsoft YaHei", 9), relief=tk.FLAT, cursor="hand2", command=self.move_folder)
        self.btn_move.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        self.monitor_box = tk.Frame(self.btn_box)
        self.monitor_box.pack(fill=tk.X, pady=(10, 2))
        
        self.chk_var = tk.BooleanVar(value=self.config["autostart"])
        self.chk_monitor = tk.Checkbutton(self.monitor_box, variable=self.chk_var, font=("Microsoft YaHei", 9, "bold"), relief=tk.FLAT, command=self.on_toggle_monitor_check)
        self.chk_monitor.pack(anchor=tk.W, pady=2)

        self.sel_box = tk.Frame(self.monitor_box)
        self.sel_box.pack(anchor=tk.W, padx=20, pady=0)
        self.lbl_threshold = tk.Label(self.sel_box, font=("Microsoft YaHei", 9))
        self.lbl_threshold.pack(side=tk.LEFT)
        
        self.cbo_threshold = ttk.Combobox(self.sel_box, values=[5, 10, 20, 50, 100], width=4, state="readonly", font=("Consolas", 9))
        self.cbo_threshold.set(self.config["threshold_gb"])
        self.cbo_threshold.pack(side=tk.LEFT, padx=4)
        self.cbo_threshold.bind("<<ComboboxSelected>>", self.on_threshold_changed)
        
        self.lbl_unit = tk.Label(self.sel_box, text="GB", font=("Consolas", 9))
        self.lbl_unit.pack(side=tk.LEFT)

        self.history_box = tk.Frame(self.root)
        self.history_box.pack(fill=tk.X, padx=12, pady=(6, 0))
        
        self.lbl_h_summary = tk.Label(self.history_box, font=("Microsoft YaHei", 8))
        self.lbl_h_summary.pack(side=tk.LEFT, padx=4)
        
        self.btn_view_log = tk.Button(self.history_box, font=("Microsoft YaHei", 8), relief=tk.FLAT, cursor="hand2", command=self.db.open_text)
        self.btn_view_log.pack(side=tk.RIGHT)

        self.con_frame = tk.Frame(self.root)
        self.con_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 10))
        self.txt_con = tk.Text(self.con_frame, height=2, font=("Consolas", 8), relief=tk.FLAT)
        self.txt_con.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

    def show_help_dialog(self):
        t = LANG_DICT[self.config["lang"]]
        messagebox.showinfo(t["help_title"], t["help_content"])

    def update_button_states(self):
        def _safe_update():
            btn_state = "disabled" if self.monitor_running else "normal"
            self.btn_clean.config(state=btn_state)
            self.btn_scan.config(state=btn_state)
            self.btn_reset.config(state=btn_state)
            self.btn_move.config(state=btn_state)
            self.cbo_threshold.config(state="disabled" if self.monitor_running else "readonly")
        self.root.after(0, _safe_update)

    def on_toggle_monitor_check(self):
        is_on = self.chk_var.get()
        self.config["autostart"] = is_on
        self.save_settings()
        self.update_autostart()
        
        self.monitor_running = is_on
        self.update_button_states()
        
        t = LANG_DICT[self.config["lang"]]
        if is_on:
            threading.Thread(target=self._monitor_loop, daemon=True).start()
            self.show_tip(t["monitor_locked"])
        else:
            self.show_tip(t["monitor_unlocked"])

    def apply_theme(self):
        c = THEMES[self.current_theme]
        self.root.configure(bg=c["bg"])
        
        for frame in [self.top_bar, self.card_main, self.card_disk, self.con_frame, 
                      self.btn_box, self.sub_grid, self.monitor_box, self.sel_box, self.history_box]:
            frame.configure(bg=c["bg"] if frame not in [self.card_main, self.card_disk] else c["card"])

        for child in self.monitor_box.winfo_children() + self.sel_box.winfo_children():
            if not isinstance(child, ttk.Combobox):
                child.configure(bg=c["bg"])
                if isinstance(child, tk.Label): child.configure(fg=c["sub_fg"])

        self.lbl_title.configure(bg=c["bg"], fg=c["accent"])
        self.btn_lang.configure(bg=c["bg"], fg=c["sub_fg"], activebackground=c["bg"])
        self.btn_theme.configure(bg=c["bg"], fg=c["sub_fg"], activebackground=c["bg"])
        self.btn_help.configure(bg=c["bg"], fg=c["sub_fg"], activebackground=c["bg"])

        self.lbl_s_t.configure(bg=c["card"], fg=c["sub_fg"])
        self.lbl_s_v.configure(bg=c["card"]) 
        
        for btn in [self.btn_scan, self.btn_reset, self.btn_move, self.btn_view_log]:
            btn.configure(bg=c["btn_bg"], fg=c["fg"], activebackground=c["btn_active"], activeforeground=c["fg"])

        self.btn_clean.configure(bg=c["accent"], fg="#FFFFFF", activebackground=c["accent_active"], activeforeground="#FFFFFF")
        self.chk_monitor.configure(bg=c["bg"], fg=c["fg"], selectcolor=c["card"], activebackground=c["bg"])

        for lbl in [self.lbl_dt_v, self.lbl_du_v, self.lbl_h_summary]:
            lbl.configure(bg=c["card"] if lbl != self.lbl_h_summary else c["bg"], fg=c["sub_fg"])

        self.lbl_dl_v.configure(bg=c["card"], fg="#0078D4")

        self.canvas.configure(bg=c["card"])
        self.txt_con.configure(bg=c["con_bg"], fg=c["accent"] if self.current_theme=="dark" else c["fg"], insertbackground=c["fg"])
        self.draw_progress()

    def refresh_text(self):
        t = LANG_DICT[self.config["lang"]]
        self.root.title(t["title"]); self.lbl_title.config(text=t["title"])
        self.btn_lang.config(text=t["lang"])
        self.btn_help.config(text=t["btn_help"])
        
        theme_obj = THEMES[self.current_theme]
        m_name = t["theme_auto"] if self.config["theme_mode"]=="auto" else (theme_obj["name_zh"] if self.config["lang"]=="zh" else theme_obj["name_en"])
        self.btn_theme.config(text=m_name)

        self.lbl_s_t.config(text=t["lbl_accumulated"])
        self.btn_clean.config(text=t["btn_clean"])
        self.btn_scan.config(text=t["btn_scan"])
        self.btn_reset.config(text=t["btn_reset"])
        self.btn_move.config(text=t["btn_move"])
        self.btn_view_log.config(text=t["btn_view_log"])
        
        self.chk_monitor.config(text=t["chk_monitor"])
        self.lbl_threshold.config(text=t["threshold_lbl"])

        self.update_live_display()

    def update_live_display(self):
        color = "#FF4444" if self.curr_log_gb > 5 else THEMES[self.current_theme]["accent"]
        unit = "个文件" if self.config["lang"]=="zh" else "Files"
        self.lbl_s_v.config(text=f"{self.curr_log_gb:.2f} GB ({self.curr_file_count} {unit})", fg=color)

        pct = int((self.drive_used_gb / self.drive_total_gb * 100)) if self.drive_total_gb > 0 else 0
        
        if self.config["lang"] == "zh":
            self.lbl_dt_v.config(text=f"物理盘符 ({self.drive_letter}) 总容量: {self.drive_total_gb:.1f} GB")
            self.lbl_du_v.config(text=f"已用总物理空间: {self.drive_used_gb:.1f} GB ({pct}%)")
            self.lbl_dl_v.config(text=f"Onedrive Log文件: {self.curr_log_gb:.2f} GB")
        else:
            self.lbl_dt_v.config(text=f"Drive ({self.drive_letter}) Capacity: {self.drive_total_gb:.1f} GB")
            self.lbl_du_v.config(text=f"Used Space: {self.drive_used_gb:.1f} GB ({pct}%)")
            self.lbl_dl_v.config(text=f"Onedrive Log: {self.curr_log_gb:.2f} GB")

        t = LANG_DICT[self.config["lang"]]
        self.lbl_h_summary.config(text=t["h_summary"].format(c=self.history_count, g=self.history_freed_gb))
        self.draw_progress()

    def start_auto_refresh(self):
        self.root.after(3000, self.auto_refresh_loop)

    def auto_refresh_loop(self):
        if not self.is_processing:
            s, c = 0, 0
            if os.path.exists(self.logs_dir):
                for r, ds, fs in os.walk(self.logs_dir):
                    for f in fs:
                        try: s += os.path.getsize(os.path.join(r, f)); c += 1
                        except: pass
            self.curr_log_gb = s / (1024**3)
            self.curr_file_count = c
            self.update_live_display()
        self.root.after(3000, self.auto_refresh_loop)

    def switch_lang(self):
        self.config["lang"] = "en" if self.config["lang"] == "zh" else "zh"
        self.save_settings(); self.refresh_text()

    def switch_color(self):
        modes = ["auto", "dark", "light"]
        idx = modes.index(self.config["theme_mode"])
        self.config["theme_mode"] = modes[(idx + 1) % len(modes)]
        self.save_settings()
        self.current_theme = self.get_system_theme()
        self.apply_theme(); self.refresh_text()

    def on_threshold_changed(self, event):
        try:
            self.config["threshold_gb"] = int(self.cbo_threshold.get())
            self.save_settings()
        except: pass

    def show_tip(self, msg_key, **kwargs):
        t = LANG_DICT[self.config["lang"]]
        text = t.get(msg_key, msg_key).format(**kwargs)
        self.txt_con.after(0, lambda: self._print_box(text))

    def _print_box(self, text):
        self.txt_con.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.txt_con.see(tk.END)

    def do_task(self, func):
        if self.is_processing: return
        self.is_processing = True
        threading.Thread(target=func, daemon=True).start()

    def check_size_now(self):
        self.show_tip("ready")
        try:
            total, _, free = shutil.disk_usage(self.drive_letter)
            self.drive_total_gb = total / (1024**3)
            self.drive_used_gb = (total - free) / (1024**3)
        except Exception as e: self.db._log_internal_error(f"读取磁盘用量失败: {e}")

        s, c = 0, 0
        if os.path.exists(self.logs_dir):
            for r, ds, fs in os.walk(self.logs_dir):
                for f in fs:
                    try: s += os.path.getsize(os.path.join(r, f)); c += 1
                    except: pass
        self.curr_log_gb = s / (1024**3)
        self.curr_file_count = c
        
        self.is_processing = False
        self.root.after(0, self.update_live_display)

    def draw_progress(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        if w <= 1: w = 372
        h = 16

        if self.drive_total_gb <= 0: return

        base_color = THEMES[self.current_theme]["bar_base"]
        self.canvas.create_rectangle(0, 0, w, h, fill=base_color, outline="")

        used_w = int((self.drive_used_gb / self.drive_total_gb) * w)
        self.canvas.create_rectangle(0, 0, used_w, h, fill="#888888", outline="")

        log_w = int((self.curr_log_gb / self.drive_total_gb) * w)
        if log_w < 3 and self.curr_log_gb > 0.01: log_w = 3
        
        self.canvas.create_rectangle(0, 0, log_w, h, fill="#0078D4", outline="")

    # ================= 全量白名单防御级清理引擎 =================
    def clean_junk(self, silent=False):
        for p in ["onedrive.exe", "FileCoAuth.exe"]:
            subprocess.run(["taskkill", "/F", "/IM", p], capture_output=True)
        time.sleep(1.5)

        if not silent: self.show_tip("cleaning")
        freed, deleted_files = 0, 0
        
        if os.path.exists(self.logs_dir):
            for r, ds, fs in os.walk(self.logs_dir, topdown=False):
                for f in fs:
                    if f.lower().endswith(SAFE_EXTS):
                        fp = os.path.join(r, f)
                        try: 
                            s = os.path.getsize(fp); os.remove(fp)
                            freed += s; deleted_files += 1
                        except Exception as e: self.db._log_internal_error(f"安全删除失败 ({f}): {e}")
                
                for d in ds:
                    try: os.rmdir(os.path.join(r, d))
                    except: pass

        freed_gb = freed / (1024**3)
        if not silent: self.show_tip("clean_done", size=freed_gb)
        
        if deleted_files > 0:
            self.db.add_record("PURGE", freed_gb=freed_gb, file_count=deleted_files)
            totals = self.db.get_totals()
            self.history_count, self.history_freed_gb = totals["count"], totals["freed_gb"]

        if self.onedrive_exe: os.system(f'start "" "{self.onedrive_exe}"')
        self.is_processing = False; self.check_size_now()

    def reset_onedrive(self):
        t = LANG_DICT[self.config["lang"]]
        if not messagebox.askyesno(t["reset_confirm_t"], t["reset_confirm_m"]):
            self.is_processing = False; return

        self.show_tip("正在让 OneDrive 重新检查文件...")
        if self.onedrive_exe:
            subprocess.run([self.onedrive_exe, "/reset"], capture_output=True)
            self.db.add_record("RESET", details="USER_RESET")
            time.sleep(3)
        self.is_processing = False; self.check_size_now()

    def move_folder(self):
        t = LANG_DICT[self.config["lang"]]
        target_dir = filedialog.askdirectory(title=t["move_select_t"])
        if not target_dir: return
        
        drive = os.path.splitdrive(target_dir)[0].upper()
        if drive == "C:":
            messagebox.showerror("提示", t["move_err_c"])
            return

        def _exec():
            self.show_tip("正在准备挪动文件夹...")
            subprocess.run(["taskkill", "/F", "/IM", "onedrive.exe"], capture_output=True)
            time.sleep(1.5)
            
            dest = os.path.join(target_dir, "OneDrive_Logs_Folder")
            try:
                os.makedirs(dest, exist_ok=True)
            except Exception as e:
                self.show_tip(f"前置校验失败，无法建立目标区: {e}")
                self.is_processing = False; return

            try:
                if os.path.exists(self.logs_dir): shutil.rmtree(self.logs_dir)
            except Exception as e:
                self.show_tip(f"解除原端锁阻碍，请检查占用: {e}")
                self.is_processing = False; return
            
            res = subprocess.run(f'mklink /j "{self.logs_dir}" "{dest}"', shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                self.db.add_record("REDIRECT", details=dest)
                self.show_tip(t["move_success"].format(d=dest))
                self.drive_letter = drive 
            else:
                self.show_tip("挪动建立连接失败了，请稍后再试。")
            
            if self.onedrive_exe: os.system(f'start "" "{self.onedrive_exe}"')
            self.is_processing = False; self.check_size_now()

        self.do_task(_exec)

    def _monitor_loop(self):
        while self.monitor_running:
            s = 0
            if os.path.exists(self.logs_dir):
                for r, ds, fs in os.walk(self.logs_dir):
                    for f in fs:
                        try: s += os.path.getsize(os.path.join(r, f))
                        except: pass
            size_gb = s / (1024**3)
            target_gb = self.config["threshold_gb"]
            
            if size_gb >= target_gb:
                self.is_processing = True
                self.clean_junk(silent=True)
                
                t = LANG_DICT[self.config["lang"]]
                msg = t["auto_purged"].format(t=target_gb)
                self.txt_con.after(0, lambda m=msg: self.txt_con.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {m}\n"))
                time.sleep(3600)
            else:
                time.sleep(300)

if __name__ == "__main__":
    root = tk.Tk()
    app = OneDriveCleanerVertical(root)
    root.mainloop()
