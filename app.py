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
                print(f"Error loading config: {e}")
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
            print(f"Error saving config: {e}")
            return False
    
    def download_file(self, filename, coin_dir):
        """Download mining file from CDN"""
        try:
            url = self.base_download_url + filename
            file_path = os.path.join(coin_dir, filename)
            
            # Skip if file already exists
            if os.path.exists(file_path):
                print(f"File {filename} already exists, skipping download")
                return True
            
            print(f"Downloading {filename} from {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            os.makedirs(coin_dir, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded {filename} successfully")
            return True
            
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return False
    
    def setup_coin_environment(self, coin_name, mining_tool, required_files):
        """Setup mining environment for a specific coin"""
        try:
            coin_dir = os.path.join(self.miners_dir, coin_name)
            
            # Download required files
            for filename in required_files:
                if not self.download_file(filename, coin_dir):
                    return False, f"Failed to download {filename}"
            
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
            
            return self.save_config(), "Configuration updated successfully"
            
        except Exception as e:
            return False, str(e)
    
    def get_default_files(self, mining_tool):
        """Get default required files for different mining tools"""
        default_files = {
            'ccminer': ['ccminer.exe', 'libcrypto-1_1-x64.dll'],  # Windows version
            't-rex': ['t-rex.exe'],
            'gminer': ['miner.exe'],
            'xmrig': ['xmrig.exe'],
            'teamredminer': ['teamredminer.exe'],
            'phoenixminer': ['PhoenixMiner.exe'],
            'claymore': ['EthDcrMiner64.exe'],
            'nbminer': ['nbminer.exe']
        }
        
        # For Linux, we might need different files
        if os.name == 'posix':  # Linux/Unix
            linux_files = {
                'ccminer': ['ccminer'],
                't-rex': ['t-rex'],
                'gminer': ['miner'],
                'xmrig': ['xmrig'],
                'teamredminer': ['teamredminer'],
                'phoenixminer': ['PhoenixMiner'],
                'claymore': ['ethdcrminer64'],
                'nbminer': ['nbminer']
            }
            return linux_files.get(mining_tool.lower(), [mining_tool])
        
        # Windows default
        return default_files.get(mining_tool.lower(), [f'{mining_tool}.exe'])
    
    def auto_start_miners(self):
        """Auto-start miners that have auto_start enabled"""
        if not self.auto_start_enabled:
            print("Auto-start is globally disabled")
            return
        
        auto_start_miners = []
        for name, miner in self.miners.items():
            if miner.get('auto_start', False) and miner.get('status') == 'stopped':
                auto_start_miners.append(name)
        
        if auto_start_miners:
            print(f"Auto-starting miners: {auto_start_miners}")
            for name in auto_start_miners:
                result = self.start_miner(name)
                if result['success']:
                    print(f"✅ Auto-started {name}")
                else:
                    print(f"❌ Failed to auto-start {name}: {result['message']}")
                time.sleep(2)  # Delay between starts
        else:
            print("No miners configured for auto-start")
    
    def set_auto_start_global(self, enabled):
        """Enable/disable auto-start globally"""
        self.auto_start_enabled = enabled
        return True
    
    def start_miner(self, name):
        """Start a mining process"""
        if name not in self.miners:
            return {'success': False, 'message': f'Miner {name} not found'}
        
        miner = self.miners[name]
        
        if miner['status'] == 'running':
            return {'success': False, 'message': f'Miner {name} is already running'}
        
        try:
            # Write config to file
            if miner['config_file'] and miner['config']:
                config_dir = os.path.dirname(miner['config_file'])
                if config_dir and not os.path.exists(config_dir):
                    os.makedirs(config_dir)
                
                with open(miner['config_file'], 'w', encoding='utf-8') as f:
                    if isinstance(miner['config'], dict):
                        json.dump(miner['config'], f, indent=2)
                    else:
                        f.write(str(miner['config']))
            
            # Prepare command with absolute paths
            coin_dir = miner.get('coin_dir')
            if not coin_dir or not os.path.exists(coin_dir):
                return {'success': False, 'message': f'Coin directory not found: {coin_dir}'}
            
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
                    return {'success': False, 'message': f'Mining executable not found: {mining_exe} or {mining_exe_win}'}
            
            if not os.path.exists(config_file):
                return {'success': False, 'message': f'Config file not found: {config_file}'}
            
            # Create command with absolute paths
            cmd = f'"{mining_exe}" -c "{config_file}"'
            
            print(f"Starting miner {name}...")
            print(f"  Working dir: {coin_dir}")
            print(f"  Command: {cmd}")
            
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
            miner['start_time'] = datetime.now().isoformat()
            
            # Start monitoring thread
            thread = threading.Thread(target=self._monitor_miner, args=(name,))
            thread.daemon = True
            thread.start()
            
            return {'success': True, 'message': f'Miner {name} started', 'pid': process.pid}
            
        except Exception as e:
            miner['status'] = 'error'
            return {'success': False, 'message': f'Failed to start miner {name}: {str(e)}'}
    
    def stop_miner(self, name):
        """Stop a mining process"""
        if name not in self.miners:
            return {'success': False, 'message': f'Miner {name} not found'}
        
        miner = self.miners[name]
        
        if miner['status'] != 'running':
            return {'success': False, 'message': f'Miner {name} is not running'}
        
        try:
            if miner['pid']:
                # Try to terminate gracefully first
                try:
                    parent = psutil.Process(miner['pid'])
                    children = parent.children(recursive=True)
                    for child in children:
                        child.terminate()
                    parent.terminate()
                    
                    # Wait for processes to terminate
                    gone, still_alive = psutil.wait_procs(children + [parent], timeout=5)
                    
                    # Force kill if still alive
                    for proc in still_alive:
                        proc.kill()
                        
                except psutil.NoSuchProcess:
                    pass
                except Exception as e:
                    print(f"Error stopping process: {e}")
            
            miner['status'] = 'stopped'
            miner['process'] = None
            miner['pid'] = None
            miner['hash_rate'] = 0
            
            return {'success': True, 'message': f'Miner {name} stopped'}
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to stop miner {name}: {str(e)}'}
    
    def get_miner_status(self, name):
        """Get status of a specific miner"""
        if name not in self.miners:
            return {'success': False, 'message': f'Miner {name} not found'}
        
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
                
                miner['last_output'] += line
                
                # Keep only last 5000 characters to prevent memory issues
                if len(miner['last_output']) > 5000:
                    miner['last_output'] = miner['last_output'][-5000:]
                
                # Extract hash rate from output (tool-specific patterns)
                hash_rate = self._extract_hash_rate(line, miner.get('mining_tool', ''))
                if hash_rate:
                    miner['hash_rate'] = hash_rate
                
                # Check if process is still running
                if process.poll() is not None:
                    break
            
            # Process has ended
            miner['status'] = 'stopped'
            miner['process'] = None
            miner['pid'] = None
            miner['hash_rate'] = 0
            
        except Exception as e:
            print(f"Error monitoring miner {name}: {e}")
            miner['status'] = 'error'
    
    def _extract_hash_rate(self, line, mining_tool=''):
        """Extract hash rate from miner output based on mining tool"""
        
        # Tool-specific patterns
        if mining_tool.lower() == 'ccminer':
            # CCMiner patterns: "GPU #0: GeForce GTX 1080, 25.50 MH/s"
            patterns = [
                r'GPU #\d+:.*?(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'[Tt]otal:\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
            ]
        elif mining_tool.lower() == 't-rex':
            # T-Rex patterns: "GPU #0: 45.5 MH/s"
            patterns = [
                r'GPU #\d+:\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'[Tt]otal:\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
            ]
        elif mining_tool.lower() == 'gminer':
            # GMiner patterns
            patterns = [
                r'GPU\d+\s+(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'[Ss]peed:\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
            ]
        elif mining_tool.lower() == 'xmrig':
            # XMRig patterns: "speed 10s/60s/15m 1000.0 1000.0 1000.0 H/s"
            patterns = [
                r'speed\s+\S+\s+(\d+\.?\d*)\s+\d+\.?\d*\s+\d+\.?\d*\s*([kmgtKMGT]?[Hh]/s)',
                r'(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
            ]
        elif mining_tool.lower() == 'phoenixminer':
            # PhoenixMiner patterns
            patterns = [
                r'GPU\d+:\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
                r'[Tt]otal\s*[Ss]peed:\s*(\d+\.?\d*)\s*([kmgtKMGT]?[Hh]/s)',
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
                    
                    # Convert to H/s based on unit
                    if 'k' in unit:
                        value *= 1000
                    elif 'm' in unit:
                        value *= 1000000
                    elif 'g' in unit:
                        value *= 1000000000
                    elif 't' in unit:
                        value *= 1000000000000
                    
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
    """
    try:
        data = request.get_json()
        
        if not isinstance(data, list):
            return jsonify({'success': False, 'message': 'Expected array of miner configurations'}), 400
        
        results = []
        for miner_config in data:
            required_fields = ['name', 'coin_name', 'mining_tool', 'config']
            if not all(key in miner_config for key in required_fields):
                results.append({
                    'name': miner_config.get('name', 'unknown'),
                    'success': False,
                    'message': 'Missing required fields: name, coin_name, mining_tool, config'
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
            return jsonify({'success': False, 'message': 'Expected "name" or "names" field'}), 400
            
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
            return jsonify({'success': False, 'message': 'Expected "name" or "names" field'}), 400
            
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
        print('\nShutting down Mining Management Server...')
        # Stop all running miners
        for name, miner in mining_manager.miners.items():
            if miner.get('status') == 'running':
                print(f'Stopping miner: {name}')
                mining_manager.stop_miner(name)
        print('Server stopped gracefully')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting Mining Management Server...")
    print("API Endpoints:")
    print("  POST /api/update-config - Update miner configurations (auto-download)")
    print("  POST /api/start - Start mining")
    print("  POST /api/stop - Stop mining")
    print("  GET  /api/status - Get mining status")
    print("  GET  /api/miners - List all miners")
    print("  GET  /api/health - Health check")
    print("  POST /api/auto-start - Manually trigger auto-start")
    print("  POST /api/auto-start/config - Enable/disable auto-start")
    print("  GET  /api/auto-start/config - Get auto-start configuration")
    print("")
    print("Mining tools supported: ccminer, t-rex, gminer, xmrig, phoenixminer, etc.")
    print("Files auto-download from: http://cdn.dndvina.com/minings/")
    print("")
    print("Example config:")
    print('POST /api/update-config')
    print('[{')
    print('  "name": "ethereum-gpu1",')
    print('  "coin_name": "ethereum",')
    print('  "mining_tool": "ccminer",')
    print('  "config": {"pool": "eth-pool.com:4444", "wallet": "0x123..."},')
    print('  "auto_start": true')
    print('}]')
    
    # Start auto-start in a separate thread after a delay
    def delayed_auto_start():
        time.sleep(5)  # Wait 5 seconds for server to fully start
        print("\n🚀 Checking for auto-start miners...")
        try:
            mining_manager.auto_start_miners()
        except Exception as e:
            print(f"❌ Auto-start failed: {e}")
    
    auto_start_thread = threading.Thread(target=delayed_auto_start)
    auto_start_thread.daemon = True
    auto_start_thread.start()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)