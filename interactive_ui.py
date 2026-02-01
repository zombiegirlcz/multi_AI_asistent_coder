#!/usr/bin/env python3
"""
Interactive UI Module for AI Coder
Features: Multi-choice selection, tables, questions, interactive menus
"""

try:
    import inquirer
except ImportError:
    inquirer = None

try:
    from rich.table import Table
    from rich.console import Console
    from rich.panel import Panel
    from rich.align import Align
except ImportError:
    Table = Console = Panel = Align = None

from typing import List, Dict, Any, Optional
import sys


class InteractiveUI:
    """Interactive CLI interface with tables and arrow navigation"""
    
    def __init__(self):
        self.console = Console() if Console else None
    
    def select_from_list(self, message: str, choices: List[str], default: int = 0) -> str:
        """
        Interactive selection with arrow keys
        
        Args:
            message: Question to display
            choices: List of options
            default: Default index
        
        Returns:
            Selected choice
        """
        if not inquirer:
            for i, choice in enumerate(choices):
                print(f"  [{i+1}] {choice}")
            sel = input(f"{message}: ").strip()
            try:
                return choices[int(sel)-1]
            except:
                return choices[default]
        
        questions = [
            inquirer.List('selection', message=message, choices=choices)
        ]
        answers = inquirer.prompt(questions)
        return answers['selection']
    
    def select_multiple(self, message: str, choices: List[str]) -> List[str]:
        """
        Multi-select with checkboxes
        
        Args:
            message: Question to display
            choices: List of options
        
        Returns:
            List of selected choices
        """
        if not inquirer:
            for i, choice in enumerate(choices):
                print(f"  [{i+1}] {choice}")
            sel = input(f"{message} (comma-separated numbers): ").strip()
            try:
                indices = [int(x.strip())-1 for x in sel.split(',')]
                return [choices[i] for i in indices if i < len(choices)]
            except:
                return []
        
        questions = [
            inquirer.Checkbox('selections', message=message, choices=choices)
        ]
        answers = inquirer.prompt(questions)
        return answers['selections']
    
    def text_input(self, message: str, default: str = "") -> str:
        """
        Get text input from user
        
        Args:
            message: Question to ask
            default: Default value
        
        Returns:
            User input
        """
        if not inquirer:
            return input(f"{message}: ").strip() or default
        
        questions = [
            inquirer.Text('text_input', message=message, default=default)
        ]
        answers = inquirer.prompt(questions)
        return answers['text_input']
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """
        Yes/No confirmation
        
        Args:
            message: Question to ask
            default: Default choice
        
        Returns:
            True if yes, False if no
        """
        if not inquirer:
            default_text = "[Y/n]" if default else "[y/N]"
            response = input(f"{message} {default_text}: ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            return default
        
        questions = [
            inquirer.Confirm('confirm', message=message, default=default)
        ]
        answers = inquirer.prompt(questions)
        return answers['confirm']
    
    def show_table(self, title: str, columns: List[str], rows: List[List[str]]):
        """
        Display formatted table
        
        Args:
            title: Table title
            columns: Column headers
            rows: Data rows
        """
        if not Table or not self.console:
            print(f"\n{title}")
            print("=" * 50)
            for row in rows:
                print(" | ".join(str(x) for x in row))
            return
        
        table = Table(title=title, show_header=True, header_style="bold cyan")
        for col in columns:
            table.add_column(col, style="green")
        for row in rows:
            table.add_row(*[str(x) for x in row])
        
        self.console.print(table)
    
    def show_panel(self, title: str, content: str, color: str = "blue"):
        """
        Display content in a panel
        
        Args:
            title: Panel title
            content: Panel content
            color: Panel color
        """
        if not Panel or not self.console:
            print(f"\n{title}")
            print("-" * 50)
            print(content)
            return
        
        panel = Panel(content, title=title, style=f"bold {color}")
        self.console.print(panel)
    
    def show_menu(self, title: str, options: Dict[str, str]) -> str:
        """
        Show interactive menu with descriptions
        
        Args:
            title: Menu title
            options: Dict of {key: description}
        
        Returns:
            Selected option key
        """
        choices = [f"{k}. {v}" for k, v in options.items()]
        selected = self.select_from_list(title, choices)
        return selected.split(".")[0].strip()
    
    def progress_message(self, message: str):
        """Show progress/info message"""
        if self.console:
            self.console.print(f"⏳ {message}", style="yellow")
        else:
            print(f"⏳ {message}")
    
    def success_message(self, message: str):
        """Show success message"""
        if self.console:
            self.console.print(f"✅ {message}", style="green")
        else:
            print(f"✅ {message}")
    
    def error_message(self, message: str):
        """Show error message"""
        if self.console:
            self.console.print(f"❌ {message}", style="red")
        else:
            print(f"❌ {message}")
    
    def info_message(self, message: str):
        """Show info message"""
        if self.console:
            self.console.print(f"ℹ️  {message}", style="cyan")
        else:
            print(f"ℹ️  {message}")


def run_interactive_setup() -> Dict[str, Any]:
    """
    Interactive setup wizard
    Returns: Configuration dictionary
    """
    ui = InteractiveUI()
    config = {}
    
    ui.show_panel("🤖 AI Coder Setup Wizard", "Pojďme konfigurovat tvého AI asistenta")
    
    # Select provider
    providers = {
        "1": "Google Gemini",
        "2": "Groq",
        "3": "OpenAI",
        "4": "DeepSeek",
        "5": "Claude (Anthropic)"
    }
    
    provider_choice = ui.select_from_list(
        "Vyber AI poskytovatele",
        list(providers.values())
    )
    config["provider"] = provider_choice
    
    # API Key
    api_key = ui.text_input("Vlož API klíč (bude šifrován)")
    config["api_key"] = api_key
    
    # Features selection
    features = ui.select_multiple(
        "Jaké funkce chceš aktivovat?",
        ["File Management", "Code Generation", "Debugging", "Testing", "Optimization"]
    )
    config["features"] = features
    
    # Project settings
    project_name = ui.text_input("Jméno projektu", default="my_project")
    config["project_name"] = project_name
    
    # Confirmation
    if ui.confirm("Potvrdit nastavení?"):
        ui.success_message("Nastavení uloženo!")
        return config
    else:
        ui.info_message("Zrušeno")
        return {}


def demo_interactive_ui():
    """Demo interactive UI features"""
    ui = InteractiveUI()
    
    print("\n" + "="*60)
    print("🎮 DEMO - Interactive UI Features")
    print("="*60)
    
    # Demo 1: Simple selection
    print("\n[1] List Selection with Arrows")
    choice = ui.select_from_list(
        "Vyber jednu možnost",
        ["Option A", "Option B", "Option C", "Option D"]
    )
    ui.success_message(f"Vybrali jste: {choice}")
    
    # Demo 2: Multiple selection
    print("\n[2] Multiple Selection")
    selections = ui.select_multiple(
        "Vyber více možností",
        ["Feature 1", "Feature 2", "Feature 3", "Feature 4"]
    )
    ui.info_message(f"Vybrali jste: {', '.join(selections)}")
    
    # Demo 3: Text input
    print("\n[3] Text Input")
    name = ui.text_input("Jak se jmenuješ?", default="User")
    ui.success_message(f"Ahoj {name}!")
    
    # Demo 4: Confirmation
    print("\n[4] Confirmation")
    if ui.confirm("Chceš pokračovat?"):
        ui.success_message("Pokračujem!")
    else:
        ui.info_message("OK, zatím")
    
    # Demo 5: Table
    print("\n[5] Formatted Table")
    ui.show_table(
        "📊 Dostupné modely",
        ["ID", "Model", "Status"],
        [
            ["1", "GPT-4", "🟢 Ready"],
            ["2", "Claude 3.5", "🟢 Ready"],
            ["3", "Gemini Pro", "🔴 Need Key"],
        ]
    )
    
    # Demo 6: Messages
    print("\n[6] Status Messages")
    ui.success_message("Vše funguje!")
    ui.error_message("Něco se pokazilo")
    ui.info_message("Užitečná informace")
    ui.progress_message("Pracuji na tom...")
    
    print("\n" + "="*60)
    print("✅ Demo finished!")
    print("="*60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_interactive_ui()
    elif len(sys.argv) > 1 and sys.argv[1] == "setup":
        config = run_interactive_setup()
        print("\nVýsledný config:")
        for k, v in config.items():
            print(f"  {k}: {v}")
    else:
        print("Použití:")
        print("  python interactive_ui.py demo    - Demo všech funkcí")
        print("  python interactive_ui.py setup   - Interaktivní setup")
