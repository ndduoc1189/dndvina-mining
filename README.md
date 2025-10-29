# Mining Management API - Remote Control Mining# Mining Management API# Mining Management API - Remote Control Mining



API quản lý mining từ xa qua HTTP với tính năng auto-download, auto-start và sync config.



## ✨ Tính năng chínhAPI quản lý mining từ xa qua HTTP với config sync và auto-start.API quản lý mining từ xa qua HTTP với tính năng auto-download, auto-start và sync config.



- 🔄 **Config Sync**: Đồng bộ config từ server về client với timestamp

- 🚀 **Global Auto-Start**: Tự động start TẤT CẢ miners khi boot (1 flag toàn cục)

- 📦 **Auto-Download**: Tự động tải mining tools từ CDN**Server:** `http://localhost:9098`## ✨ Tính năng chính

- 🎯 **Smart Hash Rate**: Auto-detect hash rate cho từng mining tool

- ⚡ **Auto-Restart (Background)**: Tự động restart miners KHÔNG ĐỒNG BỘ khi update config

- 🐧 **Cross-Platform**: Windows & Linux support

---- 🔄 **Config Sync**: Đồng bộ config từ server về client với timestamp

---

- 🚀 **Global Auto-Start**: Tự động start TẤT CẢ miners khi boot (1 flag toàn cục)

## 🚀 Cài đặt nhanh

## 🚀 Quick Start- 📦 **Auto-Download**: Tự động tải mining tools từ CDN

### Windows

```bash- 🎯 **Smart Hash Rate**: Auto-detect hash rate cho từng mining tool

pip install -r requirements.txt

python app.py```bash- ⚡ **Auto-Restart**: Tự động restart miners khi update config (nếu auto_start=true)

```

# Windows- 🐧 **Cross-Platform**: Windows & Linux support

### Linux/Ubuntu

```bashpip install -r requirements.txt && python app.py

chmod +x install.sh && ./install.sh

chmod +x run.sh && ./run.sh---

```

# Linux

**Server chạy tại:** `http://localhost:9098`

chmod +x install.sh && ./install.sh && ./run.sh## 🚀 Cài đặt nhanh

---

```

## 📡 API Endpoints

### Windows

### 1. **GET /api/status** - Lấy trạng thái

---```bash

**Response:**

```jsonpip install -r requirements.txt

{

  "success": true,## 📡 API Referencepython app.py

  "last_sync_config": 1730042400,

  "auto_start": true,```

  "miners": [

    {### 1. GET `/api/status` - Lấy trạng thái

      "name": "vrsc",

      "status": "running",### Linux/Ubuntu

      "hash_rate": 50500000,

      "coin_name": "vrsc",```typescript```bash

      "mining_tool": "ccminer",

      "pid": 12345GET /api/statuschmod +x install.sh && ./install.sh

    }

  ]```chmod +x run.sh && ./run.sh

}

``````



**Fields:****Response:**

- `last_sync_config`: Unix timestamp (số giây) - thời điểm sync config gần nhất

- `auto_start`: Boolean - global flag tự động start tất cả miners```json**Server chạy tại:** `http://localhost:9098`

- `miners[]`: Array - danh sách miners

- `hash_rate`: Number - đơn vị H/s (client tự convert sang KH/s, MH/s, GH/s){



---  "success": true,---



### 2. **POST /api/update-config** - Cập nhật config  "last_sync_config": 1730042400,



**Request:**  "auto_start": true,## 📡 API Endpoints

```json

{  "miners": [

  "last_sync_config": 1730042400,

  "auto_start": true,    {### 1. **GET /api/status** - Lấy trạng thái

  "miners": [

    {      "name": "vrsc",

      "coin_name": "vrsc",

      "mining_tool": "ccminer",      "status": "running",**Response:**

      "config": {

        "pools": [{      "hash_rate": 50500000,```json

          "url": "stratum+tcp://pool.com:3956",

          "user": "WALLET.worker1"      "coin_name": "vrsc",{

        }],

        "algo": "verus"      "mining_tool": "ccminer",  "success": true,

      },

      "required_files": ["ccminer"]      "pid": 12345  "last_sync_config": 1730042400,

    }

  ]    }  "auto_start": true,

}

```  ]  "miners": [



**⚡ Hành vi mới (Non-blocking):**}    {

1. **Update config** ngay lập tức

2. **Lưu config** vào file```      "name": "vrsc",

3. **Trả response** cho client ngay (KHÔNG chờ restart)

4. **Background thread** tự động:      "status": "running",

   - Stop tất cả miners (nếu `auto_start: true`)

   - Chờ 5 giây**Fields:**      "hash_rate": 50500000,

   - Start lại TẤT CẢ miners

- `last_sync_config`: Unix timestamp - thời điểm sync gần nhất      "coin_name": "vrsc",

**⚠️ Lợi ích:**

- Client **KHÔNG phải đợi** quá trình restart (mất 10-15 giây)- `auto_start`: Boolean - global auto-start flag      "mining_tool": "ccminer",

- Response trả về **ngay lập tức** (< 1 giây)

- Restart diễn ra **trong background** an toàn- `hash_rate`: Number (H/s) - client tự convert sang KH/s, MH/s, GH/s      "pid": 12345



**Response (Immediate - không chờ restart):**    }

```json

{---  ]

  "success": true,

  "updated": 1,}

  "total": 1,

  "last_sync_config": 1730042400,### 2. POST `/api/update-config` - Update config```

  "auto_start_enabled": true,

  "message": "Config updated successfully. Auto-restart will happen in background.",

  "results": [

    {```typescript**Fields:**

      "coin_name": "vrsc",

      "success": true,POST /api/update-config- `last_sync_config`: Unix timestamp (số giây) - thời điểm sync config gần nhất

      "message": "Cập nhật cấu hình thành công"

    }Content-Type: application/json- `auto_start`: Boolean - global flag tự động start tất cả miners

  ]

}```- `miners[]`: Array - danh sách miners

```

- `hash_rate`: Number - đơn vị H/s (client tự convert sang KH/s, MH/s, GH/s)

**Server Logs (Background):**

```**Request:**

[CẬP NHẬT] 🔄 auto_start=true, khởi động background thread để restart miners...

[BG-RESTART] Bắt đầu stop tất cả miners...```json---

[BG-RESTART] Đang dừng DERO...

[BG-RESTART] Đã dừng 2 miners, chờ 5 giây...{

[BG-RESTART] Đang khởi động lại tất cả miners...

[BG-RESTART] ✅ Đã khởi động VRSC  "last_sync_config": 1730042400,### 2. **POST /api/update-config** - Cập nhật config

[BG-RESTART] ✅ Đã khởi động DERO

[BG-RESTART] ✅ Hoàn thành restart: 2/2 miners started  "auto_start": true,

```

  "miners": [**Request:**

---

    {```json

### 3. **POST /api/start** - Start miner

      "coin_name": "vrsc",{

```json

{      "mining_tool": "ccminer",  "last_sync_config": 1730042400,

  "name": "vrsc"

}      "config": {  "auto_start": true,

```

        "pools": [{"url": "stratum+tcp://pool:3956", "user": "WALLET"}],  "miners": [

### 4. **POST /api/stop** - Stop miner

        "algo": "verus"    {

```json

{      },      "coin_name": "vrsc",

  "name": "vrsc"

}      "required_files": ["ccminer"]      "mining_tool": "ccminer",

```

    }      "config": {

### 5. **POST /api/force-stop-all** - Emergency stop

  ]        "pools": [{

Dừng ngay lập tức TẤT CẢ mining processes.

}          "url": "stratum+tcp://pool.com:3956",

---

```          "user": "WALLET.worker1"

## 🔄 Config Sync Flow

        }],

### Client Logic:

```typescript**Behavior:**        "algo": "verus"

// 1. Lấy last_sync_config từ server

const serverStatus = await fetch('/api/status').then(r => r.json());- `auto_start: true` → Stop all → Update → Start all      },

const serverTimestamp = serverStatus.last_sync_config; // Unix timestamp

- `auto_start: false` → Chỉ update      "required_files": ["ccminer"]

// 2. So sánh với local config

const localTimestamp = getLocalConfigTimestamp(); // Từ database/storage    }



if (serverTimestamp > localTimestamp) {**Response:**  ]

  // Server config mới hơn → Không cần update

  console.log('Config is up-to-date');```json}

} else if (serverTimestamp < localTimestamp) {

  // Local config mới hơn → Cần push lên server{```

  const response = await updateServerConfig({

    last_sync_config: Date.now() / 1000, // Current timestamp  "success": true,

    auto_start: true,

    miners: [...localMiners]  "updated": 1,**Hành vi khi `auto_start: true`:**

  });

    "total": 1,1. Stop tất cả miners đang chạy

  // Response trả về NGAY (không chờ restart)

  console.log('Config updated:', response.message);  "last_sync_config": 1730042400,2. Update config

  // → "Config updated successfully. Auto-restart will happen in background."

}  "auto_start_enabled": true,3. Start lại TẤT CẢ miners

```

  "auto_start_result": {4. Trả về kết quả stopped/started

### Default Timestamp:

- Server khởi động lần đầu: `last_sync_config = 1735689600` (2025-01-01 00:00:00)    "stopped": [{"name": "vrsc", "stopped": true}],

- Client thấy timestamp cũ → Trigger update config

    "started": [{"name": "vrsc", "started": true}]**Response:**

---

  }```json

## 🎯 Global Auto-Start

}{

### Logic:

- **`auto_start: true`** → Tự động start **TẤT CẢ** miners khi:```  "success": true,

  - App boot (sau 5 giây)

  - Update config (background thread, không block client)  "updated": 1,

  

- **`auto_start: false`** → KHÔNG tự động start---  "total": 1,



### Ví dụ:  "last_sync_config": 1730042400,

```json

{### 3. POST `/api/start` - Start miner  "auto_start_enabled": true,

  "auto_start": true,

  "miners": [  "auto_start_result": {

    {"coin_name": "vrsc", ...},

    {"coin_name": "dero", ...}```json    "stopped": [{"name": "vrsc", "stopped": true}],

  ]

}POST /api/start    "started": [{"name": "vrsc", "started": true}]

```

{"name": "vrsc"}  }

**Kết quả:** Cả `vrsc` VÀ `dero` đều sẽ tự động start.

```}

❌ **KHÔNG CÒN** `auto_start` riêng lẻ ở mỗi miner!

```

---

### 4. POST `/api/stop` - Stop miner

## 🔢 Hash Rate Format

---

**API luôn trả về H/s:**

```json```json

{

  "hash_rate": 50500000  // 50.5 MH/sPOST /api/stop### 3. **POST /api/start** - Start miner

}

```{"name": "vrsc"}



**Client convert:**``````json

```typescript

function formatHashRate(hashRateHS: number): string {{

  if (hashRateHS >= 1e9) return `${(hashRateHS/1e9).toFixed(2)} GH/s`;

  if (hashRateHS >= 1e6) return `${(hashRateHS/1e6).toFixed(2)} MH/s`;### 5. POST `/api/force-stop-all` - Emergency stop  "name": "vrsc"

  if (hashRateHS >= 1e3) return `${(hashRateHS/1e3).toFixed(2)} KH/s`;

  return `${hashRateHS.toFixed(2)} H/s`;}

}

```json```

// formatHashRate(50500000) → "50.50 MH/s"

// formatHashRate(1080) → "1.08 KH/s"POST /api/force-stop-all

```

```### 4. **POST /api/stop** - Stop miner

---



## 📦 Supported Mining Tools

---```json

| Tool | Hash Rate Pattern | Config Type |

|------|-------------------|-------------|{

| **ccminer** | `GPU #0: 25.50 MH/s` | JSON Object |

| **astrominer** | `Hashrate 1.08KH/s` | CLI String |## 🔄 Config Sync Logic  "name": "vrsc"

| **xmrig** | `speed 1000.0 H/s` | JSON Object |

| **t-rex** | `GPU #0: 45.5 MH/s` | JSON Object |}



**Auto-Download từ:** `http://cdn.dndvina.com/minings/{filename}````typescript```



---// 1. Get server timestamp



## 🔧 Config Examplesconst { last_sync_config } = await fetch('/api/status').then(r => r.json());### 5. **POST /api/force-stop-all** - Emergency stop



### JSON Config (ccminer):

```json

{// 2. Compare with localDừng ngay lập tức TẤT CẢ mining processes.

  "coin_name": "vrsc",

  "mining_tool": "ccminer",const localTimestamp = getLocalConfigTimestamp();

  "config": {

    "pools": [{---

      "url": "stratum+tcp://pool.com:3956",

      "user": "WALLET.worker1"if (last_sync_config < localTimestamp) {

    }],

    "algo": "verus",  // Server cũ hơn → Push config mới## 🔄 Config Sync Flow

    "threads": 8

  },  await fetch('/api/update-config', {

  "required_files": ["ccminer"]

}    method: 'POST',### Client Logic:

```

    headers: { 'Content-Type': 'application/json' },```typescript

### CLI String (astrominer):

```json    body: JSON.stringify({// 1. Lấy last_sync_config từ server

{

  "coin_name": "dero",      last_sync_config: Math.floor(Date.now() / 1000),const serverStatus = await fetch('/api/status').then(r => r.json());

  "mining_tool": "astrominer",

  "config": "-w WALLET -r pool.com:10300 -m 8",      auto_start: true,const serverTimestamp = serverStatus.last_sync_config; // Unix timestamp

  "required_files": ["astrominer"]

}      miners: [...]

```

    })// 2. So sánh với local config

---

  });const localTimestamp = getLocalConfigTimestamp(); // Từ database/storage

## 📱 Client Integration

}

### Kotlin/Android:

```kotlin```if (serverTimestamp > localTimestamp) {

data class MiningConfig(

    val last_sync_config: Long,  // Unix timestamp  // Server config mới hơn → Không cần update

    val auto_start: Boolean,

    val miners: List<MinerConfig>**Default:** Server khởi tạo với `last_sync_config = 1735689600` (2025-01-01)  console.log('Config is up-to-date');

)

} else if (serverTimestamp < localTimestamp) {

suspend fun syncConfig(localTimestamp: Long, localConfig: MiningConfig) {

    val serverStatus = apiService.getStatus()---  // Local config mới hơn → Cần push lên server

    

    if (serverStatus.last_sync_config < localTimestamp) {  await updateServerConfig({

        // Push local config to server

        val newConfig = localConfig.copy(## 🎯 Global Auto-Start    last_sync_config: Date.now() / 1000, // Current timestamp

            last_sync_config = System.currentTimeMillis() / 1000

        )    auto_start: true,

        val response = apiService.updateConfig(newConfig)

        ```json    miners: [...localMiners]

        // Response trả về ngay, restart diễn ra background

        Log.d("Mining", response.message){  });

    }

}  "auto_start": true,}

```

  "miners": [```

### JavaScript/React:

```typescript    {"coin_name": "vrsc", ...},

const syncConfig = async (localTimestamp: number, localConfig: Config) => {

  const serverStatus = await fetch('/api/status').then(r => r.json());    {"coin_name": "dero", ...}### Default Timestamp:

  

  if (serverStatus.last_sync_config < localTimestamp) {  ]- Server khởi động lần đầu: `last_sync_config = 1735689600` (2025-01-01 00:00:00)

    const response = await fetch('/api/update-config', {

      method: 'POST',}- Client thấy timestamp cũ → Trigger update config

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify({```

        last_sync_config: Math.floor(Date.now() / 1000),

        auto_start: true,---

        miners: localConfig.miners

      })- ✅ `auto_start: true` → Start TẤT CẢ miners (app boot + update config)

    }).then(r => r.json());

    - ❌ `auto_start: false` → KHÔNG start## 🎯 Global Auto-Start

    // Response trả về ngay (< 1s), không phải đợi restart

    console.log(response.message);

    // → "Config updated successfully. Auto-restart will happen in background."

  }❌ **KHÔNG CÒN** `auto_start` riêng lẻ ở mỗi miner!### Logic:

};

```- **`auto_start: true`** → Tự động start **TẤT CẢ** miners khi:



------  - App boot (sau 5 giây)



## 🎯 Typical Workflow  - Update config (stop cũ → start mới)



### 1. Client khởi động:## 🔢 Hash Rate Format  

```

Client → GET /api/status- **`auto_start: false`** → KHÔNG tự động start

       ← {last_sync_config: 1730042400, auto_start: true, miners: [...]}

       **API trả về H/s, client convert:**

Client: So sánh với local timestamp

       → Nếu server cũ hơn → Push config mới### Ví dụ:

```

```typescript```json

### 2. Update config từ client:

```function formatHashRate(hashRateHS: number): string {{

Client → POST /api/update-config

         {last_sync_config: 1730050000, auto_start: true, miners: [...]}  if (hashRateHS >= 1e9) return `${(hashRateHS/1e9).toFixed(2)} GH/s`;  "auto_start": true,

       

Server: ✅ Update config  if (hashRateHS >= 1e6) return `${(hashRateHS/1e6).toFixed(2)} MH/s`;  "miners": [

        ✅ Save to file

        ← Response NGAY (< 1s)  if (hashRateHS >= 1e3) return `${(hashRateHS/1e3).toFixed(2)} KH/s`;    {"coin_name": "vrsc", ...},

        

        [Background Thread]  return `${hashRateHS.toFixed(2)} H/s`;    {"coin_name": "dero", ...}

        🔄 Stop all miners

        ⏱️ Wait 5 seconds}  ]

        🚀 Start all miners

        ✅ Done (10-15s total)}

       

Client: ← {success: true, message: "Auto-restart will happen in background"}// Example: 50500000 → "50.50 MH/s"```

        (Không phải đợi 10-15s!)

``````



### 3. Monitor hash rate:**Kết quả:** Cả `vrsc` VÀ `dero` đều sẽ tự động start.

```

Client → GET /api/status (mỗi 10 giây)---

       ← {miners: [{hash_rate: 50500000, status: "running"}]}

       ❌ **KHÔNG CÒN** `auto_start` riêng lẻ ở mỗi miner!

Client: Format 50500000 H/s → "50.50 MH/s"

```## 📦 Mining Tools



------



## 🚨 Troubleshooting| Tool | Config Type | Hash Pattern |



### Server không start:|------|-------------|--------------|## 🔢 Hash Rate Format

```bash

# Check port| **ccminer** | JSON Object | `GPU #0: 25.50 MH/s` |

netstat -ano | findstr :9098  # Windows

lsof -i :9098                 # Linux| **astrominer** | CLI String | `Hashrate 1.08KH/s` |**API luôn trả về H/s:**



# Remove PID lock| **xmrig** | JSON Object | `speed 1000.0 H/s` |```json

rm mining_manager.pid         # Linux

del mining_manager.pid        # Windows{

```

**Auto-download từ:** `http://cdn.dndvina.com/minings/{filename}`  "hash_rate": 50500000  // 50.5 MH/s

### Config không sync:

```bash}

# Check server status

curl http://localhost:9098/api/status---```



# Force update (response trả về ngay, restart diễn ra background)

curl -X POST http://localhost:9098/api/update-config \

  -H "Content-Type: application/json" \## 💻 Client Examples**Client convert:**

  -d '{"last_sync_config": 1730050000, "auto_start": true, "miners": [...]}'

``````typescript



### Miners không auto-start:### Kotlin/Androidfunction formatHashRate(hashRateHS: number): string {

```bash

# Check global flag  if (hashRateHS >= 1e9) return `${(hashRateHS/1e9).toFixed(2)} GH/s`;

curl http://localhost:9098/api/status | grep auto_start

```kotlin  if (hashRateHS >= 1e6) return `${(hashRateHS/1e6).toFixed(2)} MH/s`;

# Manual trigger

curl -X POST http://localhost:9098/api/start \data class MiningConfig(  if (hashRateHS >= 1e3) return `${(hashRateHS/1e3).toFixed(2)} KH/s`;

  -d '{"name": "vrsc"}'

```    val last_sync_config: Long,  return `${hashRateHS.toFixed(2)} H/s`;



---    val auto_start: Boolean,}



## 📚 API Summary    val miners: List<MinerConfig>



| Endpoint | Method | Purpose | Response Time |)// formatHashRate(50500000) → "50.50 MH/s"

|----------|--------|---------|---------------|

| `/api/status` | GET | Lấy trạng thái + last_sync_config | Instant |// formatHashRate(1080) → "1.08 KH/s"

| `/api/update-config` | POST | Update config + **background restart** | **< 1s (không chờ restart)** |

| `/api/start` | POST | Start miner thủ công | Instant |suspend fun syncConfig(localTimestamp: Long, config: MiningConfig) {```

| `/api/stop` | POST | Stop miner thủ công | 2-5s |

| `/api/force-stop-all` | POST | Emergency stop tất cả | 5-10s |    val status = apiService.getStatus()



---    ---



## 📄 License    if (status.last_sync_config < localTimestamp) {



MIT License - Free to use        apiService.updateConfig(config.copy(## 📦 Supported Mining Tools



## 🎉 Credits            last_sync_config = System.currentTimeMillis() / 1000



Developed by **ndduoc1189**        ))| Tool | Hash Rate Pattern | Config Type |



GitHub: https://github.com/ndduoc1189/dndvina-mining    }|------|-------------------|-------------|


}| **ccminer** | `GPU #0: 25.50 MH/s` | JSON Object |

```| **astrominer** | `Hashrate 1.08KH/s` | CLI String |

| **xmrig** | `speed 1000.0 H/s` | JSON Object |

### TypeScript/React| **t-rex** | `GPU #0: 45.5 MH/s` | JSON Object |



```typescript**Auto-Download từ:** `http://cdn.dndvina.com/minings/{filename}`

const syncConfig = async (localTimestamp: number, config: Config) => {

  const { last_sync_config } = await fetch('/api/status').then(r => r.json());---

  

  if (last_sync_config < localTimestamp) {## 🔧 Config Examples

    await fetch('/api/update-config', {

      method: 'POST',### JSON Config (ccminer):

      body: JSON.stringify({```json

        last_sync_config: Math.floor(Date.now() / 1000),{

        auto_start: true,  "coin_name": "vrsc",

        miners: config.miners  "mining_tool": "ccminer",

      })  "config": {

    });    "pools": [{

  }      "url": "stratum+tcp://pool.com:3956",

};      "user": "WALLET.worker1"

```    }],

    "algo": "verus",

### Python    "threads": 8

  },

```python  "required_files": ["ccminer"]

import requests}

```

class MiningAPI:

    def __init__(self, base_url='http://localhost:9098'):### CLI String (astrominer):

        self.base = base_url```json

    {

    def get_status(self):  "coin_name": "dero",

        return requests.get(f'{self.base}/api/status').json()  "mining_tool": "astrominer",

      "config": "-w WALLET -r pool.com:10300 -m 8",

    def update_config(self, config):  "required_files": ["astrominer"]

        return requests.post(}

            f'{self.base}/api/update-config',```

            json=config

        ).json()---

    

    def start_miner(self, name):## 🛠️ Configuration (config.py)

        return requests.post(

            f'{self.base}/api/start',```python

            json={'name': name}# Server

        ).json()SERVER_HOST = '0.0.0.0'

```SERVER_PORT = 9098



---# Logging

ENABLE_FLASK_ACCESS_LOGS = False  # Tắt "GET /api/status" logs

## 🎯 Typical WorkflowENABLE_MONITOR_LOGS = True        # Periodic status logs

ENABLE_DEBUG_LOGS = False

```

1. Client Boot# Auto-Start

   ↓AUTO_START_ON_BOOT = True  # Global auto-start on server boot

   GET /api/status → {last_sync_config: 1730042400}```

   ↓

   Compare với local timestamp---

   ↓

   Nếu server cũ → POST /api/update-config## 📱 Client Integration



2. Monitor (mỗi 10s)### Kotlin/Android:

   ↓```kotlin

   GET /api/status → {miners: [{hash_rate: 50500000, ...}]}data class MiningConfig(

   ↓    val last_sync_config: Long,  // Unix timestamp

   Format & Display    val auto_start: Boolean,

    val miners: List<MinerConfig>

3. User thay đổi config)

   ↓

   POST /api/update-config với timestamp mớisuspend fun syncConfig(localTimestamp: Long, localConfig: MiningConfig) {

   ↓    val serverStatus = apiService.getStatus()

   Server auto-restart miners (nếu auto_start=true)    

```    if (serverStatus.last_sync_config < localTimestamp) {

        // Push local config to server

---        val newConfig = localConfig.copy(

            last_sync_config = System.currentTimeMillis() / 1000

## 🔧 Config Examples        )

        apiService.updateConfig(newConfig)

### JSON Config (ccminer):    }

```json}

{```

  "coin_name": "vrsc",

  "mining_tool": "ccminer",### JavaScript/React:

  "config": {```typescript

    "pools": [{"url": "stratum+tcp://pool:3956", "user": "WALLET"}],const syncConfig = async (localTimestamp: number, localConfig: Config) => {

    "algo": "verus",  const serverStatus = await fetch('/api/status').then(r => r.json());

    "threads": 8  

  },  if (serverStatus.last_sync_config < localTimestamp) {

  "required_files": ["ccminer"]    await fetch('/api/update-config', {

}      method: 'POST',

```      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify({

### CLI String (astrominer):        last_sync_config: Math.floor(Date.now() / 1000),

```json        auto_start: true,

{        miners: localConfig.miners

  "coin_name": "dero",      })

  "mining_tool": "astrominer",    });

  "config": "-w WALLET -r pool:10300 -m 8",  }

  "required_files": ["astrominer"]};

}```

```

---

---

## 🎯 Typical Workflow

## 🚨 Troubleshooting

### 1. Client khởi động:

```bash```

# Check server statusClient → GET /api/status

curl http://localhost:9098/api/status       ← {last_sync_config: 1730042400, auto_start: true, miners: [...]}

       

# Force updateClient: So sánh với local timestamp

curl -X POST http://localhost:9098/api/update-config \        → Nếu server cũ hơn → Push config mới

  -H "Content-Type: application/json" \```

  -d '{"last_sync_config": 1730050000, "auto_start": true, "miners": [...]}'

### 2. Update config từ client:

# Emergency stop```

curl -X POST http://localhost:9098/api/force-stop-allClient → POST /api/update-config

```         {last_sync_config: 1730050000, auto_start: true, miners: [...]}

       

---Server: Stop all miners → Update → Start all (nếu auto_start=true)

       ← {success: true, auto_start_result: {...}}

## 📚 API Summary```



| Endpoint | Method | Purpose |### 3. Monitor hash rate:

|----------|--------|---------|```

| `/api/status` | GET | Lấy trạng thái + timestamp |Client → GET /api/status (mỗi 10 giây)

| `/api/update-config` | POST | Update + auto-restart |       ← {miners: [{hash_rate: 50500000, status: "running"}]}

| `/api/start` | POST | Start miner |       

| `/api/stop` | POST | Stop miner |Client: Format 50500000 H/s → "50.50 MH/s"

| `/api/force-stop-all` | POST | Emergency stop |```



------



## 📄 License## 🚨 Troubleshooting



MIT License### Server không start:

```bash

## 🎉 Credits# Check port

netstat -ano | findstr :9098  # Windows

**ndduoc1189** - https://github.com/ndduoc1189/dndvina-mininglsof -i :9098                 # Linux


# Remove PID lock
rm mining_manager.pid         # Linux
del mining_manager.pid        # Windows
```

### Config không sync:
```bash
# Check server status
curl http://localhost:9098/api/status

# Force update
curl -X POST http://localhost:9098/api/update-config \
  -H "Content-Type: application/json" \
  -d '{"last_sync_config": 1730050000, "auto_start": true, "miners": [...]}'
```

### Miners không auto-start:
```bash
# Check global flag
curl http://localhost:9098/api/status | grep auto_start

# Manual trigger
curl -X POST http://localhost:9098/api/start \
  -d '{"name": "vrsc"}'
```

---

## 📚 API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/status` | GET | Lấy trạng thái + last_sync_config |
| `/api/update-config` | POST | Update config + auto-restart |
| `/api/start` | POST | Start miner thủ công |
| `/api/stop` | POST | Stop miner thủ công |
| `/api/force-stop-all` | POST | Emergency stop tất cả |

---

## 📄 License

MIT License - Free to use

## 🎉 Credits

Developed by **ndduoc1189**

GitHub: https://github.com/ndduoc1189/dndvina-mining

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

# Chạy với auto-restart (recommended)
chmod +x run.sh
./run.sh

# Hoặc chạy trực tiếp một lần
chmod +x start.sh
./start.sh

# Hoặc chạy với systemd (nếu đã cài)
sudo systemctl start mining-manager
```

**Lưu ý quan trọng:**
- Script tự động `cd` vào đúng thư mục, có thể chạy từ bất kỳ đâu:
  ```bash
  # Chạy từ thư mục khác vẫn OK
  bash ~/dndvina-mining/run.sh
  bash /opt/dndvina-mining/run.sh
  ```

## 📁 Cấu trúc deployment

```
dndvina-mining/
├── app.py                 # Server chính (Flask API + Mining Manager)
├── config.py              # Cấu hình tập trung (logs, server, timeouts)
├── requirements.txt       # Dependencies
├── README.md             # Documentation  
├── .gitignore           # Git ignore file
├── start_server.bat     # Windows start script
├── start.sh            # Linux quick start (single run)
├── run.sh              # Linux auto-restart script
├── install.sh          # Linux install script
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

#### Request Body (Array of Coin Configs)

```json
[
  {
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
    "required_files": ["ccminer"],
    "auto_start": false
  },
  {
    "coin_name": "dero",
    "mining_tool": "astrominer",
    "config": "-w deroi1qyzlxxgq2weyqlxg5u4tkng2lf5rktwanqhse2hwm577ps22zv2x2q9pvfz92 -r dero.rabidmining.com:10300 -m 8",
    "required_files": ["astrominer"],
    "auto_start": true
  }
]
```

**Required Fields per Coin:**
- `coin_name`: String - **Coin identifier used as miner name** (vrsc, dero, eth, etc.)
- `mining_tool`: String - Mining software (ccminer, astrominer, xmrig, etc.)
- `config`: Object | String - **Mining config (JSON object or CLI string)**
- `required_files`: Array - Files to download from CDN
- `auto_start`: Boolean - Enable auto-start on boot (default: false)

**Config Types:**
1. **JSON Object** - For tools supporting config files (ccminer, xmrig):
   ```json
   "config": {"pools": [...], "user": "...", "algo": "verus"}
   ```

2. **CLI String** - For tools using command-line args (astrominer):
   ```json
   "config": "-w WALLET -r POOL:PORT -m 8"
   ```

#### Response
```json
{
  "success": true,
  "updated": 2,
  "total": 2,
  "results": [
    {
      "coin_name": "vrsc",
      "success": true,
      "message": "Cập nhật cấu hình thành công"
    },
    {
      "coin_name": "dero",
      "success": true,
      "message": "Cập nhật cấu hình thành công"
    }
  ]
}
```

**Partial Success Response:**
```json
{
  "success": true,
  "updated": 1,
  "total": 2,
  "results": [
    {
      "coin_name": "vrsc",
      "success": false,
      "message": "Thiếu các trường bắt buộc: config"
    },
    {
      "coin_name": "dero",
      "success": true,
      "message": "Cập nhật cấu hình thành công"
    }
  ]
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
  "name": "vrsc"
}
```

#### Response - Success
```json
{
  "success": true,
  "message": "Bắt đầu đào vrsc thành công",
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
  "name": "vrsc"
}
```

#### Request Body - Multiple Miners
```json
{
  "names": ["vrsc", "dero", "btc"]
}
```

#### Response
```json
{
  "success": true,
  "message": "Đã dừng 3 miner(s) thành công",
  "stopped": ["vrsc", "dero", "btc"]
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
  "name": "vrsc",
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
      "name": "vrsc",
      "status": "running",
      "pid": 12345,
      "hash_rate": 50500000,
      "coin_name": "vrsc",
      "mining_tool": "ccminer",
      "auto_start": true
    },
    {
      "success": true,
      "name": "dero",
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

**⚠️ Lưu ý quan trọng:**
- API **KHÔNG** tính tổng hash rate (`totalHashRate`)
- Mỗi miner đào coin khác nhau → hash rate không thể cộng lại
- VD: 50 MH/s VRSC + 1 KH/s DERO không có ý nghĩa
- Client tự quyết định hiển thị từng miner riêng lẻ

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
      "name": "vrsc",
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

### 9️⃣ Server Info & Debug Endpoints

#### 9.1 Lấy thông tin server
**GET** `/api/server/info`

##### Response
```json
{
  "success": true,
  "server_pid": 12345,
  "uptime_seconds": 3600,
  "cpu_percent": 0.5,
  "memory_mb": 125.4,
  "num_threads": 8,
  "config": {
    "host": "0.0.0.0",
    "port": 9098,
    "auto_start_enabled": true,
    "monitor_logs_enabled": true
  }
}
```

#### 9.2 Xem raw output của miner
**GET** `/api/debug/output/{miner_name}`

##### Response
```json
{
  "success": true,
  "name": "dero",
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
# 1. Update config (JSON config type)
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
      "required_files": ["ccminer"],
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

### Example 2: Setup DERO Mining (CLI String)
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

### Example 2b: Setup Multiple Coins at Once
```bash
curl -X POST http://localhost:9098/api/update-config \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "vrsc-gpu1",
      "coin_name": "vrsc",
      "mining_tool": "ccminer",
      "config": {"pools": [...], "user": "...", "algo": "verus"},
      "required_files": ["ccminer"],
      "auto_start": true
    },
    {
      "name": "dero-cpu",
      "coin_name": "dero",
      "mining_tool": "astrominer",
      "config": "-w WALLET -r POOL:PORT -m 8",
      "required_files": ["astrominer"],
      "auto_start": true
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
    
    print("\n" + "="*60)
    print("MINING STATUS")
    print("="*60)
    
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
            
            # Show each miner separately - DON'T sum different coins
            print(f"[{miner['coin_name'].upper()}] {miner['name']}")
            print(f"  Hash Rate: {hr_str}")
            print(f"  Tool: {miner['mining_tool']}")
            print(f"  PID: {miner['pid']}")
            print()
    
    # ❌ WRONG: Don't do this
    # total_hash = sum(m['hash_rate'] for m in res['miners'] if m['status'] == 'running')
    # Different coins, can't sum!
    
    time.sleep(10)
```

**Output:**
```
============================================================
MINING STATUS
============================================================
[VRSC] vrsc-gpu1
  Hash Rate: 50.50 MH/s
  Tool: ccminer
  PID: 12345

[DERO] dero-miner
  Hash Rate: 1.08 KH/s
  Tool: astrominer
  PID: 12346
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

# 4. Start with auto-restart
chmod +x run.sh
./run.sh

# Or start with systemd (recommended for production)
sudo systemctl start mining-manager
sudo systemctl enable mining-manager  # Auto-start on boot
```

**Alternative: Run from anywhere**
```bash
# Script tự động cd vào đúng thư mục
bash ~/dndvina-mining/run.sh
bash /opt/dndvina-mining/run.sh

# Quick start (single run, no auto-restart)
bash ~/dndvina-mining/start.sh
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
✅ **Single Instance** - PID lock đảm bảo chỉ chạy 1 server duy nhất  
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

**Lỗi: "Ứng dụng đang chạy!"**
```bash
⚠️  CẢNH BÁO: Ứng dụng đang chạy!
PID: 12345
```

**Giải pháp:**
```bash
# Option 1: Kill process đang chạy
kill 12345              # Linux
taskkill /F /PID 12345  # Windows

# Option 2: Xóa PID lock nếu process đã chết
rm mining_manager.pid   # Linux
del mining_manager.pid  # Windows

# Check server info
curl http://localhost:9098/api/server/info
```

**Port conflict:**
```bash
# Check port 9098
netstat -ano | findstr :9098  # Windows
lsof -i :9098                 # Linux

# Check logs
cat server.log               # Ubuntu
type server.log              # Windows
```

### Ctrl+C không hoạt động
**Expected behavior:**
```bash
^C

🛑 Stopping server...
✅ Stopped miners: vrsc-main, dero-cpu
✅ Server stopped
```

**Nếu server không phản hồi:**
```bash
# Linux
killall python3
# hoặc
ps aux | grep app.py
kill -9 <PID>

# Windows
taskkill /F /IM python.exe
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