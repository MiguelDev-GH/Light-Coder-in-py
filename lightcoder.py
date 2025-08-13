import os
import sys
import platform
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, font, ttk
from PIL import Image, ImageDraw, ImageTk
import subprocess
import threading

class CodeEditor:
    COLOR_BLACK = "#1B1B1B"
    COLOR_DARK_GRAY = "#252525"
    COLOR_MEDIUM_GRAY = "#2D2D2D"
    COLOR_LIGHT_GRAY_TEXT = "#E0E0E0"
    COLOR_INACTIVE_TEXT = "#888888"
    COLOR_SEPARATOR = "#3D3D3D"
    COLOR_SELECTION = "#454545"
    COLOR_ORANGE = "#E8A14F"
    COLOR_GREEN = "#50A14F"
    COLOR_ERROR_TEXT = "#FF5555"

    def __init__(self, root):
        self.root = root
        self.root.title("Light Coder v10.2")
        self.root.geometry("1200x800")

        ctk.set_appearance_mode("Dark")
        self.root.configure(fg_color=self.COLOR_BLACK)
        
        self._line_count = 1
        self.current_file = None
        self.root_path = os.getcwd()
        self.active_tree_item = None
        self.last_saved_item = None
        
        self.status_images = {}

        self.setup_fonts()
        self.load_icons()
        self.setup_ui_style()
        self.setup_ui()
        self.create_menu()
        self.setup_key_bindings()
        
        self._update_line_numbers()

    def setup_fonts(self):
        self.main_font = ctk.CTkFont(family="Consolas", size=13)
        self.label_font = ctk.CTkFont(family="Segoe UI", size=12)

    def load_icons(self):
        try:
            folder_img = Image.new('RGBA', (20, 20), (0, 0, 0, 0)); draw_folder = ImageDraw.Draw(folder_img)
            folder_path = [(3, 5), (3, 15), (17, 15), (17, 7), (9, 7), (8, 5)]; draw_folder.polygon(folder_path, fill=self.COLOR_ORANGE, outline=self.COLOR_ORANGE)
            self.base_folder_icon = folder_img
            self.folder_icon = ImageTk.PhotoImage(self.base_folder_icon)

            file_img = Image.new('RGBA', (20, 20), (0, 0, 0, 0)); draw_file = ImageDraw.Draw(file_img)
            file_path = [(5, 3), (5, 17), (15, 17), (15, 6), (10, 3), (5,3)]; draw_file.polygon(file_path, fill=self.COLOR_LIGHT_GRAY_TEXT, outline=self.COLOR_LIGHT_GRAY_TEXT)
            self.base_file_icon = file_img
            self.file_icon = ImageTk.PhotoImage(self.base_file_icon)

            play_img = Image.new('RGBA', (20, 20), (0, 0, 0, 0)); draw_play = ImageDraw.Draw(play_img)
            play_path = [(5, 5), (5, 15), (15, 10)]; draw_play.polygon(play_path, fill=self.COLOR_LIGHT_GRAY_TEXT)
            self.play_icon = ImageTk.PhotoImage(play_img)
        except Exception as e:
            print(f"Aviso: Não foi possível carregar os ícones - {e}"); self.folder_icon = None; self.file_icon = None; self.play_icon = None

    def create_status_icon(self, base_icon, status):
        img = base_icon.copy()
        draw = ImageDraw.Draw(img)
        
        if status == 'dirty':
            color = self.COLOR_ORANGE
        elif status == 'saved':
            color = self.COLOR_GREEN
        else:
            return ImageTk.PhotoImage(img)

        bbox = (13, 13, 20, 20)
        draw.ellipse(bbox, fill=color, outline=self.COLOR_DARK_GRAY)

        return ImageTk.PhotoImage(img)

    def update_item_icon(self, item_id, status=None):
        if not item_id or not self.file_tree.exists(item_id):
            return

        item_path = self.file_tree.item(item_id, "values")[0]
        base_icon = self.base_folder_icon if os.path.isdir(item_path) else self.base_file_icon
        
        new_icon = self.create_status_icon(base_icon, status)
        self.file_tree.item(item_id, image=new_icon)
        self.status_images[item_id] = new_icon

    def setup_ui_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=self.COLOR_DARK_GRAY, foreground=self.COLOR_LIGHT_GRAY_TEXT, fieldbackground=self.COLOR_DARK_GRAY, borderwidth=0, relief='flat', rowheight=25)
        style.map('Treeview', background=[('selected', self.COLOR_SELECTION)])
        style.configure("Treeview.Heading", background=self.COLOR_DARK_GRAY, foreground=self.COLOR_LIGHT_GRAY_TEXT, relief="flat")
        style.map("Treeview.Heading", background=[('active', self.COLOR_DARK_GRAY)])
        self.file_tree_style = style

    def _on_mousewheel(self, event):
        self.text_editor.yview_scroll(-1 * (event.delta // 120), "units")
        self.line_numbers.yview_scroll(-1 * (event.delta // 120), "units")
        return "break"

    def _on_scrollbar(self, *args):
        self.text_editor.yview(*args)
        self.line_numbers.yview(*args)

    def _update_line_numbers(self, event=None):
        final_index = self.text_editor.index("end"); new_line_count = int(final_index.split('.')[0]) - 1
        if self._line_count == new_line_count: return
        self._line_count = new_line_count
        if self._line_count == 0: self._line_count = 1
        line_numbers_string = "\n".join(str(i) for i in range(1, self._line_count + 1))
        self.line_numbers.configure(state="normal"); self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", line_numbers_string); self.line_numbers.configure(state="disabled")

    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1); self.root.grid_columnconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent"); main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        self.file_name_label = ctk.CTkLabel(main_frame, text="[Nenhum arquivo aberto]", font=self.label_font, text_color=self.COLOR_INACTIVE_TEXT, anchor="w")
        self.file_name_label.grid(row=0, column=1, sticky="ew", pady=(0, 5), padx=(10, 0))

        left_panel = ctk.CTkFrame(main_frame, width=300, fg_color=self.COLOR_DARK_GRAY); left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10)); left_panel.grid_propagate(False)
        left_panel.grid_rowconfigure(0, weight=1); left_panel.grid_columnconfigure(0, weight=1)
        self.file_tree = ttk.Treeview(left_panel, show="tree", selectmode="browse"); self.file_tree.grid(row=0, column=0, sticky='nsew')
        
        editor_frame = ctk.CTkFrame(main_frame, fg_color="transparent"); editor_frame.grid(row=1, column=1, sticky="nsew")
        editor_frame.grid_rowconfigure(0, weight=1); editor_frame.grid_columnconfigure(1, weight=1)
        self.scrollbar = ctk.CTkScrollbar(editor_frame, command=self._on_scrollbar); self.scrollbar.grid(row=0, column=2, sticky="ns")
        self.line_numbers = ctk.CTkTextbox(editor_frame, width=40, font=self.main_font, fg_color=self.COLOR_MEDIUM_GRAY, text_color=self.COLOR_INACTIVE_TEXT, state="disabled", activate_scrollbars=False, yscrollcommand=self.scrollbar.set)
        self.line_numbers.grid(row=0, column=0, sticky="ns", padx=(0, 5))
        self.text_editor = ctk.CTkTextbox(editor_frame, font=self.main_font, fg_color=self.COLOR_DARK_GRAY, text_color=self.COLOR_LIGHT_GRAY_TEXT, undo=True, border_width=0, activate_scrollbars=False, yscrollcommand=self.scrollbar.set)
        self.text_editor.grid(row=0, column=1, sticky="nsew")

        command_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        command_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        command_frame.grid_columnconfigure(0, weight=1)
        self.command_entry = ctk.CTkEntry(command_frame, font=self.main_font, fg_color=self.COLOR_DARK_GRAY, text_color=self.COLOR_LIGHT_GRAY_TEXT, border_width=0)
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.command_entry.bind("<Return>", self.on_run_button_click)
        self.run_button = ctk.CTkButton(command_frame, text="", image=self.play_icon, width=30, command=self.on_run_button_click)
        self.run_button.grid(row=0, column=1)

        self.text_editor.bind("<MouseWheel>", self._on_mousewheel)
        self.text_editor.bind("<KeyRelease>", self.on_text_change)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)
        self.file_tree.bind("<<TreeviewOpen>>", self.on_tree_expand)

    def on_text_change(self, event=None):
        if self.text_editor.edit_modified():
            if self.active_tree_item:
                if self.active_tree_item == self.last_saved_item:
                    self.last_saved_item = None
                self.update_item_icon(self.active_tree_item, 'dirty')
            self.text_editor.edit_modified(False)
        
        self._update_line_numbers()
        # LINHA ADICIONADA PARA O AUTOSCROLL
        self.text_editor.see("insert")

    def create_menu(self):
        menu_bar = tk.Menu(self.root); self.root.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.config(bg=self.COLOR_BLACK, fg=self.COLOR_LIGHT_GRAY_TEXT, activebackground=self.COLOR_SELECTION, activeforeground=self.COLOR_ORANGE, selectcolor=self.COLOR_ORANGE, borderwidth=0)
        file_menu.config(bg=self.COLOR_DARK_GRAY, fg=self.COLOR_LIGHT_GRAY_TEXT, activebackground=self.COLOR_SELECTION, activeforeground=self.COLOR_LIGHT_GRAY_TEXT, borderwidth=0)
        menu_bar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Abrir Pasta...", command=self.open_folder)
        file_menu.add_command(label="Salvar", command=self.save_file)
        file_menu.add_command(label="Salvar Como...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)

    def setup_key_bindings(self):
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Command-s>", lambda event: self.save_file())
        self.text_editor.bind("<<Paste>>", self.on_text_change)
        self.text_editor.bind("<<Cut>>", self.on_text_change)

    def populate_tree(self, node, path):
        for child in self.file_tree.get_children(node): self.file_tree.delete(child)
        try:
            items = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
            for item in items:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    child_node = self.file_tree.insert(node, 'end', text=f" {item}", values=[full_path], image=self.folder_icon, open=False)
                    self.file_tree.insert(child_node, 'end', text="...")
                else: self.file_tree.insert(node, 'end', text=f" {item}", values=[full_path], image=self.file_icon)
        except OSError: pass

    def on_tree_expand(self, event):
        node_id = self.file_tree.focus()
        path = self.file_tree.item(node_id, "values")[0]
        self.populate_tree(node_id, path)

    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path: return
        self.root_path = folder_path
        os.chdir(self.root_path)
        self.file_tree.delete(*self.file_tree.get_children())
        self.last_saved_item = None
        self.status_images.clear()
        root_node = self.file_tree.insert('', 'end', text=f" {os.path.basename(folder_path)}", values=[folder_path], image=self.folder_icon, open=True)
        self.populate_tree(root_node, folder_path)
    
    def on_file_select(self, event):
        if not self.file_tree.selection(): return
        selected_id = self.file_tree.selection()[0]
        try:
            file_path = self.file_tree.item(selected_id, "values")[0]
            if os.path.isfile(file_path):
                self.active_tree_item = selected_id
                self.open_file(file_path)
        except (IndexError, FileNotFoundError):
            pass

    def open_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file: content = file.read()
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", content)
            self.text_editor.edit_modified(False)
            self.current_file = file_path
            self.file_name_label.configure(text=os.path.basename(file_path), text_color=self.COLOR_LIGHT_GRAY_TEXT)
            self._update_line_numbers()
        except Exception as e:
            self.file_name_label.configure(text=f"Erro ao abrir: {e}", text_color="red")

    def save_file(self):
        if self.current_file:
            try:
                content = self.text_editor.get("1.0", "end-1c")
                with open(self.current_file, "w", encoding="utf-8") as file: file.write(content)
                self.text_editor.edit_modified(False)
                self.file_name_label.configure(text=os.path.basename(self.current_file), text_color=self.COLOR_LIGHT_GRAY_TEXT)
                if self.active_tree_item:
                    if self.last_saved_item and self.last_saved_item != self.active_tree_item:
                        self.update_item_icon(self.last_saved_item, None)
                    self.update_item_icon(self.active_tree_item, 'saved')
                    self.last_saved_item = self.active_tree_item
            except Exception as e:
                self.file_name_label.configure(text=f"Erro ao salvar: {e}", text_color="red")
        else: self.save_as_file()

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("All Files", "*.*"), ("Text Documents", "*.txt"), ("Python Files", "*.py")])
        if not file_path: return
        try:
            content = self.text_editor.get("1.0", "end-1c")
            with open(file_path, "w", encoding="utf-8") as file: file.write(content)
            self.text_editor.edit_modified(False)
            self.current_file = file_path
            self.file_name_label.configure(text=os.path.basename(self.current_file), text_color=self.COLOR_LIGHT_GRAY_TEXT)
            self.open_folder()
        except Exception as e:
            self.file_name_label.configure(text=f"Erro ao salvar: {e}", text_color="red")

    def execute_in_external_terminal(self, command):
        try:
            current_os = platform.system()
            if current_os == "Windows":
                subprocess.Popen(f'start cmd /k "{command}"', shell=True)
            elif current_os == "Darwin":
                escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
                script = f'tell application "Terminal" to do script "{escaped_command}"'
                subprocess.Popen(['osascript', '-e', script])
            else:
                try:
                    subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'{command}; exec bash'])
                except FileNotFoundError:
                    try:
                        subprocess.Popen(['konsole', '-e', 'bash', '-c', f'{command}; exec bash'])
                    except FileNotFoundError:
                        subprocess.Popen(['xterm', '-e', 'bash', '-c', f'{command}; exec bash'])
        except Exception as e:
            print(f"Failed to open external terminal: {e}")

    def on_run_button_click(self, event=None):
        command = self.command_entry.get()
        if command:
            self.execute_in_external_terminal(command)

if __name__ == "__main__":
    root = ctk.CTk()
    editor = CodeEditor(root)
    root.mainloop()