import tkinter as tk
from tkinter import ttk, filedialog
import os
import customtkinter as ctk

class ExactMinimalistCTkEditor(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Paleta de Cores da Imagem ---
        self.APP_BG = "#1c1c1c"
        self.FG_PRIMARY = "#e3e3e3"
        self.FG_SECONDARY = "#8f9094"
        self.BUTTON_BG = "#333333"
        self.BUTTON_HOVER_BG = "#3c3c3c"
        self.SELECTION_BG = "#3c3c3c"
        self.CLOSE_RED = "#e81123"
        self.CLOSE_RED_HOVER = "#f15562"
        self.DIVIDER_COLOR = "#3c3c3c"

        # --- Configuração da Janela ---
        self.overrideredirect(True)
        self.geometry("1200x750+100+100")
        self.configure(fg_color=self.APP_BG)

        self._offset_x = 0
        self._offset_y = 0

        self.current_file_path = None
        self.bind("<Control-s>", self.save_file)

        self.create_widgets()
        self.update_file_path_display()
        
        self.setup_taskbar_icon()

    def setup_taskbar_icon(self):
        self.icon_window = tk.Toplevel(self)
        self.icon_window.title("Editor de Código Minimalista")
        
        # self.icon_window.iconbitmap("seu_icone.ico")
        
        self.wm_transient(self.icon_window)
        self.icon_window.withdraw()
        self.icon_window.bind("<Map>", self.on_restore)
        self.icon_window.bind("<Unmap>", self.on_minimize)

    def on_restore(self, event):
        self.deiconify()

    def on_minimize(self, event):
        self.withdraw()

    def create_widgets(self):
        # --- Barra Superior Customizada ---
        top_frame = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="transparent")
        top_frame.pack(side="top", fill="x", padx=4, pady=4)
        top_frame.pack_propagate(False)

        self.file_path_label = ctk.CTkLabel(top_frame, text="", anchor="w", fg_color="transparent")
        self.file_path_label.pack(side="left", padx=10, fill="both", expand=True)
        
        close_button = ctk.CTkButton(
            top_frame,
            text="\u2715",
            command=self.quit, 
            width=32,
            height=32,
            fg_color="transparent",
            hover_color=self.CLOSE_RED,
            text_color=self.FG_SECONDARY,
            font=("Segoe UI", 16)
        )
        close_button.pack(side="right")
        
        # Eventos para arrastar a janela
        top_frame.bind("<ButtonPress-1>", self.start_move)
        top_frame.bind("<ButtonRelease-1>", self.stop_move)
        top_frame.bind("<B1-Motion>", self.do_move)
        self.file_path_label.bind("<ButtonPress-1>", self.start_move)
        self.file_path_label.bind("<ButtonRelease-1>", self.stop_move)
        self.file_path_label.bind("<B1-Motion>", self.do_move)

        # --- Conteúdo Principal (dividido em dois) ---
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Painel Esquerdo (Explorador) ---
        left_pane = ctk.CTkFrame(main_frame, width=320, corner_radius=0, fg_color="transparent")
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(5,0), pady=5)
        left_pane.grid_propagate(False)
        left_pane.grid_rowconfigure(1, weight=1)
        
        open_folder_button = ctk.CTkButton(
            left_pane, text="Abrir Pasta", command=self.open_folder,
            fg_color=self.BUTTON_BG,
            hover_color=self.BUTTON_HOVER_BG,
            corner_radius=15,
            font=("Calibri", 13, "bold")
        )
        open_folder_button.grid(row=0, column=0, sticky="w", padx=15, pady=15)

        # --- Treeview (Explorador de Arquivos) ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=self.APP_BG,
                        foreground=self.FG_PRIMARY,
                        fieldbackground=self.APP_BG,
                        borderwidth=0,
                        rowheight=25)
        style.map("Treeview", background=[("selected", self.SELECTION_BG)])
        style.configure("Treeview.Heading", 
                        background=self.APP_BG, 
                        foreground=self.FG_SECONDARY,
                        font=("Calibri", 10, "bold"),
                        relief="flat")
        style.map("Treeview.Heading", background=[("active", self.APP_BG)])
        
        tree_frame = ctk.CTkFrame(left_pane, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5)

        self.file_tree = ttk.Treeview(tree_frame, style="Treeview")
        self.file_tree.heading("#0", text="Explorador", anchor="w")
        self.file_tree.pack(side="left", fill="both", expand=True)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)
        
        # --- Painel Direito (Editor) ---
        self.text_editor = ctk.CTkTextbox(
            main_frame, 
            corner_radius=0,
            fg_color=self.APP_BG,
            text_color=self.FG_PRIMARY,
            font=("Consolas", 14),
            wrap="none"
        )
        self.text_editor.grid(row=0, column=1, sticky="nsew", padx=(1, 5), pady=5)
    
    # --- MÉTODOS PARA MOVER A JANELA ---
    def start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def stop_move(self, event):
        self._offset_x = None
        self._offset_y = None

    def do_move(self, event):
        if self._offset_x is None:
            return
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")
    
    def update_file_path_display(self):
        if self.current_file_path:
            self.file_path_label.configure(text=self.current_file_path)
        else:
            self.file_path_label.configure(text="Nenhum arquivo aberto")

    def on_file_select(self, event=None):
        selected_item = self.file_tree.focus()
        if not selected_item: return

        item = self.file_tree.item(selected_item)
        if not item or not item["values"]: return
        
        file_path = item["values"][0]
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                
                self.text_editor.delete("1.0", "end")
                self.text_editor.insert("1.0", content)
                self.current_file_path = file_path
                self.update_file_path_display()
            except Exception:
                self.current_file_path = None
                self.update_file_path_display()

    def save_file(self, event=None):
        if not self.current_file_path: return
        try:
            content = self.text_editor.get("1.0", "end-1c")
            with open(self.current_file_path, "w", encoding="utf-8") as file:
                file.write(content)
        except Exception: pass
    
    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path: return
        
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
        except OSError: pass

if __name__ == "__main__":
    app = ExactMinimalistCTkEditor()
    app.mainloop()