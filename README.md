# OneDrive Log Cleaner 🧹

[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)]()
[![Language](https://img.shields.io/badge/Language-Python_3.x-yellow.svg)]()
[![GUI](https://img.shields.io/badge/GUI-Tkinter-green.svg)]()

**Current development: v1.0 Beta 2** — see the Beta 2 safety notes below.

*(English below | 中文说明在下方)*

---

## 📸 Screenshots / 软件截图

<p align="center">
<img width="630" height="856" alt="image" src="https://github.com/user-attachments/assets/80c6c70c-2720-4b20-ab19-a6ec07696026" />
<img width="630" height="856" alt="image" src="https://github.com/user-attachments/assets/eac2ad41-c48b-42f7-a31d-78d581b3d2eb" />

</p>

---



## v1.0 Beta 2 — Safety-first development

- Cleanup now uses a conservative allowlist and excludes generic .dat, .tmp, .txt, .bak, and .keystore files.
- Manual cleanup presents a file-count and estimated-size preview and requires explicit confirmation.
- Files that are locked, inaccessible, outside the resolved log directory, or symbolic links are skipped and logged.
- Background threshold monitoring is alert-only; it does not automatically delete files.
- Folder migration copies to a staging directory, verifies file count and total size, preserves the original as a timestamped backup, and attempts rollback if Junction creation fails.

> Beta 2 is under development. Please test with non-critical data first. The original main branch remains unchanged while this work is reviewed.

## 🇬🇧 English

**OneDrive Log Cleaner** is a defensive, fully portable Windows optimization engine designed to safely manage, purge, and redirect the heavy debugging logs and telemetry cache silently accumulated by Microsoft OneDrive.

It was engineered to solve a common headache for Windows users and professionals: OneDrive continuously dumping binary debugging fragments (ETL, ODL, LOG files) into the hidden `AppData` directory, which can rapidly consume dozens of GBs on your primary C-drive.

### ✨ Key Features
* **Defensive Whitelist Purging**: Precision-cleans dead debugging logs (.log, .etl, .odl, etc.) without ever touching your actual work files or cloud data.
* **Threshold Monitoring (Alert Only)**: Monitors the log directory and alerts when it reaches the configured threshold. Beta 2 never deletes files automatically.
* **Non-Destructive Sync Reset**: Safely executes native commands to rebuild broken local sync hashes when OneDrive gets stuck on "Processing changes".
* **Seamless Folder Redirection**: Uses NTFS junction points (`mklink`) to transparently move the heavy logs directory from C-drive to a secondary drive (D: or E:).
* **100% Portable**: No installation required. All configurations (`app_config.json`) and runtime logs are saved strictly in the program's folder.

### 🚀 Getting Started
1. Go to the [Releases](../../releases) page and download `OneDriveLogCleaner_vX.X.exe`.
2. Run on Windows. Administrator permission may be required to create NTFS junctions; locked or inaccessible files are skipped.
3. Click "Clean OneDrive log files", review the preview, and explicitly confirm before deletion.

---

## 🇨🇳 中文说明

**OneDrive Log Cleaner** 是一款专为彻底解决 OneDrive 长期运行导致 C 盘底层调试日志暴增、同步长期卡死等痛点而打造的 Windows 纯绿色全自动清理与调度引擎。

开发初衷是为了应对常见的 C 盘空间被无故占用的问题：OneDrive 会在深层目录下生成大量无法自动释放的二进制调试日志与遥测缓存碎片，悄无声息地吞噬数十 GB 的存储空间。

### ✨ 核心功能
* **全量白名单防御级清理**：严格基于扩展名精准抹除废旧日志碎片（.log, .etl, .odl 等），绝对不触碰您的任何实际工作文件与云端数据。
* **空间阈值监控（仅提醒）**：监控日志目录容量，达到设定阈值时提醒用户。Beta 2 不会在后台自动删除文件。
* **无损重置与账本重建**：当 OneDrive 长期转圈卡死、提示“正在处理更改”时，可一键安全重置，静默顺畅重建本地文件指纹账本。
* **底层目录无缝迁移**：集成 NTFS 软链接技术，一键将极占空间的日志存放区从 C 盘定向挂载到 D 盘或 E 盘，治标且治本。
* **极致绿色便携**：真正的单文件便携设计，配置与日志均保存在程序同级目录下，无广告、无隐私采集。

### 🚀 如何使用
1. 前往右侧的 [Releases](../../releases) 页面，下载最新的 `OneDriveLogCleaner_vX.X.exe`。
2. 在 Windows 中运行。创建 NTFS Junction 可能需要管理员权限；被占用或无权限的文件会跳过。
3. 点击“清理 OneDrive 日志文件”，先查看清理预览，再由你明确确认后执行。

---

## 🛠 For Developers / 开发者指南

### Option 1: Run from Source / 选项一：直接运行源码
```bash
pip install Pillow pystray
python "Onedrive Log Cleaner.py"
