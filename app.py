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

app = Flask(__name__)

class MiningManager:
    def __init__(self):
        self.miners = {}
        self.config_file = "mining_config.json"
        self.base_download_url = "http://cdn.dndvina.com/minings/"
        self.miners_dir = "miners"
        self.auto_start_enabled = True  # Global auto-start setting
        self.load_config()
        
        # Ensure miners directory exists
        if not os.path.exists(self.miners_dir):
            os.makedirs(self.miners_dir)
        
    def load_config(self):
        """Load mining configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.miners = json.load(f)
            except Exception as e:
                print(f"Lỗi khi tải config: {e}")
                self.miners = {}
        else:
            self.miners = {}
    
    def save_config(self):
        """Save mining configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.miners, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu config: {e}")
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
    
    def update_miner_config(self, name, coin_name, mining_tool, config, required_files=None, auto_start=False):
        """Update miner configuration with auto-download support"""
        try:
            # Check if miner exists and is running - stop it first
            need_restart = False
            if name in self.miners and self.miners[name].get('status') == 'running':
                print(f"[CẬP NHẬT] Miner {name} đang chạy, dừng lại để cập nhật...")
                stop_result = self.stop_miner(name)
                if stop_result['success']:
                    print(f"[CẬP NHẬT] Đã dừng {name} thành công")
                    need_restart = auto_start  # Only restart if auto_start is enabled
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
                'required_files': required_files,
                'auto_start': auto_start  # Add auto-start flag
            }
            
            config_saved = self.save_config()
            
            # Restart miner if it was running and auto_start is enabled
            if need_restart:
                print(f"[CẬP NHẬT] Đang khởi động lại {name} sau khi cập nhật cấu hình...")
                time.sleep(2)  # Small delay before restart
                start_result = self.start_miner(name)
                if start_result['success']:
                    print(f"[CẬP NHẬT] Đã khởi động lại {name} thành công")
                    return config_saved, f"Đã cập nhật cấu hình và khởi động lại {name} thành công"
                else:
                    print(f"[CẬP NHẬT] Không thể khởi động lại {name}: {start_result['message']}")
                    return config_saved, f"Đã cập nhật cấu hình nhưng không thể khởi động lại {name}: {start_result['message']}"
            
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
        """Auto-start miners that have auto_start enabled"""
        if not self.auto_start_enabled:
            print("Tự động khởi động đã bị vô hiệu hóa toàn cục")
            return
        
        auto_start_miners = []
        for name, miner in self.miners.items():
            if miner.get('auto_start', False) and miner.get('status') == 'stopped':
                auto_start_miners.append(name)
        
        if auto_start_miners:
            print(f"Tự động khởi động các miner: {auto_start_miners}")
            for name in auto_start_miners:
                result = self.start_miner(name)
                if result['success']:
                    print(f"✅ Đã tự động khởi động {name}")
                else:
                    print(f"❌ Không thể tự động khởi động {name}: {result['message']}")
                time.sleep(2)  # Delay between starts
        else:
            print("Không có miner nào được cấu hình để tự động khởi động")
    
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
            
            # Step 2: Send SIGINT (Ctrl+C) to all processes first
            import signal
            print(f"[KILL-ALL] Sending SIGINT to {len(found_processes)} mining processes...")
            still_alive = []
            
            for proc in found_processes:
                try:
                    proc.send_signal(signal.SIGINT)
                    print(f"[KILL-ALL] Sent SIGINT to {proc.name()} (PID: {proc.pid})")
                    
                    # Also send to children
                    children = proc.children(recursive=True)
                    for child in children:
                        try:
                            child.send_signal(signal.SIGINT)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    still_alive.extend([proc] + children)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    print(f"[KILL-ALL] Không thể gửi SIGINT tới {proc.pid}: {e}")
            
            # Step 3: Wait for graceful shutdown
            if still_alive:
                print(f"[KILL-ALL] Waiting for graceful shutdown...")
                gone, still_alive = psutil.wait_procs(still_alive, timeout=8)
                print(f"[KILL-ALL] After SIGINT: {len(gone)} stopped, {len(still_alive)} still alive")
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
                                # Update hash rate from latest output
                                hash_rate = self._extract_hash_rate(miner.get('latest_output', ''), miner.get('mining_tool', ''))
                                if hash_rate is not None and hash_rate > 0:
                                    miner['hash_rate'] = hash_rate
                                
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
                            print(f"[THEO DÕI] Không tìm thấy tiến trình miner {name}, reset trạng thái về stopped")
                
                # Print periodic status
                if active_miners:
                    print(f"\n[THEO DÕI] === Trạng thái Mining ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
                    for miner in active_miners:
                        uptime_str = f"{int(miner['uptime']//3600)}h {int((miner['uptime']%3600)//60)}m"
                        print(f"[THEO DÕI] {miner['name']}: {miner['coin']} | {miner['tool']} | {miner['hash_rate']:.2f} MH/s | PID:{miner['pid']} | Thời gian:{uptime_str}")
                    print(f"[THEO DÕI] =====================================\n")
                else:
                    print(f"[THEO DÕI] Không có miner nào đang hoạt động lúc {time.strftime('%H:%M:%S')}")
                    
            except Exception as e:
                print(f"[THEO DÕI] Lỗi trong monitor_miners: {e}")
                time.sleep(10)

    def force_kill_process_by_pid(self, pid):
        """Force kill process using system command as fallback"""
        try:
            import subprocess
            
            # Try multiple kill methods
            commands = [
                f"kill -INT {pid}",    # SIGINT first
                f"kill -INT {pid}",    # SIGINT second time
                f"kill -TERM {pid}",   # SIGTERM
                f"kill -KILL {pid}"    # SIGKILL as last resort
            ]
            
            for cmd in commands:
                try:
                    print(f"[FORCE-KILL] Running: {cmd}")
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                    print(f"[FORCE-KILL] Result: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}")
                    
                    # Check if process still exists after each command
                    check_result = subprocess.run(f"ps -p {pid}", shell=True, capture_output=True, text=True)
                    if check_result.returncode != 0:
                        print(f"[FORCE-KILL] Tiến trình {pid} đã được kết thúc thành công với {cmd}")
                        return True
                        
                    # Wait a bit before next command
                    time.sleep(2)
                    
                except subprocess.TimeoutExpired:
                    print(f"[FORCE-KILL] Command timeout: {cmd}")
                except Exception as e:
                    print(f"[FORCE-KILL] Lỗi khi chạy {cmd}: {e}")
            
            # Final check
            final_check = subprocess.run(f"ps -p {pid}", shell=True, capture_output=True, text=True)
            if final_check.returncode != 0:
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
                    
                    # Step 1: Send SIGINT (Ctrl+C) multiple times to simulate graceful shutdown
                    print(f"[DEBUG] Sending SIGINT (Ctrl+C) to mining process...")
                    import signal
                    
                    # Send SIGINT twice for better reliability
                    for attempt in range(2):
                        try:
                            parent.send_signal(signal.SIGINT)
                            print(f"[DEBUG] Sent SIGINT attempt {attempt + 1} to parent {parent.pid}")
                            
                            for child in children:
                                try:
                                    child.send_signal(signal.SIGINT)
                                    print(f"[DEBUG] Sent SIGINT attempt {attempt + 1} to child {child.pid}")
                                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                                    print(f"[DEBUG] Không thể gửi SIGINT tới tiến trình con {child.pid}: {e}")
                            
                            # Small delay between attempts
                            if attempt == 0:
                                time.sleep(2)
                                
                        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                            print(f"[DEBUG] Không thể gửi SIGINT lần thử {attempt + 1}: {e}")
                    
                    # Wait for graceful shutdown after SIGINT
                    print(f"[DEBUG] Waiting for graceful shutdown after SIGINT...")
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
            'hash_rate': miner['hash_rate'],
            'coin_name': miner.get('coin_name', ''),
            'mining_tool': miner.get('mining_tool', ''),
            'auto_start': miner.get('auto_start', False),
            'last_output': miner['last_output'][-1000:] if miner['last_output'] else ''  # Last 1000 chars
        }
    
    def get_all_status(self):
        """Get status of all miners"""
        status_list = []
        for name in self.miners:
            status = self.get_miner_status(name)
            if status['success']:
                status_list.append(status)
        
        return {'success': True, 'miners': status_list}
    
    def _monitor_miner(self, name):
        """Monitor mining process output for hash rate"""
        miner = self.miners[name]
        process = miner['process']
        
        if not process:
            return
        
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                # Store latest output for monitoring
                if 'latest_output' not in miner:
                    miner['latest_output'] = ''
                miner['latest_output'] += line
                
                # Keep only last 5000 characters to prevent memory issues
                if len(miner['latest_output']) > 5000:
                    miner['latest_output'] = miner['latest_output'][-5000:]
                
                # Extract hash rate from output (tool-specific patterns)
                # Only extract from accepted lines to avoid noise
                line_lower = line.lower()
                if 'accepted:' in line_lower or 'accepted ' in line_lower:
                    hash_rate = self._extract_hash_rate(line, miner.get('mining_tool', ''))
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
    
    def _extract_hash_rate(self, line, mining_tool=''):
        """Extract hash rate from miner output based on mining tool"""
        
        # Tool-specific patterns
        if mining_tool.lower() == 'ccminer':
            # CCMiner patterns: 
            # "accepted: 123/124 (diff 0.01), 4.95 kH/s yes!"
            # "GPU #0: GeForce GTX 1080, 25.50 MH/s"
            patterns = [
                r'accepted:\s*\d+\/\d+\s*\(diff\s*\d+\.\d+\),\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]\/s)\s*yes!',
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
            # "[dero] 16-10-2025 03:29:57 [dero.rabidmining.com:10300] Accepted 159 | Rejected 0 | Height 6076878 | Diff 20000 | Uptime 00:03:01 | Hashrate 0.956KH/s."
            patterns = [
                r'Hashrate\s+(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'hashrate\s+(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'\|\s*Hashrate\s+(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',  # Specific for astrominer format
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
            match = re.search(pattern, line, re.IGNORECASE)
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
                except:
                    continue
        
        return None

# Global mining manager instance
mining_manager = MiningManager()

@app.route('/api/update-config', methods=['POST'])
def update_config():
    """Update mining configuration
    Expected payload: [
        {
            "name": "miner1",
            "coin_name": "ethereum",
            "mining_tool": "ccminer",
            "config": {"key": "value"},
            "required_files": ["ccminer.exe", "libcrypto-1_1-x64.dll"], // optional
            "auto_start": true  // optional
        }
    ]
    Query params: ?stop_all_first=true (to stop all miners before update)
    """
    try:
        data = request.get_json()
        stop_all_first = request.args.get('stop_all_first', 'false').lower() == 'true'
        
        if not isinstance(data, list):
            return jsonify({'success': False, 'message': 'Yêu cầu mảng các cấu hình miner'}), 400
        
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
                print(f"[CẬP NHẬT] Đã dừng {len(running_miners)} miners, chờ 3 giây...")
                time.sleep(3)
        
        results = []
        for miner_config in data:
            required_fields = ['name', 'coin_name', 'mining_tool', 'config']
            if not all(key in miner_config for key in required_fields):
                results.append({
                    'name': miner_config.get('name', 'unknown'),
                    'success': False,
                    'message': 'Thiếu các trường bắt buộc: name, coin_name, mining_tool, config'
                })
                continue
            
            success, message = mining_manager.update_miner_config(
                miner_config['name'],
                miner_config['coin_name'],
                miner_config['mining_tool'],
                miner_config['config'],
                miner_config.get('required_files'),
                miner_config.get('auto_start', False)
            )
            
            results.append({
                'name': miner_config['name'],
                'success': success,
                'message': message
            })
        
        return jsonify({'success': True, 'results': results})
        
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
    
    def signal_handler(sig, frame):
        print('\nĐang tắt Server Quản lý Mining...')
        # Stop all running miners
        for name, miner in mining_manager.miners.items():
            if miner.get('status') == 'running':
                print(f'Stopping miner: {name}')
                mining_manager.stop_miner(name)
        print('Server stopped gracefully')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Đang khởi động Server Quản lý Mining...")
    
    # Start auto-start in a separate thread after a delay
    def delayed_auto_start():
        time.sleep(5)  # Wait 5 seconds for server to fully start
        print("\n🚀 Checking for auto-start miners...")
        try:
            mining_manager.auto_start_miners()
        except Exception as e:
            print(f"Lỗi trong auto-start: {e}")
    
    # Start monitoring thread
    def start_monitoring():
        time.sleep(10)  # Wait 10 seconds before starting monitoring
        print("\n📊 Đang khởi động bộ giám sát mining...")
        mining_manager.monitor_miners()
    
    auto_start_thread = threading.Thread(target=delayed_auto_start)
    auto_start_thread.daemon = True
    auto_start_thread.start()
    
    monitor_thread = threading.Thread(target=start_monitoring)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try:
        app.run(host='0.0.0.0', port=9098, debug=False)
    except Exception as e:
        print(f"❌ Server không thể khởi động: {e}")
        sys.exit(1)