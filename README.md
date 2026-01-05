# RemoteMusic Controller

一个简单的 Python Flask Web 应用，用于远程控制 Windows 上的网易云音乐播放器。

## 功能

*   **播放控制**：播放/暂停、上一首、下一首。
*   **音乐互动**：点喜欢当前歌曲。
*   **播放器管理**：启动或停止网易云音乐播放器。
*   **音量控制**：增加或减少系统主音量。
*   **Web 界面**：直观的双栏式网页控制面板，采用深色主题和深红色按钮。

## 环境要求

*   **操作系统**：Windows (因为使用了 `pycaw` 和 `wmi` 库来控制音频和启动应用)。
*   **Python**: 3.7 或更高版本。
*   **网易云音乐**：必须已安装在您的 Windows 系统上。

## 安装与配置

1.  **克隆或下载项目**：
    ```bash
    git clone <your-repo-url>
    cd RemoteMusic
    ```

2.  **安装 Python 依赖**：
    ```bash
    pip install -r requirements.txt
    ```
    如果没有 `requirements.txt` 文件，您需要手动安装以下库：
    ```bash
    pip install flask pycaw wmi
    ```

3.  **配置 `server.py`**：
    *   打开 `server.py` 文件。
    *   **设置 `NETEASE_MUSIC_FULL_PATH`**：
        *   找到 `NETEASE_MUSIC_FULL_PATH` 变量。
        *   将其值修改为您电脑上 `cloudmusic.exe` 文件的实际路径。**请务必使用原始字符串 `r"..."`**。
        *   例如：`NETEASE_MUSIC_FULL_PATH = r"C:\Program Files\Netease\CloudMusic\cloudmusic.exe"`
    *   **设置 `SECURE_TOKEN`**：
        *   找到 `SECURE_TOKEN` 变量。
        *   修改为一个安全且只有您知道的密钥。此密钥将用于保护您的服务器 API 端点。
    *   **（可选）修改服务器 IP 和端口**：
        *   如果您希望服务器在特定 IP 或端口上运行，请修改 `app.run` 行。默认为 `0.0.0.0:5000`，表示在所有网络接口的 5000 端口监听。

4.  **启动服务器**：
    ```bash
    python server.py
    ```
    服务器启动后，会显示类似 `Running on all addresses (0.0.0.0)` 和 `Running on http://192.168.x.x:5000` 的信息。记下 `http://...:5000` 这个地址。

5.  **访问 Web 界面**：
    *   在您的电脑或其他设备的浏览器中，输入上一步记下的地址。
    *   例如：`http://192.168.0.206:5000`
    *   您将看到 "CloudMusic Control" 的控制面板。

## 使用说明

*   **左侧面板**：包含播放/暂停、上一首、下一首和点喜欢按钮。
*   **右侧面板**：包含启动/停止播放器和音量控制按钮。
*   点击相应按钮即可发送命令到您的电脑，控制网易云音乐。
*   服务器会对每个请求进行 `SECURE_TOKEN` 验证，确保安全性。

## 注意事项

*   请确保 `NETEASE_MUSIC_FULL_PATH` 设置正确，否则“启动播放”功能将无法工作。
*   服务器需要保持运行状态才能接收命令。
*   请妥善保管您的 `SECURE_TOKEN`，避免泄露。
*   本项目目前仅支持 Windows 系统上的网易云音乐。

## 文件结构
RemoteMusic/
│
├── server.py          # Flask 服务器主文件
├── templates/
│   └── index.html     # Web 控制界面
└── README.md          # 本说明文件