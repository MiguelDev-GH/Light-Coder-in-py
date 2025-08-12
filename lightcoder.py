import tkinter as tk
from tkinter import ttk, filedialog
import os

class MinimalistEditor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.BG_COLOR = "#1e1e1e"
        self.FG_COLOR = "#d4d4d4"
        self.INACTIVE_FG_COLOR = "#6c6c6c"
        self.WIDGET_BG_COLOR = "#252526"
        self.SEPARATOR_COLOR = "#333333"
        self.SELECTION_BG = "#2a2d2e"

        self.overrideredirect(True)
        self.geometry("1200x700+100+100")
        self.configure(bg=self.BG_COLOR)

        self._offset_x = 0
        self._offset_y = 0

        self.create_styles()
        self.create_widgets()
        
        self.current_file_path = None
        self.bind("<Control-s>", self.save_file)
        self.update_file_path_display()

    def create_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        
        style.configure("TFrame", background=self.BG_COLOR)
        style.configure("TLabel", background=self.BG_COLOR, foreground=self.FG_COLOR)
        style.configure("TButton", 
            background=self.WIDGET_BG_COLOR, 
            foreground=self.FG_COLOR,
            borderwidth=0,
            relief="flat",
            padding=5
        )
        style.map("TButton", background=[("active", self.SEPARATOR_COLOR)])

        style.configure("Custom.TPanedwindow", background=self.BG_COLOR)
        
        style.configure("Treeview",
                        background=self.WIDGET_BG_COLOR,
                        foreground=self.FG_COLOR,
                        fieldbackground=self.WIDGET_BG_COLOR,
                        borderwidth=0,
                        relief="flat")
        style.map("Treeview", background=[("selected", self.SELECTION_BG)])
        
        style.configure("Treeview.Heading",
                        background=self.WIDGET_BG_COLOR,
                        foreground=self.FG_COLOR,
                        relief="flat",
                        font=('Calibri', 10, 'bold'))
        style.map("Treeview.Heading", relief=[("active", "groove"), ("pressed", "sunken")])
        
        style.configure("TSeparator", background=self.SEPARATOR_COLOR)

    def create_widgets(self):
        title_bar = ttk.Frame(self, style="TFrame")
        title_bar.pack(side="top", fill="x", ipady=5)

        self.file_path_label = ttk.Label(title_bar, text="", style="TLabel", foreground=self.INACTIVE_FG_COLOR)
        self.file_path_label.pack(side="left", padx=10)
        
        close_button = ttk.Button(title_bar, text="✕", command=self.quit, width=3, style="TButton")
        close_button.pack(side="right", padx=5)

        title_bar.bind("<ButtonPress-1>", self.start_move)
        title_bar.bind("<ButtonRelease-1>", self.stop_move)
        title_bar.bind("<B1-Motion>", self.do_move)
        self.file_path_label.bind("<ButtonPress-1>", self.start_move)
        self.file_path_label.bind("<ButtonRelease-1>", self.stop_move)
        self.file_path_label.bind("<B1-Motion>", self.do_move)

        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(side="top", fill="x")

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL, style="Custom.TPanedwindow")
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_pane = ttk.Frame(main_pane, style="TFrame", width=300)
        main_pane.add(left_pane, weight=1)

        explorer_header = ttk.Frame(left_pane, style="TFrame")
        explorer_header.pack(side="top", fill="x", pady=5)
        
        open_folder_button = ttk.Button(explorer_header, text="Abrir Pasta", command=self.open_folder)
        open_folder_button.pack(side="left", padx=10)

        self.file_tree = ttk.Treeview(left_pane, show="tree headings")
        self.file_tree.heading("#0", text="Explorador", anchor="w")
        self.file_tree.pack(side="left", fill=tk.BOTH, expand=True)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)
        
        right_pane = ttk.Frame(main_pane, style="TFrame")
        main_pane.add(right_pane, weight=4)

        self.text_editor = tk.Text(right_pane,
                                   background=self.BG_COLOR,
                                   foreground=self.FG_COLOR,
                                   insertbackground=self.FG_COLOR,
                                   selectbackground="#4a4a4a",
                                   selectforeground=self.FG_COLOR,
                                   borderwidth=0,
                                   highlightthickness=0,
                                   font=("Consolas", 12),
                                   undo=True,
                                   wrap="none",
                                   padx=10, pady=10)
        self.text_editor.pack(fill=tk.BOTH, expand=True)

    def start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def stop_move(self, event):
        self._offset_x = None
        self._offset_y = None

    def do_move(self, event):
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")
    
    def update_file_path_display(self):
        if self.current_file_path:
            self.file_path_label.config(text=self.current_file_path, foreground=self.FG_COLOR)
        else:
            self.file_path_label.config(text="[Nenhum arquivo aberto]", foreground=self.INACTIVE_FG_COLOR)

    def on_file_select(self, event=None):
        selected_item = self.file_tree.focus()
        if not selected_item:
            return

        file_path = self.file_tree.item(selected_item)["values"][0]
        
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                
                self.text_editor.delete("1.0", tk.END)
                self.text_editor.insert("1.0", content)
                self.current_file_path = file_path
                self.update_file_path_display()
            except Exception as e:
                self.current_file_path = None
                self.update_file_path_display()

    def save_file(self, event=None):
        if not self.current_file_path:
            return
        try:
            content = self.text_editor.get("1.0", tk.END)
            with open(self.current_file_path, "w", encoding="utf-8") as file:
                file.write(content)
        except Exception as e:
            pass
    
    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        self.populate_file_tree(folder_path)

    def populate_file_tree(self, folder_path):
        for i in self.file_tree.get_children():
            self.file_tree.delete(i)
        
        root_node = self.file_tree.insert("", "end", text=os.path.basename(folder_path), open=True, values=[folder_path])
        self._populate_tree_recursive(folder_path, root_node)

    def _populate_tree_recursive(self, path, parent_id):
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                item_id = self.file_tree.insert(parent_id, "end", text=item, open=False, values=[item_path])
                if os.path.isdir(item_path):
                    self._populate_tree_recursive(item_path, item_id)
        except OSError:
            pass

if __name__ == "__main__":
    app = MinimalistEditor()
    app.mainloop()