# Mining Management API với Auto-Download & Auto-Start

Ứng dụng Python để quản lý mining từ xa qua HTTP API với tính năng tự động tải file mining và auto-start.

## ✨ Tính năng

- 🚀 **Auto-download mining tools**: Tự động tải ccminer.exe, libcrypto-1_1-x64.dll từ CDN
- 📁 **Quản lý theo coin**: Mỗi coin có thư mục riêng
- 🔧 **Tool-specific hash rate detection**: Hỗ trợ ccminer, t-rex, gminer, xmrig, phoenixminer
- ⚙️ **Auto-config generation**: Tự động tạo config.json và command line
- 🎯 **Auto-start**: Tự động chạy mining khi khởi động server
- 🎛️ **Auto-start management**: Enable/disable auto-start theo từng miner hoặc globally
- 🔄 **Auto-restart**: Tự động khởi động lại khi server crash
- 🐧 **Cross-platform**: Hỗ trợ Windows và Ubuntu/Linux

## 🚀 Cài đặt

### Windows
```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy server
start_server.bat
# hoặc
python app.py
```

### Ubuntu/Linux
```bash
# Cài đặt tự động
chmod +x install.sh
./install.sh

# Chạy với auto-restart
./run.sh

# Hoặc chạy với systemd (nếu đã cài)
sudo systemctl start mining-manager
```

## 📁 Cấu trúc deployment

```
dndvina-mining/
├── app.py                 # Server chính
├── config.py              # Cấu hình tập trung (logs, server, timeouts)
├── requirements.txt       # Dependencies
├── README.md             # Documentation  
├── .gitignore           # Git ignore file
├── start_server.bat     # Windows start script
├── run.sh              # Ubuntu auto-restart script
├── install.sh          # Ubuntu install script
└── miners/             # Auto-created (ignored by git)
    ├── ethereum/
    ├── bitcoin/
    └── vrsc/
```

## ⚙️ Configuration (config.py)

File `config.py` chứa tất cả cấu hình có thể tùy chỉnh:

```python
# Server Configuration
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9098
DEBUG_MODE = False

# Logging Configuration
ENABLE_FLASK_ACCESS_LOGS = False  # Tắt logs: 127.0.0.1 - "GET /api/status" 200
ENABLE_APP_LOGS = True             # Mining operations logs
ENABLE_MONITOR_LOGS = True         # Periodic status logs
ENABLE_DEBUG_LOGS = False          # Debug/verbose logs

# Mining Configuration
AUTO_START_ON_BOOT = True          # Auto-start miners on server boot
HASH_RATE_CHECK_INTERVAL = 5       # Check hash rate every 5 seconds
MONITOR_STATUS_INTERVAL = 30       # Print status every 30 seconds

# Process Management
SIGINT_WAIT_TIME = 2               # Wait after SIGINT
SIGINT_RETRY_COUNT = 4             # Number of SIGINT retries
SIGTERM_WAIT_TIME = 3              # Wait after SIGTERM

# File Download
CDN_BASE_URL = 'http://cdn.dndvina.com/minings'
DOWNLOAD_CHUNK_SIZE = 8192
DOWNLOAD_TIMEOUT = 300
```

**Tắt Flask Access Logs:**
```python
# Trong config.py
ENABLE_FLASK_ACCESS_LOGS = False  # Không hiển thị "GET /api/status HTTP/1.1" 200
```

**Tắt Monitor Status Logs:**
```python
# Trong config.py
ENABLE_MONITOR_LOGS = False  # Không hiển thị "[THEO DÕI] === Trạng thái Mining ==="
```

---

## 📡 API Reference

**Base URL**: `http://localhost:9098`  
**Content-Type**: `application/json`  
**Default Port**: `9098`

---

### 1️⃣ Cập nhật cấu hình miners
**POST** `/api/update-config`

**Query Parameters:**
- `stop_all_first=true` (optional) - Stop tất cả miners trước khi update config

**Auto Stop-Restart Logic:**
- **Individual miners**: Nếu miner đang chạy → auto stop → update config → restart (nếu auto_start=true)
- **Global stop**: Thêm `?stop_all_first=true` để stop ALL miners trước
- **Safe updates**: Không conflict khi update config

#### Request Body - Option 1: JSON Config File
```json
[
  {
    "name": "vrsc-gpu1",
    "coin_name": "vrsc",
    "mining_tool": "ccminer", 
    "config": {
      "pools": [
        {
          "name": "AP",
          "url": "stratum+tcp://ap.luckpool.net:3956",
          "timeout": 150,
          "disabled": 0
        }
      ],
      "user": "RCtqovjA8xLBxdQoHJcepDBd9h6Lh7pPxp.worker1",
      "algo": "verus",
      "threads": 8,
      "cpu-priority": 1
    },
    "required_files": ["ccminer.exe", "libcrypto-1_1-x64.dll"],
    "auto_start": true
  }
]
```

#### Request Body - Option 2: Command Line Parameters
```json
[
  {
    "name": "dero-miner",
    "coin_name": "dero",
    "mining_tool": "astrominer",
    "config": "-w deroi1qyzlxxgq2weyqlxg5u4tkng2lf5rktwanqhse2hwm577ps22zv2x2q9pvfz92 -r dero.rabidmining.com:10300 -m 8",
    "required_files": ["astrominer"],
    "auto_start": false
  }
]
```

#### Response
```json
{
  "success": true,
  "message": "Cập nhật cấu hình thành công cho 2 miner(s)"
}
```

**Command Generation:**
- **JSON Config**: `./ccminer -c config.json`
- **CLI Parameters**: `./astrominer -w WALLET -r POOL:PORT -m 8`

---

### 2️⃣ Mining Tools Được Hỗ Trợ

| Tool | Default Files | Hash Rate Pattern | Notes |
|------|---------------|-------------------|-------|
| **ccminer** | ccminer.exe, libcrypto-1_1-x64.dll | `GPU #0: 25.50 MH/s` | NVIDIA GPU miner |
| **astrominer** | astrominer | `Hashrate 1.08KH/s` | DERO CPU/GPU miner |
| **t-rex** | t-rex.exe | `GPU #0: 45.5 MH/s` | NVIDIA miner |
| **gminer** | miner.exe | `GPU0 50.5 MH/s` | AMD/NVIDIA miner |
| **xmrig** | xmrig.exe | `speed 1000.0 H/s` | Monero CPU miner |
| **phoenixminer** | PhoenixMiner.exe | `GPU1: 50.5 MH/s` | ETH miner |

**Auto-Download:**
- Files tự động tải từ: `http://cdn.dndvina.com/minings/{filename}`
- Chỉ tải nếu file chưa tồn tại
- Linux: Auto chmod +x cho executables

---

### 3️⃣ Bắt đầu mining
**POST** `/api/start`

#### Request Body
```json
{
  "name": "vrsc-gpu1"
}
```

#### Response - Success
```json
{
  "success": true,
  "message": "Bắt đầu đào vrsc-gpu1 thành công",
  "pid": 12345
}
```

#### Response - Error
```json
{
  "success": false,
  "message": "Miner vrsc-gpu1 không tồn tại"
}
```

---

### 4️⃣ Dừng mining
**POST** `/api/stop`

#### Request Body - Single Miner
```json
{
  "name": "vrsc-gpu1"
}
```

#### Request Body - Multiple Miners
```json
{
  "names": ["vrsc-gpu1", "dero-miner", "btc-miner"]
}
```

#### Response
```json
{
  "success": true,
  "message": "Đã dừng 3 miner(s) thành công",
  "stopped": ["vrsc-gpu1", "dero-miner", "btc-miner"]
}
```

**Graceful Shutdown:**
1. Send SIGINT (Ctrl+C) - cho mining tool cleanup
2. Wait 2 seconds
3. Send SIGINT x3 more (1s intervals) - cho confirmation prompts
4. SIGTERM → SIGKILL nếu cần

---

### 5️⃣ Force Kill Tất Cả Processes
**POST** `/api/force-stop-all`

**Emergency Stop** - Dừng ngay lập tức tất cả mining processes.

#### Request Body (Optional)
```json
{
  "process_names": ["ccminer", "astrominer", "xmrig"]
}
```

#### Response
```json
{
  "success": true,
  "message": "Đã force kill 3 mining processes",
  "killed_count": 3,
  "active_tools_before_kill": ["ccminer", "astrominer"],
  "target_process_names": ["ccminer", "astrominer", "xmrig"]
}
```

**Kill Strategy:**
1. SIGINT x4 (delays: 2s, 1s, 1s, 1s) - Handle y/n prompts
2. SIGTERM → wait 3s
3. SIGKILL (force)
4. Windows: `taskkill /T /F`
5. Linux: `kill -9` with children

---

### 6️⃣ Kiểm tra trạng thái miner
**GET** `/api/status?name=vrsc-gpu1`

#### Response
```json
{
  "success": true,
  "name": "vrsc-gpu1",
  "status": "running",
  "pid": 12345,
  "start_time": "2025-10-16T08:00:00",
  "hash_rate": 50500000,
  "coin_name": "vrsc",
  "mining_tool": "ccminer",
  "auto_start": true,
  "last_output": "GPU #0: GeForce RTX 3080 - 50.5 MH/s"
}
```

**Hash Rate Unit:**
- API luôn trả về **H/s** (hash per second)
- Client tự convert sang KH/s, MH/s, GH/s:
  - `>= 1,000,000,000 H/s` → GH/s (÷ 1,000,000,000)
  - `>= 1,000,000 H/s` → MH/s (÷ 1,000,000)
  - `>= 1,000 H/s` → KH/s (÷ 1,000)
  - `< 1,000 H/s` → H/s

**Example Conversion:**
```javascript
// Client-side JavaScript
function formatHashRate(hashRateInHS) {
  if (hashRateInHS >= 1e9) {
    return { value: (hashRateInHS / 1e9).toFixed(2), unit: 'GH/s' };
  } else if (hashRateInHS >= 1e6) {
    return { value: (hashRateInHS / 1e6).toFixed(2), unit: 'MH/s' };
  } else if (hashRateInHS >= 1e3) {
    return { value: (hashRateInHS / 1e3).toFixed(2), unit: 'KH/s' };
  }
  return { value: hashRateInHS.toFixed(2), unit: 'H/s' };
}

// Usage: 1080 H/s → { value: "1.08", unit: "KH/s" }
```

---

### 7️⃣ Lấy trạng thái tất cả miners
**GET** `/api/status`

#### Response
```json
{
  "success": true,
  "miners": [
    {
      "success": true,
      "name": "vrsc-gpu1",
      "status": "running",
      "pid": 12345,
      "hash_rate": 50500000,
      "coin_name": "vrsc",
      "mining_tool": "ccminer",
      "auto_start": true
    },
    {
      "success": true,
      "name": "dero-miner",
      "status": "stopped",
      "pid": null,
      "hash_rate": 0,
      "coin_name": "dero",
      "mining_tool": "astrominer",
      "auto_start": false
    }
  ]
}
```

---

### 8️⃣ Auto-Start Management

#### 8.1 Lấy config auto-start
**GET** `/api/auto-start/config`

##### Response
```json
{
  "success": true,
  "global_enabled": true,
  "auto_start_miners": [
    {
      "name": "vrsc-gpu1",
      "coin_name": "vrsc",
      "mining_tool": "ccminer",
      "status": "running"
    }
  ]
}
```

#### 8.2 Enable/Disable auto-start globally
**POST** `/api/auto-start/config`

##### Request Body
```json
{
  "enabled": true
}
```

##### Response
```json
{
  "success": true,
  "message": "Auto-start đã được bật",
  "global_enabled": true
}
```

#### 8.3 Trigger auto-start thủ công
**POST** `/api/auto-start`

##### Response
```json
{
  "success": true,
  "message": "Đã kích hoạt auto-start cho 2 miner(s)",
  "started": ["vrsc-gpu1", "dero-miner"]
}
```

---

### 9️⃣ Debug Endpoints

#### 9.1 Xem raw output của miner
**GET** `/api/debug/output/{miner_name}`

##### Response
```json
{
  "success": true,
  "name": "dero-miner",
  "output": "[dero] 16-10-2025 08:14:42 [pool] Accepted 318 | Hashrate 1.055KH/s\n[dero] Connected to pool..."
}
```

---

## 📊 Client Integration Examples

### JavaScript/TypeScript
```typescript
class MiningAPIClient {
  constructor(private baseURL: string = 'http://localhost:9098') {}

  async updateConfig(miners: MinerConfig[]): Promise<void> {
    const res = await fetch(`${this.baseURL}/api/update-config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(miners)
    });
    return res.json();
  }

  async startMiner(name: string): Promise<void> {
    const res = await fetch(`${this.baseURL}/api/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    return res.json();
  }

  async stopMiner(name: string): Promise<void> {
    const res = await fetch(`${this.baseURL}/api/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    return res.json();
  }

  async getStatus(name?: string): Promise<MinerStatus> {
    const url = name 
      ? `${this.baseURL}/api/status?name=${name}`
      : `${this.baseURL}/api/status`;
    const res = await fetch(url);
    return res.json();
  }

  formatHashRate(hashRateHS: number): string {
    if (hashRateHS >= 1e9) return `${(hashRateHS/1e9).toFixed(2)} GH/s`;
    if (hashRateHS >= 1e6) return `${(hashRateHS/1e6).toFixed(2)} MH/s`;
    if (hashRateHS >= 1e3) return `${(hashRateHS/1e3).toFixed(2)} KH/s`;
    return `${hashRateHS.toFixed(2)} H/s`;
  }
}
```

### Python
```python
import requests

class MiningAPIClient:
    def __init__(self, base_url='http://localhost:9098'):
        self.base_url = base_url
    
    def update_config(self, miners):
        res = requests.post(f'{self.base_url}/api/update-config', json=miners)
        return res.json()
    
    def start_miner(self, name):
        res = requests.post(f'{self.base_url}/api/start', json={'name': name})
        return res.json()
    
    def stop_miner(self, name):
        res = requests.post(f'{self.base_url}/api/stop', json={'name': name})
        return res.json()
    
    def get_status(self, name=None):
        url = f'{self.base_url}/api/status'
        if name:
            url += f'?name={name}'
        res = requests.get(url)
        return res.json()
    
    def format_hash_rate(self, hash_rate_hs):
        if hash_rate_hs >= 1e9:
            return f"{hash_rate_hs/1e9:.2f} GH/s"
        elif hash_rate_hs >= 1e6:
            return f"{hash_rate_hs/1e6:.2f} MH/s"
        elif hash_rate_hs >= 1e3:
            return f"{hash_rate_hs/1e3:.2f} KH/s"
        return f"{hash_rate_hs:.2f} H/s"
```

### cURL Examples
```bash
# Update config
curl -X POST http://localhost:9098/api/update-config \
  -H "Content-Type: application/json" \
  -d '[{"name":"vrsc","coin_name":"vrsc","mining_tool":"ccminer","config":{...},"auto_start":true}]'

# Start miner
curl -X POST http://localhost:9098/api/start \
  -H "Content-Type: application/json" \
  -d '{"name":"vrsc"}'

# Stop miner
curl -X POST http://localhost:9098/api/stop \
  -H "Content-Type: application/json" \
  -d '{"name":"vrsc"}'

# Get status
curl http://localhost:9098/api/status?name=vrsc

# Force stop all
curl -X POST http://localhost:9098/api/force-stop-all
```

## 🔧 Cách hoạt động

### 1. Khi update-config:
1. Tạo thư mục `miners/{coin_name}/`
2. Tải file từ `http://cdn.dndvina.com/minings/{filename}`
3. Tạo `config.json` trong thư mục coin
4. Tạo command: `"{coin_dir}/ccminer.exe" -c "{coin_dir}/config.json"`

### 2. Khi start mining:
1. Ghi config vào `config.json`
2. Chuyển đến thư mục coin
3. Chạy mining tool với đường dẫn đúng
4. Monitor hash rate theo tool-specific patterns

### 3. Auto-download logic:
- Chỉ tải nếu file chưa tồn tại
- Hỗ trợ resumable download
- Validate file integrity

---

## 🎯 Quick Start Examples

### Example 1: Setup VRSC Mining
```bash
# 1. Update config với auto-start
curl -X POST http://localhost:9098/api/update-config \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "vrsc-main",
      "coin_name": "vrsc",
      "mining_tool": "ccminer",
      "config": {
        "pools": [
          {
            "name": "AP",
            "url": "stratum+tcp://ap.luckpool.net:3956",
            "timeout": 150
          }
        ],
        "user": "RCtqovjA8xLBxdQoHJcepDBd9h6Lh7pPxp.worker1",
        "algo": "verus",
        "threads": 8
      },
      "required_files": ["ccminer.exe", "libcrypto-1_1-x64.dll"],
      "auto_start": true
    }
  ]'

# 2. Start mining (hoặc chờ auto-start)
curl -X POST http://localhost:9098/api/start \
  -H "Content-Type: application/json" \
  -d '{"name":"vrsc-main"}'

# 3. Check status
curl http://localhost:9098/api/status?name=vrsc-main
```

### Example 2: Setup DERO Mining (CLI Parameters)
```bash
curl -X POST http://localhost:9098/api/update-config \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "dero-cpu",
      "coin_name": "dero",
      "mining_tool": "astrominer",
      "config": "-w deroi1qyzlxxgq2weyqlxg5u4tkng2lf5rktwanqhse2hwm577ps22zv2x2q9pvfz92.worker1 -r dero.rabidmining.com:10300 -m 8",
      "required_files": ["astrominer"],
      "auto_start": false
    }
  ]'
```

### Example 3: Monitor Hash Rates
```python
import requests
import time

api = 'http://localhost:9098'

while True:
    res = requests.get(f'{api}/api/status').json()
    
    for miner in res['miners']:
        if miner['status'] == 'running':
            # API returns H/s, convert to readable format
            hr = miner['hash_rate']
            if hr >= 1e6:
                hr_str = f"{hr/1e6:.2f} MH/s"
            elif hr >= 1e3:
                hr_str = f"{hr/1e3:.2f} KH/s"
            else:
                hr_str = f"{hr:.2f} H/s"
            
            print(f"{miner['name']}: {hr_str} (PID: {miner['pid']})")
    
    time.sleep(10)
```

---

## 🔧 Deployment trên Production

### Ubuntu Server
```bash
# 1. Clone repository
git clone https://github.com/ndduoc1189/dndvina-mining.git
cd dndvina-mining

# 2. Run install script
chmod +x install.sh
./install.sh

# 3. Configure miners via API
curl -X POST http://localhost:9098/api/update-config \
  -H "Content-Type: application/json" \
  -d @miners-config.json

# 4. Start with systemd
sudo systemctl start mining-manager
sudo systemctl enable mining-manager  # Auto-start on boot
```

### Windows Server
```powershell
# 1. Clone repository
git clone https://github.com/ndduoc1189/dndvina-mining.git
cd dndvina-mining

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start server
.\start_server.bat

# Or run directly
python app.py
```

### Monitoring & Logs
```bash
# Ubuntu - Check systemd service
sudo systemctl status mining-manager
sudo journalctl -u mining-manager -f

# Check miners via API
curl http://localhost:9098/api/status

# Debug specific miner output
curl http://localhost:9098/api/debug/output/vrsc-main
```

---

## 📋 Configuration File Format

### miners-config.json
```json
[
  {
    "name": "vrsc-gpu1",
    "coin_name": "vrsc",
    "mining_tool": "ccminer",
    "config": {
      "pools": [
        {
          "name": "LuckPool-AP",
          "url": "stratum+tcp://ap.luckpool.net:3956",
          "timeout": 150
        }
      ],
      "user": "YOUR_WALLET_ADDRESS.worker1",
      "algo": "verus",
      "threads": 8,
      "cpu-priority": 1
    },
    "required_files": ["ccminer.exe", "libcrypto-1_1-x64.dll"],
    "auto_start": true
  },
  {
    "name": "dero-cpu1",
    "coin_name": "dero",
    "mining_tool": "astrominer",
    "config": "-w YOUR_DERO_WALLET.worker1 -r dero.rabidmining.com:10300 -m 8",
    "required_files": ["astrominer"],
    "auto_start": true
  }
]
```

---

## 🎯 Lợi ích

✅ **API-First Design** - RESTful JSON API cho mọi platform  
✅ **Auto-Download** - Tự động tải mining tools từ CDN  
✅ **Multi-Coin Support** - Đào nhiều coin đồng thời  
✅ **Smart Hash Rate** - Auto-detect patterns cho từng tool  
✅ **Flexible Config** - JSON config hoặc CLI parameters  
✅ **Auto-Start** - Per-miner và global auto-start  
✅ **Graceful Shutdown** - SIGINT → SIGTERM → SIGKILL  
✅ **Cross-Platform** - Windows & Linux support  
✅ **Production Ready** - Systemd, logging, monitoring  
✅ **Client Libraries** - Python, JavaScript, TypeScript examples  

---

## 🛠️ Troubleshooting

### Server không khởi động
```bash
# Check port conflict
netstat -ano | findstr :9098  # Windows
lsof -i :9098                 # Linux

# Check logs
cat server.log               # Ubuntu
type server.log              # Windows
```

### File mining không tải được
```bash
# Kiểm tra CDN URL
curl -I http://cdn.dndvina.com/minings/ccminer.exe

# Kiểm tra quyền thư mục
ls -la miners/              # Linux
dir miners\                 # Windows

# Download thủ công
curl -o miners/vrsc/ccminer.exe http://cdn.dndvina.com/minings/ccminer.exe
```

### Miner không start
```bash
# Check miner config
curl http://localhost:9098/api/status?name=vrsc-main

# Check debug output
curl http://localhost:9098/api/debug/output/vrsc-main

# Check file permissions (Linux)
ls -la miners/vrsc/
chmod +x miners/vrsc/ccminer
```

### Hash rate = 0
```bash
# Check if miner is running
curl http://localhost:9098/api/status?name=vrsc-main

# Check raw output
curl http://localhost:9098/api/debug/output/vrsc-main

# Verify mining tool is producing output
# Server auto-detects these patterns:
# - ccminer: "GPU #0: 25.50 MH/s"
# - astrominer: "Hashrate 1.08KH/s"
# - xmrig: "speed 1000.0 H/s"
```

### Miner không stop
```bash
# Force stop all
curl -X POST http://localhost:9098/api/force-stop-all

# Check running processes
ps aux | grep ccminer        # Linux
tasklist | findstr ccminer  # Windows

# Manual kill
kill -9 <PID>               # Linux
taskkill /F /PID <PID>      # Windows
```

### API Error Responses
```json
// Miner not found
{
  "success": false,
  "message": "Miner vrsc-main không tồn tại"
}

// Already running
{
  "success": false,
  "message": "Miner vrsc-main đang chạy"
}

// Start failed
{
  "success": false,
  "message": "Lỗi khi bắt đầu đào: <error details>"
}
```

---

## 📚 API Response Codes

| HTTP Code | Meaning | Example |
|-----------|---------|---------|
| **200** | Success | Miner started/stopped successfully |
| **400** | Bad Request | Invalid JSON, missing fields |
| **404** | Not Found | Miner name doesn't exist |
| **500** | Server Error | Process spawn failed, file I/O error |

---

## 🔒 Security Notes

⚠️ **Production Deployment:**
- API hiện tại **KHÔNG có authentication**
- Khuyến nghị chạy trong **private network** hoặc thêm reverse proxy (nginx) với auth
- Không expose port `9098` ra internet công cộng
- Sử dụng firewall để restrict access

**Recommended Setup:**
```nginx
# nginx reverse proxy với basic auth
server {
    listen 80;
    server_name mining.yourdomain.com;
    
    location /api/ {
        auth_basic "Mining API";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://localhost:9098;
    }
}
```

---

## 📞 Support & Contributing

- **GitHub**: https://github.com/ndduoc1189/dndvina-mining
- **Issues**: Report bugs via GitHub Issues
- **Pull Requests**: Welcome!

**Development Setup:**
```bash
git clone https://github.com/ndduoc1189/dndvina-mining.git
cd dndvina-mining
pip install -r requirements.txt
python app.py
```

---

## 📄 License

MIT License - Free to use for personal and commercial projects.

---

## 🎉 Credits

Developed by **ndduoc1189** for remote mining management.

**Supported Mining Tools:**
- CCMiner - NVIDIA GPU miner
- Astrominer - DERO miner  
- T-Rex - Multi-algo NVIDIA miner
- GMiner - AMD/NVIDIA miner
- XMRig - Monero CPU miner
- PhoenixMiner - ETH miner