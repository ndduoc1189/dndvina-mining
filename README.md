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

## API Endpoints

### 1. Cập nhật cấu hình miners (với auto-download & auto-start)
**POST** `/api/update-config`

Body:
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
        },
        {
          "name": "NA",
          "url": "stratum+tcp://eu.luckpool.net:3956",
          "timeout": 60,
          "time-limit": 1000,
          "disabled": 0
        }
      ],
      "user": "RCtqovjA8xLBxdQoHJcepDBd9h6Lh7pPxp.[DEVICE_ID]",
      "algo": "verus",
      "threads": 8,
      "cpu-priority": 1,
      "retry-pause": 5
    },
    "required_files": ["ccminer.exe", "libcrypto-1_1-x64.dll"],  // optional
    "auto_start": true  // optional - enable auto-start
  }
]
```

### 2. Mining tools được hỗ trợ

| Tool | Default Files | Hash Rate Pattern |
|------|---------------|-------------------|
| ccminer | ccminer.exe, libcrypto-1_1-x64.dll | GPU #0: 25.50 MH/s |
| t-rex | t-rex.exe | GPU #0: 45.5 MH/s |
| gminer | miner.exe | GPU0 50.5 MH/s |
| xmrig | xmrig.exe | speed 1000.0 H/s |
| phoenixminer | PhoenixMiner.exe | GPU1: 50.5 MH/s |

### 3. Bắt đầu mining
**POST** `/api/start`

```json
{"name": "vrsc"}
```

### 4. Dừng mining
**POST** `/api/stop`

```json
{"name": "vrsc"}
```

Hoặc dừng nhiều miners:
```json
{"names": ["vrsc", "bitcoin"]}
```

### 5. Force kill tất cả mining processes (Emergency Stop)
**POST** `/api/kill-all`

```json
{"process_names": ["ccminer", "t-rex", "xmrig"]}  // optional
```

**Cách hoạt động:**
- **Auto-detect**: Nếu không có `process_names`, sẽ tự động lấy mining tools từ miners đã config (ccminer, t-rex, xmrig, etc.)
- **Cross-platform**: Tìm cả `.exe` và non-`.exe` versions
- **Process scanning**: Scan tất cả running processes để tìm matching names
- **Force kill**: Kill parent process và tất cả children
- **Reset status**: Set tất cả miners về "stopped"

**Response:**
```json
{
  "success": true,
  "message": "Force killed 3 mining processes", 
  "killed_count": 3,
  "active_tools_before_kill": ["ccminer", "t-rex"],
  "target_process_names": ["ccminer", "ccminer.exe", "t-rex", "t-rex.exe"]
}
```

### 6. Kiểm tra trạng thái
**GET** `/api/status?name=vrsc-gpu1`

Response:
```json
{
  "success": true,
  "name": "vrsc-gpu1",
  "status": "running",
  "pid": 1234,
  "start_time": "2025-10-15T10:30:00",
  "hash_rate": 50000000,
  "coin_name": "vrsc",
  "mining_tool": "ccminer",
  "auto_start": true,
  "last_output": "GPU #0: GeForce RTX 3080 - 50.5 MH/s"
}
```

### 5. Auto-Start Management

#### Get auto-start config
**GET** `/api/auto-start/config`

Response:
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

#### Enable/disable auto-start globally
**POST** `/api/auto-start/config`

Body:
```json
{"enabled": true}
```

#### Manually trigger auto-start
**POST** `/api/auto-start`

Response:
```json
{
  "success": true,
  "message": "Auto-start triggered"
}
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

## 🎯 Ví dụ sử dụng VRSC

### 1. Thiết lập VRSC mining với auto-start
```bash
curl -X POST http://localhost:5000/api/update-config \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "vrsc",
      "coin_name": "vrsc",
      "mining_tool": "ccminer",
      "config": {
        "pools": [
          {
            "name": "AP",
            "url": "stratum+tcp://ap.luckpool.net:3956",
            "timeout": 150,
            "disabled": 0
          },
          {
            "name": "NA",
            "url": "stratum+tcp://eu.luckpool.net:3956",
            "timeout": 60,
            "time-limit": 1000,
            "disabled": 0
          }
        ],
        "user": "RCtqovjA8xLBxdQoHJcepDBd9h6Lh7pPxp.[DEVICE_ID]",
        "algo": "verus",
        "threads": 8,
        "cpu-priority": 1,
        "retry-pause": 5
      },
      "auto_start": true
    }
  ]'
```

### 2. Khởi động server với auto-restart (Ubuntu)
```bash
./run.sh
```

### 3. Khởi động server với systemd (Ubuntu)
```bash
sudo systemctl start mining-manager
sudo systemctl enable mining-manager  # Auto-start on boot
```

### 4. Kiểm tra trạng thái
```bash
curl http://localhost:5000/api/status?name=vrsc
```

## 🔧 Deployment trên Production

### Ubuntu Server
```bash
# 1. Clone repository
git clone <your-repo>
cd dndvina-mining

# 2. Run install script
./install.sh

# 3. Configure miners via API
curl -X POST http://localhost:5000/api/update-config -d @config.json

# 4. Start with systemd
sudo systemctl start mining-manager
sudo systemctl enable mining-manager
```

### Monitoring
```bash
# Check status
sudo systemctl status mining-manager

# View logs
sudo journalctl -u mining-manager -f

# Check miners
curl http://localhost:5000/api/status
```

## 🎯 Lợi ích

✅ **Không cần cài đặt thủ công** - Tự động tải mining tools  
✅ **Quản lý đa coin** - Mỗi coin có môi trường riêng  
✅ **Tool-specific optimization** - Hash rate detection chính xác  
✅ **Zero-config deployment** - Chỉ cần start server  
✅ **Path management** - Tự động resolve đường dẫn  
✅ **Concurrent mining** - Đào nhiều coin cùng lúc  
✅ **Auto-start on boot** - Tự động chạy mining khi khởi động  
✅ **Flexible auto-start** - Enable/disable theo từng miner  
✅ **Auto-restart** - Tự động khởi động lại khi crash  
✅ **Production ready** - Systemd support, logging, monitoring  

## 📋 Scripts có sẵn

### Windows
- `start_server.bat` - Khởi động server

### Ubuntu/Linux  
- `install.sh` - Cài đặt tự động
- `run.sh` - Chạy với auto-restart
- Systemd service - Production deployment

## 🛠️ Troubleshooting

### File không tải được:
- Kiểm tra kết nối internet
- Kiểm tra URL: `http://cdn.dndvina.com/minings/ccminer.exe`
- Kiểm tra quyền ghi thư mục

### Mining không start:
- Kiểm tra file exe có tồn tại không
- Kiểm tra config.json có valid không  
- Kiểm tra log trong `last_output`

### Hash rate = 0:
- Kiểm tra mining tool có đang chạy không
- Kiểm tra pattern detection cho tool cụ thể
- Xem log output để debug pattern

### Server crash:
- Sử dụng `run.sh` cho auto-restart
- Kiểm tra log file `server.log`
- Sử dụng systemd cho production  

## 🛠️ Troubleshooting

### File không tải được:
- Kiểm tra kết nối internet
- Kiểm tra URL: `http://cdn.dndvina.com/minings/ccminer.exe`
- Kiểm tra quyền ghi thư mục

### Mining không start:
- Kiểm tra file exe có tồn tại không
- Kiểm tra config.json có valid không  
- Kiểm tra log trong `last_output`

### Hash rate = 0:
- Kiểm tra mining tool có đang chạy không
- Kiểm tra pattern detection cho tool cụ thể
- Xem log output để debug pattern