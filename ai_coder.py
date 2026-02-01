#!/usr/bin/env python3
"""
AI CODER - Multi-Model Genius Copilot
Supports: Google Gemini, Groq, OpenAI, DeepSeek, Claude
Based on JARVIS architecture with enhanced features

Repository: https://github.com/zombiegirlcz/multi_AI_asistent_coder
Version: 2.1.0
"""

__version__ = "2.1.0"
REPO_URL = "https://api.github.com/repos/zombiegirlcz/multi_AI_asistent_coder"
UPDATE_CHECK_URL = f"{REPO_URL}/releases/latest"

import os
import sys
import json
import subprocess
import re
import time
import ast
import textwrap
import difflib
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

# Import interactive UI
try:
    from interactive_ui import InteractiveUI
except ImportError:
    InteractiveUI = None

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = BLUE = MAGENTA = WHITE = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""

try:
    import requests
except ImportError:
    requests = None

# API libraries
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


PROVIDERS = {
    "1": {"name": "Google Gemini", "type": "google", "base_url": "https://generativelanguage.googleapis.com/v1beta/models", "list_url": "https://generativelanguage.googleapis.com/v1beta/models?key={KEY}"},
    "2": {"name": "Groq", "type": "openai", "base_url": "https://api.groq.com/openai/v1/chat/completions", "list_url": "https://api.groq.com/openai/v1/models"},
    "3": {"name": "OpenAI", "type": "openai", "base_url": "https://api.openai.com/v1/chat/completions", "list_url": "https://api.openai.com/v1/models"},
    "4": {"name": "DeepSeek", "type": "openai", "base_url": "https://api.deepseek.com/chat/completions", "list_url": "https://api.deepseek.com/models"},
    "5": {"name": "Claude (Anthropic)", "type": "anthropic", "local": True}
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def type_effect(text, speed=0.01, color=Fore.GREEN):
    for char in text:
        sys.stdout.write(color + char)
        sys.stdout.flush()
        time.sleep(speed)
    print(Fore.RESET)

def send_request(provider: Dict, key: str, model: str, messages: List[Dict]) -> str:
    """Universal API request handler"""
    try:
        if not requests:
            return "❌ Install: pip install requests"
        
        if provider["type"] == "google":
            full_prompt = ""
            for m in messages:
                role = "USER" if m["role"] == "user" else "SYSTEM"
                full_prompt += f"{role}: {m['content']}\n"
            url = f"{provider['base_url']}/{model}:generateContent?key={key}"
            data = {"contents": [{"parts": [{"text": full_prompt}]}]}
            r = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=30)
            if r.status_code != 200:
                return f"❌ API Error: {r.text}"
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        elif provider["type"] == "openai":
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            data = {"model": model, "messages": messages}
            r = requests.post(provider["base_url"], json=data, headers=headers, timeout=30)
            if r.status_code != 200:
                return f"❌ API Error: {r.text}"
            return r.json()["choices"][0]["message"]["content"]
        
        elif provider["type"] == "anthropic":
            if not anthropic:
                return "❌ Install: pip install anthropic"
            client = anthropic.Anthropic(api_key=key)
            response = client.messages.create(model=model, max_tokens=4096, messages=messages)
            return response.content[0].text
        
        return "❌ Unknown provider"
    except Exception as e:
        return f"❌ Critical Error: {e}"


class AICodeAssistant:
    """Main AI Code Assistant - JARVIS Genius Edition"""
    
    def __init__(self):
        self.config_file = Path.home() / ".ai_coder_config"
        self.config = {}
        self.provider = None
        self.key = None
        self.model = None
        self.conversation_history = []
        self.memory = {
            "active_file": None,
            "last_error": None,
            "created_files": []
        }
        self.ui = InteractiveUI() if InteractiveUI else None
        self.load_config()
    
    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
        os.chmod(self.config_file, 0o600)
    
    def get_key_from_history(self, provider_name: str) -> str:
        """Get or create API key for provider"""
        if "provider_keys" not in self.config:
            self.config["provider_keys"] = {}
        if provider_name not in self.config["provider_keys"]:
            self.config["provider_keys"][provider_name] = []
        
        history = self.config["provider_keys"][provider_name]
        
        print(f"\n{Fore.CYAN}--- SPRÁVA KLÍČŮ: {provider_name} ---{Fore.RESET}")
        
        if history:
            for i, k in enumerate(history):
                masked = k[:8] + "..." + k[-4:] if len(k) > 12 else k
                print(f" [{i+1}] {masked}")
        else:
            print(f"{Style.DIM}(Žádné uložené klíče){Fore.RESET}")
        
        print(f" [N] + Nový klíč")
        sel = input(f"{Fore.YELLOW}> {Fore.RESET}").lower().strip()
        
        if sel == "n" or sel == "":
            key = input(f"{Fore.GREEN}Vlož API klíč: {Fore.RESET}").strip()
            if key and key not in history:
                history.append(key)
                self.save_config()
            return key
        
        try:
            return history[int(sel)-1]
        except:
            return ""
    
    def fetch_models(self, provider: Dict, key: str) -> List[str]:
        """Fetch available models from provider"""
        if not requests:
            return []
        
        try:
            print(f"\n{Fore.CYAN}Stahuji dostupné modely...{Fore.RESET}")
            
            if provider["type"] == "google":
                url = provider["list_url"].format(KEY=key)
                r = requests.get(url, timeout=10)
            else:
                url = provider["list_url"]
                headers = {"Authorization": f"Bearer {key}"}
                r = requests.get(url, headers=headers, timeout=10)
            
            if r.status_code != 200:
                print(f"{Fore.RED}❌ Chyba: {r.status_code}{Fore.RESET}")
                return []
            
            data = r.json()
            models = []
            
            if provider["type"] == "google":
                for m in data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        models.append(m["name"].replace("models/", ""))
            else:
                for m in data.get("data", []):
                    models.append(m["id"])
            
            return sorted(models)[:20]
        except Exception as e:
            print(f"{Fore.RED}❌ Chyba při stahování: {e}{Fore.RESET}")
            return []
    
    def surgical_update(self, file_path: str, func_name: str, new_code: str) -> str:
        """Smart surgical code update - preserves indentation"""
        try:
            if not os.path.exists(file_path):
                return f"❌ Soubor '{file_path}' neexistuje"
            
            with open(file_path, "r", encoding="utf-8") as f:
                full_code = f.read()
            
            lines = full_code.splitlines()
            tree = ast.parse(full_code)
            
            start, end, indent_str = None, None, ""
            
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == func_name:
                            start = item.lineno - 1
                            end = item.end_lineno
                            indent_str = lines[start][:len(lines[start]) - len(lines[start].lstrip())]
                            break
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    start = node.lineno - 1
                    end = node.end_lineno
                    break
            
            if start is None:
                return f"❌ Funkce '{func_name}' nenalezena"
            
            clean_code = new_code.replace("```python", "").replace("```", "").strip()
            ast.parse(clean_code)
            
            dedented = textwrap.dedent(clean_code)
            indented = [indent_str + line if line.strip() else line for line in dedented.splitlines()]
            
            final = lines[:start] + indented + lines[end:]
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(final))
            
            return f"✅ Funkce '{func_name}' aktualizována"
        except SyntaxError as e:
            return f"❌ Syntaxe chyba: {e}"
        except Exception as e:
            return f"❌ Chyba: {e}"
    
    def tool_scan(self, path: str) -> str:
        """Scan directory with limit"""
        target = path.strip() if path.strip() else os.getcwd()
        if target.startswith("~"):
            target = os.path.expanduser(target)
        
        if not os.path.exists(target):
            return f"❌ Adresář '{target}' neexistuje"
        
        try:
            items = os.listdir(target)
            dirs = [i + "/" for i in items if os.path.isdir(os.path.join(target, i))]
            files = [i for i in items if not os.path.isdir(os.path.join(target, i))]
            
            all_items = sorted(dirs) + sorted(files)
            limit = 100
            
            output = []
            for item in all_items[:limit]:
                output.append(item)
                print(f"  {item}")
            
            if len(all_items) > limit:
                print(f"  ... (+{len(all_items)-limit} dalších)")
            
            return "\n".join(output)
        except Exception as e:
            return f"❌ Chyba: {e}"
    
    def tool_edit(self, file_path: str, instruction: str) -> str:
        """Generate and edit file"""
        fn = file_path.strip()
        
        if os.path.exists(fn):
            with open(fn, "r", errors="ignore") as f:
                original = f.read()
        else:
            os.makedirs(os.path.dirname(fn) or ".", exist_ok=True)
            original = ""
        
        print(f"{Fore.BLUE}⏳ Generuji kód...{Fore.RESET}")
        
        prompt = f"FILE: {fn}\nOriginal:\n```\n{original}\n```\n\nInstructions: {instruction}\n\nReturn ONLY code in ```blocks```"
        resp = send_request(self.provider, self.key, self.model, 
                           [{"role": "user", "content": prompt}])
        
        new_code = resp
        if "```" in resp:
            try:
                new_code = resp.split("```")[1]
                if new_code.startswith(("python", "bash")):
                    new_code = new_code.lstrip("pythonbash").lstrip()
                new_code = new_code.strip()
            except:
                pass
        
        if original == new_code:
            return "Žádné změny"
        
        diff = list(difflib.unified_diff(original.splitlines()[:20], new_code.splitlines()[:20], lineterm=''))
        
        print(f"\n{Fore.CYAN}--- NÁHLED ZMĚN ---{Fore.RESET}")
        for line in diff[:30]:
            if line.startswith('+'):
                print(f"{Fore.GREEN}{line}{Fore.RESET}")
            elif line.startswith('-'):
                print(f"{Fore.RED}{line}{Fore.RESET}")
            else:
                print(f"{Style.DIM}{line}{Fore.RESET}")
        
        if input(f"\n{Fore.YELLOW}Uložit? [a/n]: {Fore.RESET}").lower().startswith('a'):
            if os.path.exists(fn):
                os.rename(fn, fn + ".bak")
            with open(fn, "w") as f:
                f.write(new_code)
            self.memory["active_file"] = fn
            return f"✅ Uloženo: {fn}"
        
        return "⛔ Zrušeno"
    
    def tool_exec(self, cmd: str) -> str:
        """Execute shell command"""
        print(f"\n{Fore.MAGENTA}$ {cmd}{Fore.RESET}")
        
        if input(f"{Fore.YELLOW}Spustit? [a/n]: {Fore.RESET}").lower().startswith('a'):
            try:
                is_live = any(x in cmd for x in ["python", "bash", "sh", "vim", "nano", "play"])
                
                if is_live:
                    os.system(cmd)
                    return "✅ Interaktivní příkaz hotov"
                
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                out = (res.stdout + res.stderr)[:2000]
                
                print(f"{Fore.CYAN}{out}{Fore.RESET}")
                return f"EXIT: {res.returncode}\nOUT:\n{out}"
            except subprocess.TimeoutExpired:
                return "❌ Timeout"
            except Exception as e:
                return f"❌ Chyba: {e}"
        
        return "⛔ Zrušeno"
    
    def check_updates(self) -> bool:
        """Check for new version from GitHub"""
        if not requests:
            return False
        
        try:
            r = requests.get(UPDATE_CHECK_URL, timeout=5)
            if r.status_code == 200:
                latest = r.json().get("tag_name", "").lstrip("v")
                if latest and latest > __version__:
                    print(f"\n{Fore.YELLOW}⬆️  Nová verze dostupná: {latest}")
                    print(f"{Fore.CYAN}   https://github.com/zombiegirlcz/multi_AI_asistent_coder/releases{Fore.RESET}\n")
                    return True
        except:
            pass
        return False
    
    def show_intro(self):
        """Show beautiful intro screen"""
        clear_screen()
        time.sleep(0.5)
        
        print(f"\n{Fore.BLUE}{'═' * 60}")
        print(f"{Fore.MAGENTA}     ▄▄████▄▄        ".center(60))
        print(f"{Fore.MAGENTA}    ██████████▄       ".center(60))
        print(f"{Fore.MAGENTA}   ███▀▀    ▀▀███     ".center(60))
        print(f"{Fore.CYAN}   AI CODER v{__version__} - GENIUS EDITION")
        print(f"{Fore.MAGENTA}   Multi-Provider Copilot for Termux".center(60))
        print(f"{Fore.BLUE}{'═' * 60}\n{Fore.RESET}")
        
        self.check_updates()
    
    def show_menu(self):
        """Show provider selection menu"""
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════╗")
        print(f"║ 🧠 VÝBĚR POSKYTOVATELE                    ║")
        print(f"╠══════════════════════════════════════════════╣")
        
        for k, v in PROVIDERS.items():
            name = v['name'].ljust(25)
            print(f"║ {Fore.YELLOW}[{k}]{Fore.RESET} {Fore.WHITE}{name}{Fore.CYAN}║")
        
        print(f"║ {Fore.RED}[X]{Fore.RESET} Ukončit{' ' * 37}{Fore.CYAN}║")
        print(f"╚══════════════════════════════════════════════╝{Fore.RESET}")
    
    def show_help(self):
        """Display help"""
        print(f"""
{Fore.CYAN}╔════════════════════════════════════════════╗
║        PŘÍKAZY                             ║
╚════════════════════════════════════════════╝{Fore.RESET}

{Fore.GREEN}📁 SPRÁVA SOUBORŮ:{Fore.RESET}
  /read <cesta>              - Čtení souboru
  /write <cesta> <text>      - Zápis souboru
  /scan [cesta]              - Procházení adresáře

{Fore.GREEN}⚙️  OPERACE:{Fore.RESET}
  /run <příkaz>              - Spuštění příkazu
  /search <text>             - Hledání v souborech

{Fore.GREEN}🎮 KONTROLA:{Fore.RESET}
  /menu                      - Zpět do menu
  /help                      - Tato nápověda
  /exit                      - Ukončit program

{Fore.GREEN}💬 CHAT:{Fore.RESET}
  Jen piš normálně - AI bude pracovat!
""")
    
    def run(self):
        """Main interactive loop with interactive UI"""
        self.show_intro()
        
        if self.ui:
            return self.run_interactive()
        else:
            return self.run_classic()
    
    def run_interactive(self):
        """Modern interactive mode with arrow selection"""
        while True:
            provider_names = list(PROVIDERS.values())
            provider_list = [v["name"] for v in provider_names]
            provider_list.append("❌ Ukončit")
            
            choice = self.ui.select_from_list(
                "🧠 Vyber AI poskytovatele",
                provider_list
            )
            
            if choice == "❌ Ukončit":
                self.ui.info_message("Vypínám...")
                break
            
            provider = next((v for v in PROVIDERS.values() if v["name"] == choice), None)
            if not provider:
                continue
            
            if provider.get("local"):
                key = self.get_key_from_history(provider["name"])
                models = ["claude-3-5-sonnet-20241022", "claude-3-opus-20250129"]
            else:
                key = self.get_key_from_history(provider["name"])
                models = self.fetch_models(provider, key)
            
            if not key or not models:
                self.ui.error_message("Nelze se připojit")
                continue
            
            self.provider = provider
            self.key = key
            
            selected_model = self.ui.select_from_list(
                "🎯 Vyber model",
                models[:20]
            )
            self.model = selected_model
            
            self.ui.success_message(f"Připraven! Model: {self.model}")
            
            self.conversation_history = []
            self.run_chat_loop()
    
    def run_classic(self):
        """Classic text-based mode (fallback)"""
        while True:
            self.show_menu()
            
            choice = input(f"{Fore.YELLOW}root@ai-coder:~# {Fore.RESET}").strip().lower()
            
            if choice == "x":
                print(f"{Fore.RED}Vypínám...{Fore.RESET}")
                break
            
            if choice not in PROVIDERS:
                print(f"{Fore.RED}❌ Neznámá volba{Fore.RESET}")
                continue
            
            provider = PROVIDERS[choice]
            
            if provider.get("local"):
                key = self.get_key_from_history(provider["name"])
                models = ["claude-3-5-sonnet-20241022", "claude-3-opus-20250129"]
            else:
                key = self.get_key_from_history(provider["name"])
                models = self.fetch_models(provider, key)
            
            if not key or not models:
                print(f"{Fore.RED}❌ Nelze se připojit{Fore.RESET}")
                continue
            
            self.provider = provider
            self.key = key
            
            print(f"\n{Fore.GREEN}╔══════════════════════════════════════════════╗")
            print(f"║ 🎯 DOSTUPNÉ MODELY                        ║")
            print(f"╠══════════════════════════════════════════════╣")
            
            for i, m in enumerate(models):
                m_display = m[:35] + ".." if len(m) > 37 else m
                print(f"║ {Fore.YELLOW}[{i+1}]{Fore.RESET} {m_display:<37} {Fore.GREEN}║")
            
            print(f"╚══════════════════════════════════════════════╝{Fore.RESET}")
            
            try:
                sel = int(input(f"{Fore.CYAN}Vyber [1-{len(models)}]: {Fore.RESET}")) - 1
                self.model = models[sel]
            except:
                self.model = models[0]
            
            type_effect(f"\n✅ Připraven! Napiš /help pro příkazy.", speed=0.02)
            
            self.conversation_history = []
            self.run_chat_loop()
    
    def run_chat_loop(self):
        """Main chat loop"""
        while True:
            try:
                user_input = input(f"\n{Fore.BLUE}You> {Fore.RESET}").strip()
                
                if not user_input:
                    continue
                
                if user_input == "/exit":
                    sys.exit()
                
                if user_input == "/menu":
                    break
                
                if user_input == "/help":
                    self.show_help()
                    continue
                
                # Handle file commands
                if user_input.startswith("/read "):
                    path = user_input[6:]
                    try:
                        with open(path) as f:
                            print(f"\n📄 {path}:\n{f.read()}\n")
                    except Exception as e:
                        print(f"{Fore.RED}❌ {e}{Fore.RESET}")
                    continue
                
                if user_input.startswith("/scan"):
                    path = user_input[5:].strip()
                    print(f"\n📁 Skenuji: {path}")
                    self.tool_scan(path)
                    continue
                
                if user_input.startswith("/run "):
                    cmd = user_input[5:]
                    self.tool_exec(cmd)
                    continue
                
                # AI Chat
                print(f"\n{Fore.YELLOW}⏳ Thinking...{Fore.RESET}")
                
                self.conversation_history.append({"role": "user", "content": user_input})
                
                response = send_request(self.provider, self.key, self.model, 
                                       self.conversation_history)
                
                self.conversation_history.append({"role": "assistant", "content": response})
                
                print(f"\n{Fore.CYAN}AI: {response}{Fore.RESET}")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.RED}Interrupted{Fore.RESET}")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Error: {e}{Fore.RESET}")


def main():
    """Main entry point"""
    try:
        os.chdir(os.path.expanduser("~"))
    except:
        pass
    
    assistant = AICodeAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
