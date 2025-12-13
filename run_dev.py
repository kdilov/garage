#!/usr/bin/env python
"""
Development launcher - starts Flask and ngrok together.
Usage: python run_dev.py [--domain your-name.ngrok-free.app]
"""
import subprocess
import sys
import time
import signal
import json
import urllib.request
import shutil

# Configuration
FLASK_PORT = 8000
NGROK_DOMAIN = None  # Set your static domain here, or pass via --domain flag

flask_process = None
ngrok_process = None


def get_ngrok_url():
    """Fetch the public URL from ngrok's local API"""
    try:
        time.sleep(2)  # Give ngrok time to start
        req = urllib.request.urlopen('http://localhost:4040/api/tunnels')
        data = json.loads(req.read().decode())
        for tunnel in data['tunnels']:
            if tunnel['proto'] == 'https':
                return tunnel['public_url']
    except Exception:
        pass
    return None


def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    print("\n\n🛑 Shutting down...")
    
    if ngrok_process:
        ngrok_process.terminate()
        print("   ngrok stopped")
    
    if flask_process:
        flask_process.terminate()
        print("   Flask stopped")
    
    print("👋 Goodbye!\n")
    sys.exit(0)


def main():
    global flask_process, ngrok_process, NGROK_DOMAIN
    
    # Check for --domain flag
    if '--domain' in sys.argv:
        idx = sys.argv.index('--domain')
        if idx + 1 < len(sys.argv):
            NGROK_DOMAIN = sys.argv[idx + 1]
    
    # Register cleanup handler
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("=" * 60)
    print("🚀 Garage Inventory - Development Server")
    print("=" * 60)
    
    # Determine how to run Flask (uv or plain python)
    if shutil.which('uv'):
        flask_cmd = ['uv', 'run', 'python', 'app.py']
        print("\n📦 Starting Flask server (using uv)...")
    else:
        flask_cmd = [sys.executable, 'app.py']
        print("\n📦 Starting Flask server...")
    
    # Start Flask (don't capture output so we can see errors)
    flask_process = subprocess.Popen(flask_cmd)
    
    # Wait and check if Flask started
    time.sleep(3)
    
    if flask_process.poll() is not None:
        print("\n❌ Flask failed to start! Check the error above.")
        sys.exit(1)
    
    print(f"   ✅ Flask running on http://localhost:{FLASK_PORT}")
    
    # Check if ngrok is installed
    if not shutil.which('ngrok'):
        print("\n⚠️  ngrok not found! Install it from https://ngrok.com/download")
        print(f"   Flask is still running at http://localhost:{FLASK_PORT}")
        print("\nPress Ctrl+C to stop\n")
        try:
            flask_process.wait()
        except KeyboardInterrupt:
            cleanup()
        return
    
    # Start ngrok
    print("\n🌐 Starting ngrok tunnel...")
    
    if NGROK_DOMAIN:
        ngrok_cmd = ['ngrok', 'http', f'--domain={NGROK_DOMAIN}', str(FLASK_PORT)]
    else:
        ngrok_cmd = ['ngrok', 'http', str(FLASK_PORT)]
    
    ngrok_process = subprocess.Popen(
        ngrok_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Get the public URL
    public_url = get_ngrok_url()
    
    if public_url:
        print(f"   ✅ ngrok tunnel active")
    else:
        print("   ⚠️  Could not fetch ngrok URL (tunnel may still work)")
        public_url = f"https://{NGROK_DOMAIN}" if NGROK_DOMAIN else "Check http://localhost:4040"
    
    # Display info
    print("\n" + "=" * 60)
    print("✨ READY!")
    print("=" * 60)
    print(f"""
📍 Local URL:     http://localhost:{FLASK_PORT}
🌍 Public URL:    {public_url}
📱 ngrok inspect: http://localhost:4040

Use the Public URL on your phone to scan QR codes!
    """)
    print("=" * 60)
    print("Press Ctrl+C to stop\n")
    
    # Keep running
    try:
        while True:
            if flask_process.poll() is not None:
                print("❌ Flask stopped unexpectedly!")
                cleanup()
            if ngrok_process and ngrok_process.poll() is not None:
                print("❌ ngrok stopped unexpectedly!")
                cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == '__main__':
    main()