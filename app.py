from flask import Flask, request, jsonify
import json
import subprocess
import threading
import time
import os
import signal
import psutil
from datetime import datetime
import re
import requests
import hashlib
from urllib.parse import urlparse
import logging
import sys

# Import configuration
import config

# Configure Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Disable Flask access logs if configured
if not config.ENABLE_FLASK_ACCESS_LOGS:
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Only show errors, not requests

# Helper function to convert timestamp to Unix timestamp
def to_unix_timestamp(timestamp_value):
    """Convert ISO string or Unix timestamp to Unix timestamp (seconds)"""
    if timestamp_value is None:
        return int(datetime(2025, 1, 1).timestamp())  # Default: 2025-01-01
    
    # If already a number, return as is
    if isinstance(timestamp_value, (int, float)):
        return int(timestamp_value)
    
    # If string, try to parse
    if isinstance(timestamp_value, str):
        try:
            # Try parsing ISO format
            dt = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
            return int(dt.timestamp())
        except:
            # Default if parsing fails
            return int(datetime(2025, 1, 1).timestamp())
    
    return int(datetime(2025, 1, 1).timestamp())

class MiningManager:
    def __init__(self):
        self.miners = {}
        self.config_file = "mining_config.json"
        self.base_download_url = config.CDN_BASE_URL + "/"
        self.miners_dir = config.MINERS_DIR
        self.auto_start_enabled = config.AUTO_START_ON_BOOT
        self.last_sync_config = int(datetime(2025, 1, 1).timestamp())  # Default to oldest timestamp
        self.load_config()
        
        # Ensure miners directory exists
        if not os.path.exists(self.miners_dir):
            os.makedirs(self.miners_dir)
    
    # ==================== Logging Helper Methods ====================
    def log_info(self, message):
        """Log application info if enabled"""
        if config.ENABLE_APP_LOGS:
            print(message)
    
    def log_monitor(self, message):
        """Log monitor status if enabled"""
        if config.ENABLE_MONITOR_LOGS:
            print(message)
    
    def log_debug(self, message):
        """Log debug info if enabled"""
        if config.ENABLE_DEBUG_LOGS:
            print(message)
        
    def load_config(self):
        """Load mining configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Support new format: {last_sync_config, auto_start, miners}
                    if isinstance(data, dict) and 'miners' in data:
                        # Convert to Unix timestamp
                        self.last_sync_config = to_unix_timestamp(data.get('last_sync_config'))
                        self.auto_start_enabled = data.get('auto_start', config.AUTO_START_ON_BOOT)
                        self.miners = data.get('miners', {})
                    else:
                        # Old format: direct miners object - set oldest timestamp to trigger update
                        self.miners = data
                        self.last_sync_config = int(datetime(2025, 1, 1).timestamp())
            except Exception as e:
                self.log_info(f"Lỗi khi tải config: {e}")
                self.miners = {}
                self.last_sync_config = int(datetime(2025, 1, 1).timestamp())
        else:
            self.miners = {}
            self.last_sync_config = int(datetime(2025, 1, 1).timestamp())
    
    def save_config(self):
        """Save mining configuration to file in new format"""
        try:
            # Ensure last_sync_config is Unix timestamp
            timestamp = self.last_sync_config if isinstance(self.last_sync_config, (int, float)) else int(datetime(2025, 1, 1).timestamp())
            
            # Clean miners data - remove runtime fields that can't be serialized
            clean_miners = {}
            for name, miner in self.miners.items():
                clean_miner = {
                    'coin_name': miner.get('coin_name'),
                    'mining_tool': miner.get('mining_tool'),
                    'coin_dir': miner.get('coin_dir'),
                    'config_file': miner.get('config_file'),
                    'config': miner.get('config'),
                    'cmd': miner.get('cmd', ''),
                    'required_files': miner.get('required_files', []),
                    # Skip runtime fields: process, pid, status, hash_rate, etc.
                }
                # Add status as stopped (will be set to running when started)
                clean_miner['status'] = 'stopped'
                clean_miner['process'] = None
                clean_miner['pid'] = None
                clean_miner['start_time'] = None
                clean_miner['hash_rate'] = 0
                clean_miner['last_output'] = ''
                
                clean_miners[name] = clean_miner
            
            config_data = {
                'last_sync_config': int(timestamp),
                'auto_start': self.auto_start_enabled,
                'miners': clean_miners
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu config: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def download_file(self, filename, coin_dir):
        """Download mining file from CDN"""
        try:
            url = self.base_download_url + filename
            file_path = os.path.join(coin_dir, filename)
            
            # Skip if file already exists
            if os.path.exists(file_path):
                print(f"Tập tin {filename} đã tồn tại, bỏ qua tải xuống")
                # Make sure it's executable on Linux
                if os.name == 'posix' and not filename.endswith('.dll'):
                    os.chmod(file_path, 0o755)
                return True
            
            print(f"Đang tải xuống {filename} từ {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            os.makedirs(coin_dir, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Make executable on Linux (except for .dll files)
            if os.name == 'posix' and not filename.endswith('.dll'):
                os.chmod(file_path, 0o755)
                print(f"Đã cấp quyền thực thi cho {filename}")
            
            print(f"Tải xuống {filename} thành công")
            return True
            
        except Exception as e:
            print(f"Lỗi khi tải xuống {filename}: {e}")
            return False
    
    def setup_coin_environment(self, coin_name, mining_tool, required_files):
        """Setup mining environment for a specific coin"""
        try:
            coin_dir = os.path.join(self.miners_dir, coin_name)
            
            # Download required files
            for filename in required_files:
                if not self.download_file(filename, coin_dir):
                    return False, f"Không thể tải xuống {filename}"
            
            # Make executable files executable (for mining tools)
            mining_exe = os.path.join(coin_dir, f"{mining_tool}.exe")
            if os.path.exists(mining_exe):
                # On Windows, this is not needed but we can check if file exists
                pass
            
            return True, coin_dir
            
        except Exception as e:
            return False, str(e)
    
    def update_miner_config(self, name, coin_name, mining_tool, config, required_files=None):
        """Update miner configuration with auto-download support"""
        try:
            # Check if miner exists and is running - stop it first
            if name in self.miners and self.miners[name].get('status') == 'running':
                print(f"[CẬP NHẬT] Miner {name} đang chạy, dừng lại để cập nhật...")
                stop_result = self.stop_miner(name)
                if stop_result['success']:
                    print(f"[CẬP NHẬT] Đã dừng {name} thành công")
                else:
                    print(f"[CẬP NHẬT] Không thể dừng {name}: {stop_result['message']}")
                    # Continue with config update anyway
            
            # Default required files based on mining tool
            if required_files is None:
                required_files = self.get_default_files(mining_tool)
            
            # Setup coin environment and download files
            success, result = self.setup_coin_environment(coin_name, mining_tool, required_files)
            if not success:
                return False, result
            
            coin_dir = result
            
            # Create config file path
            config_file = os.path.join(coin_dir, "config.json")
            
            # Store absolute paths but don't create command yet (will be created in start_miner)
            mining_exe = os.path.join(coin_dir, f"{mining_tool}.exe")
            
            self.miners[name] = {
                'coin_name': coin_name,
                'mining_tool': mining_tool,
                'coin_dir': os.path.abspath(coin_dir),
                'config_file': os.path.abspath(config_file),
                'config': config,
                'cmd': '',  # Will be set dynamically in start_miner
                'status': 'stopped',
                'process': None,
                'pid': None,
                'start_time': None,
                'hash_rate': 0,
                'last_output': '',
                'required_files': required_files
            }
            
            config_saved = self.save_config()
            
            # Config updated - user needs to call /api/start to run the miner
            return config_saved, "Cập nhật cấu hình thành công"
            
        except Exception as e:
            return False, str(e)
    
    def get_default_files(self, mining_tool):
        """Get default required files for different mining tools"""
        default_files = {
            'ccminer': ['ccminer.exe', 'libcrypto-1_1-x64.dll'],  # Windows version
            'xmrig': ['xmrig.exe']
        }
        
        # For Linux, we might need different files
        if os.name == 'posix':  # Linux/Unix
            linux_files = {
                'ccminer': ['ccminer'],
                'xmrig': ['xmrig']
            }
            return linux_files.get(mining_tool.lower(), [mining_tool])
        
        # Windows default
        return default_files.get(mining_tool.lower(), [f'{mining_tool}.exe'])
    
    def auto_start_miners(self):
        """Auto-start ALL miners if global auto_start is enabled"""
        if not self.auto_start_enabled:
            print("Tự động khởi động đã bị vô hiệu hóa toàn cục")
            return
        
        # Auto-start ALL miners (no per-miner auto_start flag)
        stopped_miners = []
        for name, miner in self.miners.items():
            if miner.get('status') == 'stopped':
                stopped_miners.append(name)
        
        if stopped_miners:
            print(f"Tự động khởi động TẤT CẢ {len(stopped_miners)} miners: {stopped_miners}")
            for name in stopped_miners:
                result = self.start_miner(name)
                if result['success']:
                    print(f"✅ Đã tự động khởi động {name}")
                else:
                    print(f"❌ Không thể tự động khởi động {name}: {result['message']}")
                time.sleep(2)  # Delay between starts
        else:
            print("Không có miner nào cần tự động khởi động (tất cả đã chạy hoặc chưa config)")
    
    def set_auto_start_global(self, enabled):
        """Enable/disable auto-start globally"""
        self.auto_start_enabled = enabled
        return True
    
    def start_miner(self, name):
        """Start a mining process"""
        if name not in self.miners:
            return {'success': False, 'message': f'Miner {name} không tồn tại'}
        
        miner = self.miners[name]
        
        if miner['status'] == 'running':
            return {'success': False, 'message': f'Miner {name} đã đang chạy'}
        
        try:
            # Write config to file or prepare command args
            config_is_json = isinstance(miner['config'], dict)
            
            if config_is_json:
                # Traditional JSON config file approach
                if miner['config_file'] and miner['config']:
                    config_dir = os.path.dirname(miner['config_file'])
                    if config_dir and not os.path.exists(config_dir):
                        os.makedirs(config_dir)
                    
                    with open(miner['config_file'], 'w', encoding='utf-8') as f:
                        json.dump(miner['config'], f, indent=2)
                
                # Prepare command with config file
                coin_dir = miner.get('coin_dir')
                if not coin_dir or not os.path.exists(coin_dir):
                    return {'success': False, 'message': f'Thư mục coin không tồn tại: {coin_dir}'}
                
                # Use mining tool name directly (without .exe extension)
                mining_tool = miner.get('mining_tool', 'ccminer')
                mining_exe = os.path.abspath(os.path.join(coin_dir, mining_tool))
                config_file = os.path.abspath(miner['config_file'])
                
                # Check if executable exists (try with and without .exe for cross-platform)
                if not os.path.exists(mining_exe):
                    # Try with .exe extension for Windows
                    mining_exe_win = mining_exe + '.exe'
                    if os.path.exists(mining_exe_win):
                        mining_exe = mining_exe_win
                    else:
                        return {'success': False, 'message': f'File thực thi mining không tồn tại: {mining_exe} hoặc {mining_exe_win}'}
                
                if not os.path.exists(config_file):
                    return {'success': False, 'message': f'File config không tồn tại: {config_file}'}
                
                # Create command with config file
                cmd = f'"{mining_exe}" -c "{config_file}"'
                
            else:
                # Command line parameters approach (config is a string)
                coin_dir = miner.get('coin_dir')
                if not coin_dir or not os.path.exists(coin_dir):
                    return {'success': False, 'message': f'Thư mục coin không tồn tại: {coin_dir}'}
                
                # Use mining tool name directly (without .exe extension)
                mining_tool = miner.get('mining_tool', 'ccminer')
                mining_exe = os.path.abspath(os.path.join(coin_dir, mining_tool))
                
                # Check if executable exists (try with and without .exe for cross-platform)
                if not os.path.exists(mining_exe):
                    # Try with .exe extension for Windows
                    mining_exe_win = mining_exe + '.exe'
                    if os.path.exists(mining_exe_win):
                        mining_exe = mining_exe_win
                    else:
                        return {'success': False, 'message': f'File thực thi mining không tồn tại: {mining_exe} hoặc {mining_exe_win}'}
                
                # Create command with parameters
                config_params = str(miner['config']).strip()
                cmd = f'"{mining_exe}" {config_params}'
            
            print(f"Đang khởi động miner {name}...")
            print(f"  Thư mục làm việc: {coin_dir}")
            print(f"  Lệnh: {cmd}")
            print(f"  Loại cấu hình: {'Tập tin JSON' if config_is_json else 'Tham số dòng lệnh'}")
            
            # Start mining process
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=coin_dir  # Set working directory to coin directory
            )
            
            miner['process'] = process
            miner['pid'] = process.pid
            miner['status'] = 'running'
            miner['start_time'] = time.time()  # Use timestamp for uptime calculation
            miner['latest_output'] = ''
            
            # Debug: Check if process is actually running
            time.sleep(0.5)  # Wait a bit for process to start
            if process.poll() is not None:
                print(f"[LỖI] Process {name} died immediately after start! Return code: {process.returncode}")
                # Try to read any error output
                try:
                    error_output = process.stdout.read()
                    if error_output:
                        print(f"[LỖI] Error output: {error_output}")
                except:
                    pass
                return {'success': False, 'message': f'Process died immediately with code {process.returncode}'}
            
            print(f"[DEBUG] Process {name} started successfully with PID {process.pid}")
            
            # Special check for astrominer - verify it's actually running
            if miner.get('mining_tool', '').lower() == 'astrominer':
                time.sleep(2)  # Wait a bit more for astrominer to initialize
                try:
                    proc = psutil.Process(process.pid)
                    children = proc.children(recursive=True)
                    print(f"[DEBUG] Astrominer process tree:")
                    print(f"[DEBUG]   Parent PID {process.pid}: {proc.name()} - Status: {proc.status()}")
                    for child in children:
                        try:
                            print(f"[DEBUG]   Child PID {child.pid}: {child.name()} - Status: {child.status()}")
                        except:
                            pass
                except Exception as e:
                    print(f"[DEBUG] Error checking astrominer process: {e}")
            
            # Start monitoring thread
            thread = threading.Thread(target=self._monitor_miner, args=(name,))
            thread.daemon = True
            thread.start()
            
            return {'success': True, 'message': f'Miner {name} started', 'pid': process.pid}
            
        except Exception as e:
            miner['status'] = 'error'
            return {'success': False, 'message': f'Không thể khởi động miner {name}: {str(e)}'}
    
    def kill_all_miners_by_name(self, process_names=None):
        """Kill all mining processes by process name (brute force)"""
        if process_names is None:
            # Get all mining tools from current miners configuration
            process_names = set()
            for miner in self.miners.values():
                mining_tool = miner.get('mining_tool', '')
                if mining_tool:
                    # Only add the mining tool name (no .exe extension)
                    process_names.add(mining_tool)
            
            # If no miners configured, use common mining tools as fallback
            if not process_names:
                process_names = {'ccminer', 'xmrig'}
        
        killed_count = 0
        found_processes = []
        
        try:
            # Step 1: Find all matching processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower()
                    
                    # Check if process name matches any mining process
                    for mining_name in process_names:
                        if mining_name.lower() in proc_name or proc_name == mining_name.lower():
                            print(f"[KILL-ALL] Found mining process: {proc.info['name']} (PID: {proc.info['pid']})")
                            found_processes.append(proc)
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if not found_processes:
                print("[KILL-ALL] No mining processes found")
                return 0
            
            # Step 2: Send multiple SIGINT (Ctrl+C) to handle confirmation prompts
            import signal
            print(f"[KILL-ALL] Sending multiple SIGINT to {len(found_processes)} mining processes...")
            all_processes = []
            
            for proc in found_processes:
                try:
                    # Collect all processes including children
                    children = proc.children(recursive=True)
                    all_processes.extend([proc] + children)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    all_processes.append(proc)
            
            # Send multiple SIGINT signals to handle tools that prompt for confirmation
            for attempt in range(3):  # 3 attempts to handle y/n prompts
                for proc in all_processes:
                    try:
                        proc.send_signal(signal.SIGINT)
                        if attempt == 0:
                            print(f"[KILL-ALL] Sent SIGINT attempt {attempt + 1} to {proc.name()} (PID: {proc.pid})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Progressive delays
                if attempt == 0:
                    time.sleep(2)  # Wait for initial prompt
                elif attempt == 1:
                    time.sleep(1)  # Quick response to confirmation
                elif attempt == 2:
                    time.sleep(1)  # Final confirmation
            
            # Step 3: Wait for graceful shutdown after multiple SIGINT
            if all_processes:
                print(f"[KILL-ALL] Waiting for graceful shutdown after multiple SIGINT...")
                gone, still_alive = psutil.wait_procs(all_processes, timeout=6)
                print(f"[KILL-ALL] After multiple SIGINT: {len(gone)} stopped, {len(still_alive)} still alive")
                killed_count += len(gone)
            
            # Step 4: SIGTERM for remaining processes
            if still_alive:
                print(f"[KILL-ALL] Sending SIGTERM to {len(still_alive)} remaining processes...")
                for proc in still_alive:
                    try:
                        proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Wait after SIGTERM
                gone, still_alive = psutil.wait_procs(still_alive, timeout=5)
                print(f"[KILL-ALL] After SIGTERM: {len(gone)} stopped, {len(still_alive)} still alive")
                killed_count += len(gone)
            
            # Step 5: Force kill remaining processes
            if still_alive:
                print(f"[KILL-ALL] Force killing {len(still_alive)} remaining processes...")
                for proc in still_alive:
                    try:
                        proc.kill()
                        killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
            # Step 6: Special handling for stubborn astrominer processes
            for mining_name in process_names:
                if mining_name.lower() == 'astrominer':
                    print("[KILL-ALL] Special astrominer cleanup...")
                    time.sleep(2)
                    
                    # Find any remaining astrominer processes
                    remaining_astrominer = []
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if 'astrominer' in proc.info['name'].lower():
                                remaining_astrominer.append(proc)
                        except:
                            pass
                    
                    if remaining_astrominer:
                        print(f"[KILL-ALL] Found {len(remaining_astrominer)} stubborn astrominer processes")
                        for proc in remaining_astrominer:
                            try:
                                print(f"[KILL-ALL] Force killing stubborn astrominer PID {proc.pid}")
                                proc.kill()
                                killed_count += 1
                                
                                # Also use system command as backup
                                import subprocess
                                import os
                                if os.name == 'nt':  # Windows
                                    subprocess.run(f"taskkill /PID {proc.pid} /T /F", shell=True, capture_output=True)
                                else:
                                    subprocess.run(f"kill -9 {proc.pid}", shell=True, capture_output=True)
                            except Exception as e:
                                print(f"[KILL-ALL] Error killing stubborn astrominer {proc.pid}: {e}")
                    break
                    
        except Exception as e:
            print(f"[KILL-ALL] Lỗi trong kill_all_miners_by_name: {e}")
        
        print(f"[KILL-ALL] Total processes handled: {killed_count}")
        return killed_count

    def get_active_mining_tools(self):
        """Get list of active mining tools from current miners"""
        tools = set()
        for miner in self.miners.values():
            mining_tool = miner.get('mining_tool', '')
            if mining_tool and miner.get('status') == 'running':
                tools.add(mining_tool)
        return list(tools)

    def monitor_miners(self):
        """Monitor mining processes and output status periodically"""
        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                active_miners = []
                for name, miner in self.miners.items():
                    if miner['status'] == 'running' and miner['pid']:
                        try:
                            proc = psutil.Process(miner['pid'])
                            if proc.is_running():
                                # Don't override hash_rate here, let the _monitor_miner thread handle it
                                # hash_rate is already being updated in real-time by _monitor_miner
                                
                                active_miners.append({
                                    'name': name,
                                    'coin': miner.get('coin_name', ''),
                                    'tool': miner.get('mining_tool', ''),
                                    'hash_rate': miner.get('hash_rate', 0),
                                    'pid': miner['pid'],
                                    'uptime': time.time() - miner.get('start_time', time.time())
                                })
                            else:
                                # Process died, update status
                                miner['status'] = 'stopped'
                                miner['pid'] = None
                                miner['hash_rate'] = 0
                                print(f"[THEO DÕI] Miner {name} đã dừng, reset trạng thái về stopped")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            # Process no longer exists
                            miner['status'] = 'stopped'
                            miner['pid'] = None
                            miner['hash_rate'] = 0
                            self.log_monitor(f"[THEO DÕI] Không tìm thấy tiến trình miner {name}, reset trạng thái về stopped")
                
                # Print periodic status
                if active_miners:
                    self.log_monitor(f"\n[THEO DÕI] === Trạng thái Mining ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
                    for miner in active_miners:
                        uptime_str = f"{int(miner['uptime']//3600)}h {int((miner['uptime']%3600)//60)}m"
                        hash_info = self._format_hash_rate(miner['hash_rate'])
                        self.log_monitor(f"[THEO DÕI] {miner['name']}: {miner['coin']} | {miner['tool']} | {hash_info['value']:.2f} {hash_info['unit']} | PID:{miner['pid']} | Thời gian:{uptime_str}")
                    self.log_monitor(f"[THEO DÕI] =====================================\n")
                else:
                    self.log_monitor(f"[THEO DÕI] Không có miner nào đang hoạt động lúc {time.strftime('%H:%M:%S')}")
                    
            except Exception as e:
                self.log_info(f"[THEO DÕI] Lỗi trong monitor_miners: {e}")
                time.sleep(10)

    def force_kill_process_by_pid(self, pid):
        """Force kill process using system command as fallback"""
        try:
            import subprocess
            import os
            
            # Try multiple kill methods based on OS
            if os.name == 'nt':  # Windows
                commands = [
                    f"taskkill /PID {pid} /T",           # Terminate process tree
                    f"taskkill /PID {pid} /T /F",        # Force terminate process tree
                    f"wmic process where processid={pid} delete",  # WMI delete
                ]
                check_cmd = f"tasklist /FI \"PID eq {pid}\""
            else:  # Unix/Linux
                commands = [
                    f"kill -INT {pid}",    # SIGINT first
                    f"kill -INT {pid}",    # SIGINT second time
                    f"kill -TERM {pid}",   # SIGTERM
                    f"kill -KILL {pid}"    # SIGKILL as last resort
                ]
                check_cmd = f"ps -p {pid}"
            
            for cmd in commands:
                try:
                    print(f"[FORCE-KILL] Running: {cmd}")
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    print(f"[FORCE-KILL] Result: {result.returncode}, stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}")
                    
                    # Wait a bit for process to die
                    time.sleep(2)
                    
                    # Check if process still exists after each command
                    check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
                    if os.name == 'nt':
                        # On Windows, if no output or error, process is gone
                        if not check_result.stdout.strip() or "INFO: No tasks are running" in check_result.stdout:
                            print(f"[FORCE-KILL] Tiến trình {pid} đã được kết thúc thành công với {cmd}")
                            return True
                    else:
                        # On Unix, non-zero return code means process is gone
                        if check_result.returncode != 0:
                            print(f"[FORCE-KILL] Tiến trình {pid} đã được kết thúc thành công với {cmd}")
                            return True
                    
                except subprocess.TimeoutExpired:
                    print(f"[FORCE-KILL] Command timeout: {cmd}")
                except Exception as e:
                    print(f"[FORCE-KILL] Lỗi khi chạy {cmd}: {e}")
            
            # Final check
            final_check = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            if os.name == 'nt':
                process_gone = not final_check.stdout.strip() or "INFO: No tasks are running" in final_check.stdout
            else:
                process_gone = final_check.returncode != 0
                
            if process_gone:
                print(f"[FORCE-KILL] Process {pid} is gone")
                return True
            else:
                print(f"[FORCE-KILL] Process {pid} still exists")
                return False
                
        except Exception as e:
            print(f"[FORCE-KILL] Exception in force_kill_process_by_pid: {e}")
            return False

    def stop_miner(self, name):
        """Stop a mining process"""
        if name not in self.miners:
            return {'success': False, 'message': f'Miner {name} không tồn tại'}
        
        miner = self.miners[name]
        
        if miner['status'] != 'running':
            return {'success': False, 'message': f'Miner {name} không đang chạy'}

        # Special handling for astrominer - kill immediately with brute force
        mining_tool = miner.get('mining_tool', '').lower()
        if mining_tool == 'astrominer':
            print(f"[DEBUG] Detected astrominer - using aggressive kill strategy for {name}")
            
            # Step 1: Try normal kill first
            try:
                if miner['pid']:
                    proc = psutil.Process(miner['pid'])
                    proc.kill()
                    print(f"[DEBUG] Killed astrominer parent process {miner['pid']}")
            except:
                pass
            
            # Step 2: Kill all astrominer processes by name immediately
            kill_count = self.kill_all_miners_by_name(['astrominer'])
            print(f"[DEBUG] Aggressive astrominer kill completed: {kill_count} processes")
            
            # Reset miner status
            miner['status'] = 'stopped'
            miner['process'] = None
            miner['pid'] = None
            miner['hash_rate'] = 0
            
            return {'success': True, 'message': f'Astrominer {name} force stopped'}

        try:
            if miner['pid']:
                # Try to terminate gracefully first
                try:
                    parent = psutil.Process(miner['pid'])
                    print(f"[DEBUG] Stopping miner {name} (PID: {miner['pid']})")
                    print(f"[DEBUG] Process name: {parent.name()}")
                    print(f"[DEBUG] Process status: {parent.status()}")
                    print(f"[DEBUG] Process cmdline: {parent.cmdline()}")
                    
                    # Handle permission issues - try to get children but don't fail if can't
                    children = []
                    try:
                        children = parent.children(recursive=True)
                        print(f"[DEBUG] Found {len(children)} child processes")
                    except (psutil.AccessDenied, PermissionError) as e:
                        print(f"[DEBUG] Cannot access children due to permission: {e}")
                        # Try to find children by scanning all processes
                        try:
                            for proc in psutil.process_iter(['pid', 'ppid']):
                                if proc.info['ppid'] == miner['pid']:
                                    children.append(psutil.Process(proc.info['pid']))
                            print(f"[DEBUG] Found {len(children)} children via process scan")
                        except Exception as scan_e:
                            print(f"[DEBUG] Process scan also failed: {scan_e}")
                    
                    # Step 1: Send SIGINT (Ctrl+C) multiple times to handle confirmation prompts
                    print(f"[DEBUG] Sending SIGINT (Ctrl+C) to mining process...")
                    import signal
                    
                    # Send multiple SIGINT signals to handle tools that ask for confirmation
                    for attempt in range(4):  # Increased from 2 to 4 attempts
                        try:
                            parent.send_signal(signal.SIGINT)
                            print(f"[DEBUG] Sent SIGINT attempt {attempt + 1} to parent {parent.pid}")
                            
                            for child in children:
                                try:
                                    child.send_signal(signal.SIGINT)
                                    print(f"[DEBUG] Sent SIGINT attempt {attempt + 1} to child {child.pid}")
                                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                                    print(f"[DEBUG] Không thể gửi SIGINT tới tiến trình con {child.pid}: {e}")
                            
                            # Progressive delays to handle confirmation prompts
                            if attempt == 0:
                                time.sleep(2)  # Wait for first prompt
                            elif attempt == 1:
                                time.sleep(1)  # Quick response to y/n prompt
                            elif attempt == 2:
                                time.sleep(1)  # Another quick response
                            elif attempt == 3:
                                time.sleep(1)  # Final attempt
                                
                        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                            print(f"[DEBUG] Không thể gửi SIGINT lần thử {attempt + 1}: {e}")
                    
                    # Wait for graceful shutdown after multiple SIGINT
                    print(f"[DEBUG] Waiting for graceful shutdown after multiple SIGINT...")
                    all_processes = [parent] + children
                    
                    try:
                        gone, still_alive = psutil.wait_procs(all_processes, timeout=12)
                        print(f"[DEBUG] After SIGINT: {len(gone)} processes stopped, {len(still_alive)} still alive")
                        
                        # If all processes stopped gracefully, we're done
                        if not still_alive:
                            print(f"[DEBUG] All processes stopped gracefully with SIGINT")
                            miner['status'] = 'stopped'
                            miner['process'] = None
                            miner['pid'] = None
                            miner['hash_rate'] = 0
                            print(f"[DEBUG] Miner {name} status reset to stopped")
                            return {'success': True, 'message': f'Miner {name} stopped gracefully'}
                        
                        # Update lists for next steps
                        children = [p for p in still_alive if p.pid != miner['pid']]
                        parent = None
                        for proc in still_alive:
                            if proc.pid == miner['pid']:
                                parent = proc
                                break
                                
                    except Exception as wait_e:
                        print(f"[DEBUG] Lỗi chờ tiến trình: {wait_e}")
                        # Assume they are still alive
                        still_alive = all_processes
                    
                    # Step 2: If SIGINT didn't work, use SIGTERM on remaining processes
                    if still_alive:
                        print(f"[DEBUG] Sending SIGTERM to {len(still_alive)} remaining processes...")
                        for proc in still_alive:
                            try:
                                print(f"[DEBUG] Terminating process {proc.pid} ({proc.name() if hasattr(proc, 'name') else 'unknown'})")
                                proc.terminate()
                            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                                print(f"[DEBUG] Không thể kết thúc {proc.pid}: {e}")
                        
                        # Step 3: Wait for graceful shutdown after SIGTERM
                        print(f"[DEBUG] Waiting for graceful shutdown after SIGTERM...")
                        try:
                            gone, still_alive = psutil.wait_procs(still_alive, timeout=6)
                            print(f"[DEBUG] After SIGTERM: {len(gone)} processes stopped, {len(still_alive)} still alive")
                        except Exception as wait_e:
                            print(f"[DEBUG] Lỗi chờ sau SIGTERM: {wait_e}")
                    
                    # Step 4: Force kill any remaining processes with SIGKILL
                    if still_alive:
                        print(f"[DEBUG] Force killing {len(still_alive)} remaining processes...")
                        for proc in still_alive:
                            try:
                                print(f"[DEBUG] Force killing process {proc.pid}")
                                proc.kill()
                            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                                print(f"[DEBUG] Không thể buộc kết thúc {proc.pid}: {e}")
                        
                        # Step 5: Final wait to ensure all are dead
                        try:
                            print(f"[DEBUG] Final wait for {len(still_alive)} processes...")
                            psutil.wait_procs(still_alive, timeout=3)
                        except Exception as wait_e:
                            print(f"[DEBUG] Lỗi chờ cuối cùng: {wait_e}")
                        
                except psutil.NoSuchProcess:
                    print(f"[DEBUG] Process {miner['pid']} already terminated")
                except Exception as e:
                    print(f"[DEBUG] Lỗi khi dừng tiến trình {miner['pid']}: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Try fallback kill using system commands
                    print(f"[DEBUG] Trying fallback system kill for PID {miner['pid']}")
                    if self.force_kill_process_by_pid(miner['pid']):
                        print(f"[DEBUG] Đã kết thúc thành công {miner['pid']} bằng lệnh hệ thống")
                    else:
                        print(f"[DEBUG] Không thể kết thúc {miner['pid']} ngay cả với lệnh hệ thống")
                        
                        # Last resort: kill by process name
                        print(f"[DEBUG] Last resort: killing by process name...")
                        mining_tool = miner.get('mining_tool', '')
                        if mining_tool:
                            kill_count = self.kill_all_miners_by_name([mining_tool])
                            print(f"[DEBUG] Killed {kill_count} processes by name {mining_tool}")
                            
                            # Wait a bit and check if any astrominer processes still exist
                            if mining_tool.lower() == 'astrominer':
                                time.sleep(2)
                                astrominer_procs = []
                                for proc in psutil.process_iter(['pid', 'name']):
                                    try:
                                        if 'astrominer' in proc.info['name'].lower():
                                            astrominer_procs.append(proc)
                                    except:
                                        pass
                                
                                if astrominer_procs:
                                    print(f"[DEBUG] Found {len(astrominer_procs)} remaining astrominer processes, force killing...")
                                    for proc in astrominer_procs:
                                        try:
                                            proc.kill()
                                            print(f"[DEBUG] Force killed remaining astrominer PID {proc.pid}")
                                        except:
                                            pass
            
            miner['status'] = 'stopped'
            miner['process'] = None
            miner['pid'] = None
            miner['hash_rate'] = 0
            
            print(f"[DEBUG] Miner {name} status reset to stopped")
            return {'success': True, 'message': f'Miner {name} stopped'}
            
        except Exception as e:
            print(f"[DEBUG] Không thể dừng miner {name}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Không thể dừng miner {name}: {str(e)}'}
    
    def get_miner_status(self, name):
        """Get status of a specific miner"""
        if name not in self.miners:
            return {'success': False, 'message': f'Miner {name} không tồn tại'}
        
        miner = self.miners[name]
        
        # Check if process is still running
        if miner['status'] == 'running' and miner['pid']:
            try:
                psutil.Process(miner['pid'])
            except psutil.NoSuchProcess:
                miner['status'] = 'stopped'
                miner['process'] = None
                miner['pid'] = None
                miner['hash_rate'] = 0
        
        return {
            'success': True,
            'name': name,
            'status': miner['status'],
            'pid': miner['pid'],
            'start_time': miner['start_time'],
            'hash_rate': miner['hash_rate'] * 1_000_000 if miner['hash_rate'] is not None else 0,  # Always return H/s for API
            'coin_name': miner.get('coin_name', ''),
            'mining_tool': miner.get('mining_tool', ''),
            'last_output': miner['last_output'][-1000:] if miner['last_output'] else ''  # Last 1000 chars
        }
    
    def get_all_status(self):
        """Get status of all miners"""
        status_list = []
        for name in self.miners:
            status = self.get_miner_status(name)
            if status['success']:
                status_list.append(status)
        
        return {
            'success': True,
            'last_sync_config': int(self.last_sync_config) if isinstance(self.last_sync_config, (int, float)) else int(datetime(2025, 1, 1).timestamp()),
            'auto_start': self.auto_start_enabled,  # Global auto-start flag
            'miners': status_list
        }
    
    def _monitor_miner(self, name):
        """Monitor mining process output for hash rate"""
        miner = self.miners[name]
        process = miner['process']
        
        if not process:
            return
        
        try:
            mining_tool = miner.get('mining_tool', '').lower()
            line_count = 0
            
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                line_count += 1
                
                # Debug: Print first 10 lines for astrominer to see what's happening
                if mining_tool == 'astrominer' and line_count <= 10:
                    print(f"[{name}] [DEBUG-LINE-{line_count}] {line.strip()}")
                
                # Store latest output for monitoring
                if 'latest_output' not in miner:
                    miner['latest_output'] = ''
                miner['latest_output'] += line
                
                # Keep only last 5000 characters to prevent memory issues
                if len(miner['latest_output']) > 5000:
                    miner['latest_output'] = miner['latest_output'][-5000:]
                
                # Extract hash rate from output (tool-specific patterns)
                # Different extraction logic for different tools
                line_lower = line.lower()
                tool_name = miner.get('mining_tool', '').lower()
                
                # Astrominer: extract from any line with "Hashrate"
                if tool_name == 'astrominer':
                    if 'hashrate' in line_lower:
                        hash_rate = self._extract_hash_rate(line, tool_name)
                        if hash_rate:
                            miner['hash_rate'] = hash_rate
                # CCMiner/XMRig: extract only from accepted lines
                elif 'accepted:' in line_lower or 'accepted ' in line_lower:
                    hash_rate = self._extract_hash_rate(line, tool_name)
                    if hash_rate:
                        miner['hash_rate'] = hash_rate
                
                # Print important mining output
                if any(keyword in line_lower for keyword in ['accepted', 'rejected', 'error', 'connected', 'difficulty', 'hashrate']):
                    print(f"[{name}] {line.strip()}")
                
                # Check if process is still running
                if process.poll() is not None:
                    break
            
            # Process has ended
            miner['status'] = 'stopped'
            miner['process'] = None
            miner['pid'] = None
            miner['hash_rate'] = 0
            print(f"[{name}] Tiến trình mining đã kết thúc")
            
        except Exception as e:
            print(f"[LỖI] Lỗi khi theo dõi miner {name}: {e}")
            miner['status'] = 'error'
            miner['status'] = 'error'
    
    def _format_hash_rate(self, hash_rate_mh):
        """Format hash rate with smart unit selection (KH/s, MH/s, GH/s)"""
        if hash_rate_mh is None or hash_rate_mh == 0:
            return {'value': 0, 'unit': 'H/s'}
        
        # Auto-select best unit
        if hash_rate_mh >= 1000:  # >= 1000 MH/s -> use GH/s
            return {'value': round(hash_rate_mh / 1000, 2), 'unit': 'GH/s'}
        elif hash_rate_mh >= 0.01:  # >= 0.01 MH/s -> use MH/s
            return {'value': round(hash_rate_mh, 2), 'unit': 'MH/s'}
        else:  # < 0.01 MH/s -> use KH/s
            return {'value': round(hash_rate_mh * 1000, 2), 'unit': 'KH/s'}
    
    def _extract_hash_rate(self, line, mining_tool=''):
        """Extract hash rate from miner output based on mining tool"""
        
        # Remove ANSI color codes that some miners use (like astrominer)
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_line = ansi_escape.sub('', line)
        
        # Tool-specific patterns
        if mining_tool.lower() == 'ccminer':
            # CCMiner patterns: 
            # "accepted: 7/7 (diff 436900.000), 2451.53 kH/s yes!"
            # "GPU #0: GeForce GTX 1080, 25.50 MH/s"
            patterns = [
                r'accepted:\s*\d+\/\d+\s*\(diff\s*[\d\.]+\),\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]\/s)\s*yes!',
                r'GPU #\d+:.*?(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'[Tt]otal:\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
            ]
        elif mining_tool.lower() == 'xmrig':
            # XMRig patterns: "speed 10s/60s/15m 1000.0 1000.0 1000.0 H/s"
            patterns = [
                r'speed\s+\S+\s+(\d+\.?\d*)\s+\d+\.?\d*\s+\d+\.?\d*\s*([kmgtKMGT]?[Hh]/s)',
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
            ]
        elif mining_tool.lower() == 'astrominer':
            # Astrominer patterns: 
            # "[dero] 16-10-2025 03:29:57 [dero.rabidmining.com:10300] Accepted 159 | Rejected 0 | Height 6076878 | Diff 20000 | Uptime 00:03:01 | Hashrate 0.956KH/s"
            patterns = [
                r'Hashrate\s+(\d+\.?\d*)([kmgtKMGT]?[Hh]/s)',  # Hashrate 1.179KH/s (no space before unit)
                r'hashrate\s+(\d+\.?\d*)([kmgtKMGT]?[Hh]/s)',
                r'\|\s*Hashrate\s+(\d+\.?\d*)([kmgtKMGT]?[Hh]/s)',
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
            ]
        else:
            # Generic patterns for unknown tools
            patterns = [
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'[Hh]ashrate[:\s]+(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'[Ss]peed[:\s]+(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/[Ss])',
            ]
        
        for pattern in patterns:
            match = re.search(pattern, clean_line, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    unit = match.group(2).lower() if len(match.groups()) > 1 else ''
                    
                    # Convert to MH/s for display consistency
                    if 'k' in unit:
                        value = value / 1000  # kH/s to MH/s
                    elif 'm' in unit:
                        value = value  # MH/s stays the same
                    elif 'g' in unit:
                        value = value * 1000  # GH/s to MH/s
                    elif 't' in unit:
                        value = value * 1000000  # TH/s to MH/s
                    else:
                        value = value / 1000000  # H/s to MH/s
                    
                    return value
                except Exception as e:
                    continue
        
        return None

# Global mining manager instance
mining_manager = MiningManager()

@app.route('/api/update-config', methods=['POST'])
def update_config():
    """Update mining configuration
    Expected payload (New format with wrapper object):
    {
        "last_sync_config": "2025-10-27T10:30:00Z",  // ISO timestamp or Unix timestamp
        "auto_start": true,  // Global auto-start on server boot
        "miners": [
            {
                "coin_name": "vrsc",
                "mining_tool": "ccminer",
                "config": {"pools": [...], "user": "...", "algo": "verus"},
                "required_files": ["ccminer"]
            },
            {
                "coin_name": "dero",
                "mining_tool": "astrominer",
                "config": "-w WALLET -r POOL:PORT -m 8",
                "required_files": ["astrominer"]
            }
        ]
    }
    
    Query params: ?stop_all_first=true (to stop all miners before update)
    """
    try:
        data = request.get_json()
        stop_all_first = request.args.get('stop_all_first', 'false').lower() == 'true'
        
        # Support both old format (array) and new format (object with miners array)
        if isinstance(data, dict) and 'miners' in data:
            # New format
            miners_list = data.get('miners', [])
            last_sync_config = data.get('last_sync_config')
            auto_start_global = data.get('auto_start', True)
            
            # Update global settings - convert timestamp to Unix format
            mining_manager.last_sync_config = to_unix_timestamp(last_sync_config)
            mining_manager.auto_start_enabled = auto_start_global
        elif isinstance(data, list):
            # Old format (backward compatibility)
            miners_list = data
            last_sync_config = None
        else:
            return jsonify({'success': False, 'message': 'Config phải là object với field "miners" hoặc array'}), 400
        
        # Option to stop all miners first
        if stop_all_first:
            print("[CẬP NHẬT] Đang dừng tất cả miners trước khi cập nhật cấu hình...")
            running_miners = []
            for name, miner in mining_manager.miners.items():
                if miner.get('status') == 'running':
                    running_miners.append(name)
            
            for name in running_miners:
                print(f"[CẬP NHẬT] Đang dừng {name}...")
                stop_result = mining_manager.stop_miner(name)
                if stop_result['success']:
                    print(f"[CẬP NHẬT] Đã dừng {name}")
                else:
                    print(f"[CẬP NHẬT] Không thể dừng {name}: {stop_result['message']}")
            
            if running_miners:
                print(f"[CẬP NHẬT] Đã dừng {len(running_miners)} miners, chờ 2 giây...")
                time.sleep(2)
                
                # Force kill any remaining mining processes
                print("[CẬP NHẬT] Đang kiểm tra và force kill các process mining còn lại...")
                active_tools = mining_manager.get_active_mining_tools()
                if active_tools:
                    print(f"[CẬP NHẬT] Tìm thấy các tool còn hoạt động: {active_tools}")
                    kill_result = mining_manager.kill_all_miners_by_name(active_tools)
                    print(f"[CẬP NHẬT] Kết quả force kill: {kill_result}")
                    time.sleep(3)  # Additional wait after force kill
        
        # Process each miner config
        results = []
        for miner_config in miners_list:
            # Validate required fields (use coin_name as identifier)
            required_fields = ['coin_name', 'mining_tool', 'config']
            missing_fields = [f for f in required_fields if f not in miner_config]
            
            coin_name = miner_config.get('coin_name', 'unknown')
            
            if missing_fields:
                results.append({
                    'coin_name': coin_name,
                    'success': False,
                    'message': f'Thiếu các trường bắt buộc: {", ".join(missing_fields)}'
                })
                continue
            
            # Validate config type (must be dict or string)
            config = miner_config['config']
            if not isinstance(config, (dict, str)):
                results.append({
                    'coin_name': coin_name,
                    'success': False,
                    'message': 'Field "config" phải là object (JSON) hoặc string (CLI params)'
                })
                continue
            
            success, message = mining_manager.update_miner_config(
                coin_name,  # Use coin_name as the identifier
                coin_name,
                miner_config['mining_tool'],
                config,
                miner_config.get('required_files')
            )
            
            results.append({
                'coin_name': coin_name,
                'success': success,
                'message': message
            })
        
        # Save config with new format (BEFORE auto-restart to ensure it's saved)
        config_saved = mining_manager.save_config()
        if not config_saved:
            print("[CẬP NHẬT] ⚠️ Cảnh báo: Không thể lưu config!")
        
        # Check if auto-restart is needed
        should_auto_restart = mining_manager.auto_start_enabled
        
        # Return response immediately
        response = {
            'success': True,
            'updated': len([r for r in results if r['success']]),
            'total': len(results),
            'last_sync_config': mining_manager.last_sync_config,
            'auto_start_enabled': mining_manager.auto_start_enabled,
            'results': results,
            'message': 'Config updated successfully. Auto-restart will happen in background.' if should_auto_restart else 'Config updated successfully.'
        }
        
        # Trigger auto-restart in background thread if enabled
        if should_auto_restart:
            print("[CẬP NHẬT] 🔄 auto_start=true, khởi động background thread để restart miners...")
            
            def background_restart():
                """Background thread to restart miners without blocking response"""
                try:
                    time.sleep(1)  # Small delay to ensure response is sent
                    
                    print("[BG-RESTART] Bắt đầu stop tất cả miners...")
                    # Step 1: Stop all running miners first
                    stopped_miners = []
                    for name, miner in mining_manager.miners.items():
                        if miner.get('status') == 'running':
                            print(f"[BG-RESTART] Đang dừng {name}...")
                            stop_result = mining_manager.stop_miner(name)
                            stopped_miners.append({'name': name, 'stopped': stop_result['success']})
                    
                    if stopped_miners:
                        print(f"[BG-RESTART] Đã dừng {len(stopped_miners)} miners, chờ 5 giây...")
                        time.sleep(5)  # Wait 5 seconds for clean shutdown
                        
                        # Force kill to ensure clean state
                        active_tools = mining_manager.get_active_mining_tools()
                        if active_tools:
                            kill_count = mining_manager.kill_all_miners_by_name(active_tools)
                            print(f"[BG-RESTART] Force killed {kill_count} processes")
                            time.sleep(2)
                    
                    # Step 2: Start all miners
                    print("[BG-RESTART] Đang khởi động lại tất cả miners...")
                    started_miners = []
                    for name in mining_manager.miners.keys():
                        result = mining_manager.start_miner(name)
                        started_miners.append({
                            'name': name,
                            'started': result['success'],
                            'message': result.get('message', '')
                        })
                        if result['success']:
                            print(f"[BG-RESTART] ✅ Đã khởi động {name}")
                        else:
                            print(f"[BG-RESTART] ❌ Không thể khởi động {name}: {result['message']}")
                        time.sleep(2)  # Delay between starts
                    
                    print(f"[BG-RESTART] ✅ Hoàn thành restart: {len([m for m in started_miners if m['started']])}/{len(started_miners)} miners started")
                    
                except Exception as e:
                    print(f"[BG-RESTART] ❌ Lỗi trong background restart: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Start background thread
            restart_thread = threading.Thread(target=background_restart)
            restart_thread.daemon = True
            restart_thread.start()
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_mining():
    """Start mining
    Expected payload: {"name": "miner1"} or {"names": ["miner1", "miner2"]}
    """
    try:
        data = request.get_json()
        
        if 'name' in data:
            # Start single miner
            result = mining_manager.start_miner(data['name'])
            return jsonify(result)
        elif 'names' in data:
            # Start multiple miners
            results = []
            for name in data['names']:
                result = mining_manager.start_miner(name)
                result['name'] = name
                results.append(result)
            return jsonify({'success': True, 'results': results})
        else:
            return jsonify({'success': False, 'message': 'Yêu cầu trường "name" hoặc "names"'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_mining():
    """Stop mining
    Expected payload: {"name": "miner1"} or {"names": ["miner1", "miner2"]}
    """
    try:
        data = request.get_json()
        
        if 'name' in data:
            # Stop single miner
            result = mining_manager.stop_miner(data['name'])
            return jsonify(result)
        elif 'names' in data:
            # Stop multiple miners
            results = []
            for name in data['names']:
                result = mining_manager.stop_miner(name)
                result['name'] = name
                results.append(result)
            return jsonify({'success': True, 'results': results})
        else:
            return jsonify({'success': False, 'message': 'Yêu cầu trường "name" hoặc "names"'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/force-stop-all', methods=['POST'])
def force_stop_all():
    """Force stop all mining processes - comprehensive cleanup"""
    try:
        print("[FORCE-STOP] Bắt đầu force stop tất cả mining processes...")
        
        # Step 1: Get all active tools
        active_tools = mining_manager.get_active_mining_tools()
        print(f"[FORCE-STOP] Active tools detected: {active_tools}")
        
        # Step 2: Try normal stop first
        stopped_miners = []
        for name, miner in mining_manager.miners.items():
            if miner.get('status') == 'running':
                print(f"[FORCE-STOP] Trying normal stop for {name}...")
                stop_result = mining_manager.stop_miner(name)
                stopped_miners.append({
                    'name': name,
                    'normal_stop_success': stop_result['success'],
                    'message': stop_result['message']
                })
        
        # Step 3: Wait a bit
        time.sleep(3)
        
        # Step 4: Force kill all mining processes by name
        print(f"[FORCE-STOP] Force killing all mining processes...")
        common_mining_tools = ['ccminer', 'cpuminer', 'xmrig', 'astrominer', 't-rex', 'teamredminer', 'nbminer', 'gminer']
        all_tools = list(set(active_tools + common_mining_tools))
        
        killed_count = mining_manager.kill_all_miners_by_name(all_tools)
        print(f"[FORCE-STOP] Force killed {killed_count} processes")
        
        # Step 5: Reset all miner statuses
        for miner_name in mining_manager.miners:
            miner = mining_manager.miners[miner_name]
            miner['status'] = 'stopped'
            miner['process'] = None
            miner['pid'] = None
            miner['hash_rate'] = 0
        
        print("[FORCE-STOP] Đã reset tất cả miner status")
        
        return jsonify({
            'success': True,
            'message': f'Force stopped all mining. Killed {killed_count} processes.',
            'details': {
                'stopped_miners': stopped_miners,
                'killed_count': killed_count,
                'target_tools': all_tools,
                'active_tools_before': active_tools
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/kill-all', methods=['POST'])
def kill_all_mining():
    """Force kill all mining processes by process name (brute force method)
    Expected payload: {"process_names": ["ccminer", "cpuminer"]} (optional)
    """
    try:
        data = request.get_json() or {}
        process_names = data.get('process_names', None)
        
        # Get current active mining tools before killing
        active_tools = mining_manager.get_active_mining_tools()
        
        killed_count = mining_manager.kill_all_miners_by_name(process_names)
        
        # Also reset all miner statuses
        for miner_name in mining_manager.miners:
            miner = mining_manager.miners[miner_name]
            miner['status'] = 'stopped'
            miner['process'] = None
            miner['pid'] = None
            miner['hash_rate'] = 0
        
        return jsonify({
            'success': True, 
            'message': f'Force killed {killed_count} mining processes',
            'killed_count': killed_count,
            'active_tools_before_kill': active_tools,
            'target_process_names': list(process_names) if process_names else 'auto-detected from miners'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get mining status
    Optional query params: ?name=miner1 (for specific miner)
    """
    try:
        miner_name = request.args.get('name')
        
        if miner_name:
            # Get status of specific miner
            result = mining_manager.get_miner_status(miner_name)
            return jsonify(result)
        else:
            # Get status of all miners
            result = mining_manager.get_all_status()
            return jsonify(result)
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/miners', methods=['GET'])
def list_miners():
    """List all configured miners"""
    try:
        miners = []
        for name, config in mining_manager.miners.items():
            # Generate current command for display
            coin_dir = config.get('coin_dir', '')
            mining_tool = config.get('mining_tool', 'ccminer')
            config_file = config.get('config_file', '')
            
            if coin_dir and config_file:
                # Try to find the executable (with or without .exe)
                mining_exe = os.path.abspath(os.path.join(coin_dir, mining_tool))
                if not os.path.exists(mining_exe):
                    mining_exe_win = mining_exe + '.exe'
                    if os.path.exists(mining_exe_win):
                        mining_exe = mining_exe_win
                
                display_cmd = f'"{mining_exe}" -c "{config_file}"'
            else:
                display_cmd = config.get('cmd', 'Not configured')
            
            miners.append({
                'name': name,
                'coin_name': config.get('coin_name', ''),
                'mining_tool': config.get('mining_tool', ''),
                'config_file': config.get('config_file', ''),
                'cmd': display_cmd,
                'status': config['status'],
                'auto_start': config.get('auto_start', False)
            })
        
        return jsonify({'success': True, 'miners': miners})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Mining manager is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/server/info', methods=['GET'])
def get_server_info():
    """Get server information including PID and uptime"""
    try:
        pid_file = 'mining_manager.pid'
        server_pid = None
        
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                server_pid = int(f.read().strip())
        
        # Get process info
        proc = psutil.Process(server_pid or os.getpid())
        
        return jsonify({
            'success': True,
            'server_pid': server_pid or os.getpid(),
            'uptime_seconds': time.time() - proc.create_time(),
            'cpu_percent': proc.cpu_percent(interval=0.1),
            'memory_mb': proc.memory_info().rss / 1024 / 1024,
            'num_threads': proc.num_threads(),
            'config': {
                'host': config.SERVER_HOST,
                'port': config.SERVER_PORT,
                'auto_start_enabled': config.AUTO_START_ON_BOOT,
                'monitor_logs_enabled': config.ENABLE_MONITOR_LOGS
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/debug/output/<miner_name>', methods=['GET'])
def get_miner_output(miner_name):
    """Get raw output from miner for debugging"""
    try:
        if miner_name not in mining_manager.miners:
            return jsonify({'success': False, 'message': f'Miner {miner_name} not found'}), 404
        
        miner = mining_manager.miners[miner_name]
        
        return jsonify({
            'success': True,
            'name': miner_name,
            'status': miner['status'],
            'pid': miner['pid'],
            'latest_output': miner.get('latest_output', ''),
            'last_output': miner.get('last_output', ''),
            'hash_rate': miner.get('hash_rate', 0)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auto-start', methods=['POST'])
def trigger_auto_start():
    """Manually trigger auto-start for configured miners"""
    try:
        mining_manager.auto_start_miners()
        return jsonify({
            'success': True,
            'message': 'Auto-start triggered'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auto-start/config', methods=['POST'])
def set_auto_start_config():
    """Enable/disable auto-start globally
    Expected payload: {"enabled": true/false}
    """
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        
        mining_manager.set_auto_start_global(enabled)
        
        return jsonify({
            'success': True,
            'message': f'Auto-start globally {"enabled" if enabled else "disabled"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auto-start/config', methods=['GET'])
def get_auto_start_config():
    """Get auto-start configuration"""
    try:
        auto_start_miners = []
        for name, miner in mining_manager.miners.items():
            if miner.get('auto_start', False):
                auto_start_miners.append({
                    'name': name,
                    'coin_name': miner.get('coin_name', ''),
                    'mining_tool': miner.get('mining_tool', ''),
                    'status': miner.get('status', 'stopped')
                })
        
        return jsonify({
            'success': True,
            'global_enabled': mining_manager.auto_start_enabled,
            'auto_start_miners': auto_start_miners
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    import signal
    import sys
    import atexit
    
    # PID file để đảm bảo chỉ chạy 1 instance
    PID_FILE = 'mining_manager.pid'
    
    def check_already_running():
        """Check if another instance is already running"""
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if process is still running
                try:
                    # Check if PID exists
                    proc = psutil.Process(old_pid)
                    # Check if it's actually our app
                    if 'python' in proc.name().lower() and 'app.py' in ' '.join(proc.cmdline()):
                        print("=" * 60)
                        print("⚠️  CẢNH BÁO: Ứng dụng đang chạy!")
                        print("=" * 60)
                        print(f"PID: {old_pid}")
                        print(f"Command: {' '.join(proc.cmdline())}")
                        print(f"\nĐể dừng server hiện tại:")
                        print(f"  kill {old_pid}              # Linux")
                        print(f"  taskkill /F /PID {old_pid}  # Windows")
                        print(f"\nHoặc xóa file lock nếu process đã chết:")
                        print(f"  rm {PID_FILE}")
                        print("=" * 60)
                        return True
                except psutil.NoSuchProcess:
                    # Process không tồn tại, xóa PID file cũ
                    print(f"⚠️  Tìm thấy PID file cũ (process {old_pid} đã chết), cleaning up...")
                    os.remove(PID_FILE)
            except (ValueError, IOError) as e:
                print(f"⚠️  PID file lỗi, removing: {e}")
                os.remove(PID_FILE)
        
        return False
    
    def create_pid_file():
        """Create PID file with current process ID"""
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"✅ Created PID file: {PID_FILE} (PID: {os.getpid()})")
    
    def remove_pid_file():
        """Remove PID file on exit"""
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
                print(f"🗑️  Removed PID file: {PID_FILE}")
        except Exception as e:
            print(f"⚠️  Error removing PID file: {e}")
    
    # Check if already running
    if check_already_running():
        sys.exit(1)
    
    # Create PID file
    create_pid_file()
    
    # Register cleanup
    atexit.register(remove_pid_file)
    
    # Simple signal handler
    def signal_handler(sig, frame):
        print('\n\n🛑 Stopping server...')
        # Stop all running miners
        try:
            stopped = []
            for name, miner in mining_manager.miners.items():
                if miner.get('status') == 'running':
                    mining_manager.stop_miner(name)
                    stopped.append(name)
            if stopped:
                print(f'✅ Stopped miners: {", ".join(stopped)}')
        except Exception as e:
            print(f'⚠️  Error stopping miners: {e}')
        
        # Remove PID file
        remove_pid_file()
        print('✅ Server stopped\n')
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🚀 Mining Management API Server")
    print("=" * 60)
    print(f"📡 Server URL: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    print(f"📊 Monitor Logs: {'Enabled' if config.ENABLE_MONITOR_LOGS else 'Disabled'}")
    print(f"🔍 Flask Logs: {'Enabled' if config.ENABLE_FLASK_ACCESS_LOGS else 'Disabled'}")
    print(f"🎯 Auto-Start: {'Enabled' if config.AUTO_START_ON_BOOT else 'Disabled'}")
    print("=" * 60)
    
    # Start auto-start in a separate thread after a delay
    def delayed_auto_start():
        time.sleep(5)  # Wait 5 seconds for server to fully start
        if config.AUTO_START_ON_BOOT:
            print("\n🚀 Checking for auto-start miners...")
            try:
                mining_manager.auto_start_miners()
            except Exception as e:
                print(f"Lỗi trong auto-start: {e}")
    
    # Start monitoring thread
    def start_monitoring():
        time.sleep(10)  # Wait 10 seconds before starting monitoring
        if config.ENABLE_MONITOR_LOGS:
            print("\n📊 Đang khởi động bộ giám sát mining...")
        mining_manager.monitor_miners()
    
    auto_start_thread = threading.Thread(target=delayed_auto_start)
    auto_start_thread.daemon = True
    auto_start_thread.start()
    
    monitor_thread = threading.Thread(target=start_monitoring)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try:
        app.run(
            host=config.SERVER_HOST, 
            port=config.SERVER_PORT, 
            debug=config.DEBUG_MODE
        )
    except Exception as e:
        print(f"❌ Server không thể khởi động: {e}")
        sys.exit(1)