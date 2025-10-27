# Cấu trúc Config Mới - Global Auto-Start

## ✅ Thay đổi đã thực hiện

### 1. **Cấu trúc Config Mới**
```json
{
  "last_sync_config": 1730042400,  // ← Unix timestamp (số giây)
  "auto_start": true,  // ← Global flag: tự động khởi động TẤT CẢ miners
  "miners": {
    "vrsc": {
      "coin_name": "vrsc",
      "mining_tool": "ccminer",
      "config": {...},
      "status": "stopped",
      ...
      // ❌ KHÔNG CÒN auto_start ở mỗi miner
    },
    "dero": {
      "coin_name": "dero",
      "mining_tool": "astrominer",
      "config": "...",
      "status": "stopped",
      ...
    }
  }
}
```

### 2. **Logic Auto-Start**

#### Trước đây (per-miner auto_start):
```python
# Mỗi miner có auto_start riêng
for name, miner in miners.items():
    if miner.get('auto_start', False) and status == 'stopped':
        start_miner(name)  # Chỉ start miner có auto_start=true
```

#### Bây giờ (global auto_start):
```python
# Global flag quyết định cho TẤT CẢ miners
if config['auto_start'] == true:
    for name, miner in miners.items():
        if status == 'stopped':
            start_miner(name)  # Start TẤT CẢ miners đã stopped
```

### 3. **API Endpoints Đã Cập Nhật**

#### POST `/api/update-config`
**Request mới:**
```json
{
  "last_sync_config": 1730042400,
  "auto_start": true,
  "miners": [
    {
      "coin_name": "vrsc",
      "mining_tool": "ccminer",
      "config": {...},
      "required_files": ["ccminer"]
      // ❌ KHÔNG CÒN "auto_start" field
    }
  ]
}
```

**Response mới:**
```json
{
  "success": true,
  "updated": 2,
  "total": 2,
  "last_sync_config": 1730042400,
  "auto_start_enabled": true,
  "auto_start_result": {
    "stopped": [
      {"name": "vrsc", "stopped": true},
      {"name": "dero", "stopped": true}
    ],
    "started": [
      {"name": "vrsc", "started": true, "message": "Miner vrsc started"},
      {"name": "dero", "started": true, "message": "Miner dero started"}
    ]
  },
  "results": [...]
}
```

**Hành vi:**
- ✅ Nếu `auto_start: true` → Stop tất cả miners cũ → Start lại TẤT CẢ miners mới
- ❌ Nếu `auto_start: false` → Chỉ update config, không start

#### GET `/api/status`
**Response mới:**
```json
{
  "success": true,
  "last_sync_config": "2025-10-27T12:00:00Z",
  "auto_start": true,  // ← Global flag
  "miners": [
    {
      "name": "vrsc",
      "status": "running",
      "coin_name": "vrsc",
      ...
      // ❌ KHÔNG CÒN "auto_start" field ở mỗi miner
    }
  ]
}
```

### 4. **Hành Vi Khi App Khởi Động**

#### Scenario 1: `auto_start: true` khi boot app
```
App Boot → 5 giây chờ → Tự động start TẤT CẢ miners (vrsc + dero)
```

#### Scenario 2: `auto_start: false` khi boot app
```
App Boot → 5 giây chờ → KHÔNG start miners nào
```

#### Scenario 3: `auto_start: true` khi update config
```
POST /api/update-config với auto_start=true
  ↓
Stop tất cả miners đang chạy
  ↓
Chờ 3 giây + Force kill
  ↓
Start lại TẤT CẢ miners
  ↓
Response với auto_start_result (stopped/started miners)
```

#### Scenario 4: `auto_start: false` khi update config
```
POST /api/update-config với auto_start=false
  ↓
Chỉ update config
  ↓
KHÔNG start miners
```

### 5. **Files Đã Sửa**

#### `app.py`
- **`load_config()`**: Đọc `auto_start` từ config wrapper
- **`save_config()`**: Lưu format mới với `{last_sync_config, auto_start, miners}`
- **`auto_start_miners()`**: Logic mới - start TẤT CẢ miners nếu global flag = true
- **`update_miner_config()`**: Loại bỏ tham số `auto_start` (không cần nữa)
- **`get_miner_status()`**: Không trả về `auto_start` cho từng miner
- **`get_all_status()`**: Thêm `auto_start` ở cấp độ global response
- **`/api/update-config`**: Nhận `auto_start` từ config wrapper, không từ mỗi miner

## 📋 Test Cases

### ✅ Test 1: Global Auto-Start = true
```bash
python test_global_auto_start.py
# Kết quả: Cả vrsc và dero đều sẽ tự động start
```

### ✅ Test 2: Global Auto-Start = false
```bash
# Config: mining_config_no_auto_start.json
# Kết quả: KHÔNG có miner nào tự động start
```

## 🎯 Tóm Tắt Thay Đổi

| Trước                              | Sau                                |
|------------------------------------|------------------------------------|
| `auto_start` ở **mỗi miner**       | `auto_start` ở **config global**   |
| Start **một số miners** (selective)| Start **TẤT CẢ miners** hoặc không |
| Config phức tạp hơn               | Config đơn giản hơn                |
| Logic phân tán                     | Logic tập trung                    |

## 📦 Files Mẫu

- `mining_config_global_auto_start.json` - auto_start = true
- `mining_config_no_auto_start.json` - auto_start = false
- `test_global_auto_start.py` - Script test logic

## 🚀 Cách Sử Dụng

1. **Bật auto-start cho tất cả miners:**
   ```bash
   # Chỉnh mining_config.json
   {
     "auto_start": true,
     "miners": {...}
   }
   ```

2. **Tắt auto-start:**
   ```bash
   # Chỉnh mining_config.json
   {
     "auto_start": false,
     "miners": {...}
   }
   ```

3. **Khởi động app:**
   ```bash
   python app.py
   # Sau 5 giây, nếu auto_start=true → tất cả miners sẽ start
   ```
