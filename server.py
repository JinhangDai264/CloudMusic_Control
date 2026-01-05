# server.py - remotemusic 项目核心服务器 (包含网页界面)
import os
import time
import subprocess
import json
from flask import Flask, request, render_template, jsonify # 导入 render_template 和 jsonify
from flask_cors import CORS # 导入 flask_cors
from pynput.keyboard import Key, Controller # 使用 pynput 发送快捷键
import psutil # 用于检查进程状态
from win32com.client import GetObject # 用于设置系统音量

# --- 创建 Flask 应用 ---
app = Flask(__name__, template_folder='templates') # 指定模板文件夹

# --- 立即应用 CORS (确保在所有路由定义之前) ---
# 启用 CORS，允许来自任何来源的请求 (在局域网内使用，更宽松)
CORS(app)

# --- 配置项 ---
# 请将 YOUR_SECRET_TOKEN 替换为您自己设置的安全令牌
SECURE_TOKEN = "aaa"  # 确保这里是您的令牌

# 网易云音乐相关配置
NETEASE_MUSIC_EXE_PATH = "cloudmusic.exe" # 网易云音乐进程名
NETEASE_MUSIC_FULL_PATH = r"F:\myApps\Netease\CloudMusic\cloudmusic.exe" # 网易云音乐完整路径
NETEASE_MUSIC_WINDOW_KEYWORD = "网易云音乐" # 网易云音乐窗口标题关键词

# 默认目标系统音量 (0.0 - 1.0)
DEFAULT_TARGET_VOLUME = 0.5

# --- 工具函数 ---

def is_process_running(process_name):
    """检查指定进程是否正在运行"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == process_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def set_system_volume(volume_level):
    """
    设置系统主音量 (使用 Windows COM API)
    volume_level: 0.0 - 1.0
    """
    try:
        # 获取 Windows 音量控制对象
        o = GetObject('winmgmts:').Get("Win32_SoundDevice").Instances_()
        for item in o:
            if "Primary Sound" in item.Description: # 通常选择主音频设备
                # 音量范围 0-100
                item.SetVolume(int(volume_level * 100))
                print(f"[INFO] 系统音量已设置为 {volume_level:.2f} ({int(volume_level * 100)}%)")
                return True
        print("[WARNING] 未找到主音频设备，无法设置音量")
        return False
    except Exception as e:
        print(f"[ERROR] 设置系统音量失败: {e}")
        return False

def send_hotkey(keys):
    """
    发送快捷键组合
    keys: 一个包含 Key 或字符的列表，例如 [Key.ctrl_l, Key.alt_l, 'p']
    """
    try:
        keyboard = Controller()
        # 按下所有键
        for key in keys:
            keyboard.press(key)
        # 等待一小段时间以确保快捷键被识别 (可以尝试移除或减少此延迟)
        # time.sleep(0.1) # [Modified] - 尝试移除此延迟以进一步优化
        # 释放所有键
        for key in reversed(keys): # 反向释放，符合按键习惯
            keyboard.release(key)
        print(f"[INFO] 发送快捷键: {keys}")
    except Exception as e:
        print(f"[ERROR] 发送快捷键失败: {e}")

# --- API 路由 (保持原有功能) ---

@app.route('/start_music', methods=['POST'])
def start_music():
    """启动网易云音乐（如果未运行）并确保播放"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}")
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        print("[INFO] 收到启动音乐请求...")

        # [Modified Begin] - 简化启动逻辑，移除复杂的窗口操作
        is_running = is_process_running(NETEASE_MUSIC_EXE_PATH)
        if not is_running:
             print("[INFO] 网易云音乐未运行，正在启动...")
             subprocess.Popen([NETEASE_MUSIC_FULL_PATH])
             # 可以选择性地保留或移除启动后的等待时间
             time.sleep(2) # 减少启动等待时间，但不能完全去掉
        else:
            print("[INFO] 网易云音乐已运行。")
        # [Modified End]

        # 设置默认音量
        set_system_volume(DEFAULT_TARGET_VOLUME)
        # 发送播放/暂停快捷键
        send_hotkey([Key.ctrl_l, Key.alt_l, 'p'])
        return jsonify({"status": "success", "message": "Start/Resume music playback triggered"}), 200
    except Exception as e:
        print(f"[ERROR] 处理启动请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

@app.route('/play_pause', methods=['POST']) # 重命名原路由
def play_pause():
    """播放/暂停音乐"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") # [Modified]
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        print("[INFO] 收到播放/暂停请求...")

        # [Modified Begin] - 移除 ensure_netmusic_running_and_focused 调用
        # success = ensure_netmusic_running_and_focused() # 移除这一行
        # if not success:
        #     return jsonify({"status": "error", "message": "Failed to focus Netease Cloud Music"}), 500
        # [Modified End]

        # 使用官方全局快捷键 Ctrl + Alt + P
        send_hotkey([Key.ctrl_l, Key.alt_l, 'p'])
        return jsonify({"status": "success", "message": "Play/Pause command sent"}), 200
    except Exception as e:
        print(f"[ERROR] 处理播放/暂停请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

@app.route('/stop_music', methods=['POST'])
def stop_music():
    """停止音乐 (通过播放/暂停实现，或使用下一曲快捷键)"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") # [Modified]
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        print("[INFO] 收到停止音乐请求...")

        # [Modified Begin] - 移除 ensure_netmusic_running_and_focused 调用
        # success = ensure_netmusic_running_and_focused() # 移除这一行
        # if not success:
        #     return jsonify({"status": "error", "message": "Failed to focus Netease Cloud Music"}), 500
        # [Modified End]

        # 通常使用播放/暂停快捷键来实现停止（如果当前正在播放）
        # 使用官方全局快捷键 Ctrl + Alt + P
        send_hotkey([Key.ctrl_l, Key.alt_l, 'p'])
        return jsonify({"status": "success", "message": "Stop command sent (via Play/Pause)"}), 200
    except Exception as e:
        print(f"[ERROR] 处理停止请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

# 对 prev_track, next_track, like 路由做同样的修改：
@app.route('/prev_track', methods=['POST'])
def prev_track():
    """上一首"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") # [Modified]
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        print("[INFO] 收到上一首请求...")

        # [Modified Begin] - 移除 ensure_netmusic_running_and_focused 调用
        # success = ensure_netmusic_running_and_focused() # 移除这一行
        # if not success:
        #     return jsonify({"status": "error", "message": "Failed to focus Netease Cloud Music"}), 500
        # [Modified End]

        # 使用官方全局快捷键 Ctrl + Alt + Left
        send_hotkey([Key.ctrl_l, Key.alt_l, Key.left])
        return jsonify({"status": "success", "message": "Previous track command sent"}), 200
    except Exception as e:
        print(f"[ERROR] 处理上一首请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

@app.route('/next_track', methods=['POST'])
def next_track():
    """下一首"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") # [Modified]
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        print("[INFO] 收到下一首请求...")

        # [Modified Begin] - 移除 ensure_netmusic_running_and_focused 调用
        # success = ensure_netmusic_running_and_focused() # 移除这一行
        # if not success:
        #     return jsonify({"status": "error", "message": "Failed to focus Netease Cloud Music"}), 500
        # [Modified End]

        # 使用官方全局快捷键 Ctrl + Alt + Right
        send_hotkey([Key.ctrl_l, Key.alt_l, Key.right])
        return jsonify({"status": "success", "message": "Next track command sent"}), 200
    except Exception as e:
        print(f"[ERROR] 处理下一首请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

@app.route('/like', methods=['POST'])
def like():
    """点喜欢当前歌曲"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") # [Modified]
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        print("[INFO] 收到点喜欢请求...")

        # [Modified Begin] - 移除 ensure_netmusic_running_and_focused 调用
        # success = ensure_netmusic_running_and_focused() # 移除这一行
        # if not success:
        #     return jsonify({"status": "error", "message": "Failed to focus Netease Cloud Music"}), 500
        # [Modified End]

        # 使用官方全局快捷键 Ctrl + Alt + L
        send_hotkey([Key.ctrl_l, Key.alt_l, 'l'])
        return jsonify({"status": "success", "message": "Like command sent"}), 200
    except Exception as e:
        print(f"[ERROR] 处理点喜欢请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

# --- 保留原 /trigger_music 路由作为播放/暂停的别名 ---
@app.route('/trigger_music', methods=['POST'])
def trigger_music():
    """原触发音乐路由，现作为播放/暂停的别名"""
    print("[INFO] /trigger_music 路由被调用，重定向到 /play_pause 功能")
    return play_pause()

@app.route('/volume_up', methods=['POST'])
def volume_up():
    """音量增加 (使用系统音量)"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") # [Modified]
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        print("[INFO] 收到音量增加请求...")
        current_vol = psutil.Process().memory_info().vms / 1024 / 1024 # 这个方法不准确，只是为了示例
        # 这里我们简单地将音量增加一个固定值 (例如 0.1)
        new_vol = min(1.0, DEFAULT_TARGET_VOLUME + 0.1) # 限制最大音量为 1.0
        set_system_volume(new_vol)
        return jsonify({"status": "success", "message": f"Volume increased to {new_vol:.2f}"}), 200
    except Exception as e:
        print(f"[ERROR] 处理音量增加请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

@app.route('/volume_down', methods=['POST'])
def volume_down():
    """音量减少 (使用系统音量)"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") # [Modified]
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        print("[INFO] 收到音量减少请求...")
        # 这里我们简单地将音量减少一个固定值 (例如 0.1)
        new_vol = max(0.0, DEFAULT_TARGET_VOLUME - 0.1) # 限制最小音量为 0.0
        set_system_volume(new_vol)
        return jsonify({"status": "success", "message": f"Volume decreased to {new_vol:.2f}"}), 200
    except Exception as e:
        print(f"[ERROR] 处理音量减少请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

@app.route('/volume_set', methods=['POST'])
def volume_set():
    """设置音量 (使用系统音量)"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") # [Modified]
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        data = request.get_json()
        volume = data.get('volume')

        if volume is None or not (0.0 <= volume <= 1.0):
            return jsonify({"status": "error", "message": "Invalid volume value, must be between 0.0 and 1.0"}), 400

        print(f"[INFO] 收到设置音量请求，音量: {volume}")
        set_system_volume(volume)
        return jsonify({"status": "success", "message": f"Volume set to {volume:.2f}"}), 200
    except Exception as e:
        print(f"[ERROR] 处理设置音量请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查路由"""
    return jsonify({"status": "ok", "message": "Server is running"}), 200

@app.route('/get_volume', methods=['GET'])
def get_volume():
    """获取当前系统音量"""
    try:
        token = request.headers.get('Authorization')
        if token != f"Bearer {SECURE_TOKEN}":
            print(f"[WARNING] 收到未授权请求，收到令牌: {repr(token)}, 期望令牌: {repr(f'Bearer {SECURE_TOKEN}')}") 
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        # 获取系统音量
        volume_level = get_system_volume()  # 需要实现这个函数
        return jsonify({"status": "success", "volume": volume_level}), 200
    except Exception as e:
        print(f"[ERROR] 处理获取音量请求时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

def get_system_volume():
    """
    获取当前系统主音量 (0.0 - 1.0)
    这个函数是 set_system_volume 的逆操作。
    """
    try:
        o = GetObject('winmgmts:').Get("Win32_SoundDevice").Instances_()
        for item in o:
            if "Primary Sound" in item.Description:
                # 音量范围 0-100
                current_volume = item.GetVolume()
                return current_volume / 100.0
        return 0.0  # 默认返回 0
    except Exception as e:
        print(f"[ERROR] 获取系统音量失败: {e}")
        return 0.0

# --- 主页路由 ---
@app.route('/')
def main():
    """主页路由，渲染网页界面"""
    return render_template('index.html', token=SECURE_TOKEN) # 将 token 传递给模板

if __name__ == '__main__':
    print(f"[INFO] remotemusic 服务器即将启动...")
    print(f"[INFO] 请确保您的 iPhone 快捷指令中的 Authorization Header 为: Bearer {SECURE_TOKEN}")
    print(f"[INFO] 检查网易云音乐的快捷键设置，确保 Ctrl+Alt+P (播放/暂停), Ctrl+Alt+L (点喜欢), Ctrl+Alt+Left/Right (上/下一首) 未被其他应用占用或冲突。")
    print(f"[INFO] 网页界面可通过 http://<PC的局域网IP>:5000 访问")
    # 注意：在生产环境中，应使用 WSGI 服务器 (如 Gunicorn) 而不是 Flask 的内置开发服务器
    # host='0.0.0.0' 允许局域网内其他设备访问
    app.run(host='0.0.0.0', port=5000, debug=False) # 关闭调试模式以提高性能