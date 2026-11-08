import requests
import time
import concurrent.futures
import os
from datetime import datetime

try:
    from termcolor import colored
except ImportError:
    def colored(text, color=None):
        return text

os.system('title Roblox Username Checker')

AVAILABLE_FILE = 'availableRoblox.txt'
TAKEN_FILE = 'takenRoblox.txt'
INVALID_FILE = 'invalidRoblox.txt'
USERNAMES_FILE = 'usernames.txt'

available = open(AVAILABLE_FILE, 'a+', encoding='utf-8')
taken = open(TAKEN_FILE, 'a+', encoding='utf-8')
invalid = open(INVALID_FILE, 'a+', encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

# Roblox codes from their validate endpoint
# 0 = valid / available
# 1 = already in use
# 2 = not appropriate
# 3 = length invalid (3-20)
# 4 = starts/ends with _
# 5 = more than one _
# 6 = contains spaces
# 7+ = other invalid / reserved / pii etc.

def check(user):
    user = user.strip()
    if not user:
        return

    url = (
        f"https://auth.roblox.com/v1/usernames/validate"
        f"?username={user}"
        f"&birthday=2000-01-01T00:00:00.000Z"
        f"&context=Signup"
    )

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            print(colored(f"[?] ERROR {user}  status={r.status_code}", 'yellow'))
            return

        data = r.json()
        code = data.get('code')
        msg = data.get('message', '')

        if code == 0:
            print(colored(f"[+] AVAILABLE  {user}", 'green'))
            available.write(user + '\n')
            available.flush()
        elif code == 1:
            print(colored(f"[-] TAKEN      {user}", 'red'))
            taken.write(user + '\n')
            taken.flush()
        else:
            print(colored(f"[!] INVALID    {user}  ({code}: {msg})", 'magenta'))
            invalid.write(f"{user} | code={code} | {msg}\n")
            invalid.flush()

    except Exception as e:
        print(colored(f"[?] FAIL       {user}  {e}", 'yellow'))


print(colored(r'''
██████╗  ██████╗ ██████╗ ██╗      ██████╗ ██╗  ██╗
██╔══██╗██╔═══██╗██╔══██╗██║     ██╔═══██╗╚██╗██╔╝
██████╔╝██║   ██║██████╔╝██║     ██║   ██║ ╚███╔╝ 
██╔══██╗██║   ██║██╔══██╗██║     ██║   ██║ ██╔██╗ 
██║  ██║╚██████╔╝██████╔╝███████╗╚██████╔╝██╔╝ ██╗
╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═╝
                                                  
██╗   ██╗███████╗███████╗██████╗ ███╗   ██╗ █████╗ ███╗   ███╗███████╗
██║   ██║██╔════╝██╔════╝██╔══██╗████╗  ██║██╔══██╗████╗ ████║██╔════╝
██║   ██║███████╗█████╗  ██████╔╝██╔██╗ ██║███████║██╔████╔██║█████╗  
██║   ██║╚════██║██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝  
╚██████╔╝███████║███████╗██║  ██║██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗
 ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝
                                                  
 ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗ 
██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝
██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗
╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║
 ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
''', 'cyan'))

print(colored("Roblox Username Availability Checker", 'yellow'))
print(colored("Endpoint: auth.roblox.com/v1/usernames/validate", 'white'))
print(colored(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", 'white'))

if not os.path.exists(USERNAMES_FILE):
    print(colored(f"[!] {USERNAMES_FILE} not found. Create it with one username per line.", 'red'))
    input(colored("Press Enter to exit...", 'yellow'))
    exit(1)

lol = input(colored("Press Enter to start checking...", "yellow"))
time.sleep(0.3)

with open(USERNAMES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
    users = [line.strip() for line in f if line.strip()]

print(colored(f"\nLoaded {len(users)} usernames. Checking...\n", 'cyan'))

with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    executor.map(check, users)

available.close()
taken.close()
invalid.close()

print(colored("\nDone.", 'green'))
print(colored(f"Available → {AVAILABLE_FILE}", 'green'))
print(colored(f"Taken     → {TAKEN_FILE}", 'red'))
print(colored(f"Invalid   → {INVALID_FILE}", 'magenta'))
input(colored("\nPress Enter to exit...", 'yellow'))
