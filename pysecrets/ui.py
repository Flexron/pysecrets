import clipboard
import tkinter as tk
from tkinter import ttk
from ttkwidgets.autocomplete import AutocompleteCombobox

from pysecrets import constants, secrets


class KeySecretEntry:

    def __init__(self, root: tk.Tk, database: str, password: str):
        self.root = root
        # init ui widgets
        self.frm_database = ttk.Frame(self.root)
        self.database = ttk.Label(self.frm_database, text=f"{database}", font=("Ubuntu", 40))
        self.add_secret = ttk.Button(self.frm_database, text="Add secret", width=15, command=self.add_secret_ui)
        self.get_secret = ttk.Button(self.frm_database, text="Get secret", width=15, command=self.get_secret_ui)

        self.add_or_secret_frame = None
        self.get_secret_ui_display = False
        self.add_secret_ui_display = False

        self.storage = secrets.StorageManager(database)
        self.secrets = self.storage.load()
        if self.secrets is None:
            self.secrets = secrets.Secrets(database, password)
            self.right_password = True
        else:
            self.secrets.set_key(password)
            self.right_password = self.secrets.check_password()

    def init_ui(self):
        self.frm_database.pack(side=tk.TOP)
        self.database.pack()
        self.add_secret.pack(side=tk.RIGHT)
        self.get_secret.pack(side=tk.RIGHT)

    def insert_secret(self):
        key = self.key_entry.get()
        secret = self.secret_entry.get()
        if key != '':
            self.secrets[key] = secret
            self.storage.save(self.secrets)
            self.secret_entry.delete(0, 'end')
            self.key_entry.delete(0, 'end')

    def add_secret_ui(self):
        if self.add_secret_ui_display:
            return

        self._destroy_add_or_get_secret_ui()

        self.add_or_secret_frame = ttk.Frame(self.root)
        self.key_entry = ttk.Entry(self.add_or_secret_frame, justify="left", width=15)
        self.secret_entry = ttk.Entry(self.add_or_secret_frame, justify="left", width=30)
        self.insert_button = ttk.Button(self.add_or_secret_frame, text="Insert", command=self.insert_secret)

        self.add_or_secret_frame.pack(pady=(150, 0))
        self.key_entry.pack(side=tk.LEFT, pady=(0, 0))
        self.secret_entry.pack(side=tk.LEFT, pady=(0, 0))
        self.insert_button.pack(side=tk.LEFT, pady=(0, 0))

        self.add_secret_ui_display = True
        self.get_secret_ui_display = False

    def get_secret_ui(self):
        if self.get_secret_ui_display:
            return

        self._destroy_add_or_get_secret_ui()

        self.add_or_secret_frame = ttk.Frame(self.root)
        keys = self.secrets.list_keys()
        self.secret_combobox = AutocompleteCombobox(self.add_or_secret_frame, width=60, completevalues=keys)
        self.secret_combobox.bind("<KeyRelease>", self.confirm_selected_key, add="+")
        self.secret_combobox.bind("<<ComboboxSelected>>", self.get_secret_from_selected_key)

        self.add_or_secret_frame.pack(pady=(50, 0))
        self.secret_combobox.pack()

        self.add_secret_ui_display = False
        self.get_secret_ui_display = True

    def confirm_selected_key(self, event):
        if event.keysym == constants.KeyPressed.ENTER:
            self.get_secret_from_selected_key(event)

    def get_secret_from_selected_key(self, event):
        key = self.secret_combobox.get()
        if key in self.secrets.list_keys():
            secret = self.secrets[key]
        else:
            secret = ""

        entry = self.add_or_secret_frame.children.get('!entry', None)
        copy = self.add_or_secret_frame.children.get('!button', None)
        if entry is None:
            entry = ttk.Entry(self.add_or_secret_frame, justify="left", width=60)
            copy = ttk.Button(self.add_or_secret_frame, text="Copy", command=self.copy_secret)
        entry.config(state='enable')
        entry.delete(0, 'end')
        entry.insert(0, secret)
        entry.config(state='disabled')
        entry.pack(pady=(100, 0))
        copy.pack()

    def copy_secret(self):
        secret_value = self.add_or_secret_frame.children['!entry'].get()
        clipboard.copy(secret_value)

    def _destroy_add_or_get_secret_ui(self):
        if self.add_or_secret_frame:
            self.add_or_secret_frame.destroy()

    def destroy(self):
        self.frm_database.destroy()
        self._destroy_add_or_get_secret_ui()


class Login:

    def __init__(self, root: tk.Tk):
        self.frm = ttk.Frame(root, width=10, height=10)

        self.database_label = ttk.Label(self.frm, text="Database")
        self.database = ttk.Entry(self.frm, justify="left")

        self.password_label = ttk.Label(self.frm, text="Password")
        self.password = ttk.Entry(self.frm, justify="left", show="*")

    def init_ui(self):
        self.frm.pack(pady=(200, 0))

        self.database_label.pack()
        self.database.pack()

        self.password_label.pack()
        self.password.pack()

    def destroy(self):
        self.frm.destroy()

    def get_database(self):
        return self.database.get()

    def get_password(self):
        return self.password.get()


class App:

    def __init__(self):
        self.root = tk.Tk(screenName="secrets", className="secrets")
        self.root.geometry(f"{constants.UI.WIDTH}x{constants.UI.HEIGHT}")

        self.app_frm = ttk.Frame(self.root)
        self.login: Login
        self.secret: KeySecretEntry

    def _log_in(self, database_name, password):
        self.secret = KeySecretEntry(self.root, database_name, password)
        if self.secret.right_password:
            self.destroy()
            self.login.destroy()
            self.app_frm = ttk.Frame(self.root, width=10, height=10)
            #self.secret = KeySecretEntry(self.root, database_name, password)
            leave = ttk.Button(self.app_frm, text="Quit", command=self.log_out)
            self.secret.init_ui()
            self.app_frm.pack(side=tk.BOTTOM)
            leave.pack()

    def log_in(self):
        database = self.login.get_database()
        password = self.login.get_password()
        if database != "" and password != "":
            self._log_in(database.lower(), password)

    def log_in_via_enter_key(self, event):
        if event.keysym == constants.KeyPressed.ENTER:
            self.log_in()

    def log_out(self):
        self.destroy()
        self.secret.destroy()
        self.app_frm = ttk.Frame(self.root)
        self.init_ui()

    def init_ui(self):
        self.login = Login(self.root)
        enter = ttk.Button(self.app_frm, text="Enter", command=self.log_in)
        self.login.password.bind("<KeyPress>", self.log_in_via_enter_key)
        self.login.init_ui()
        self.app_frm.pack()
        enter.pack()
        self.login.database.focus_set()

    def mainloop(self):
        self.init_ui()
        self.root.mainloop()

    def destroy(self):
        self.app_frm.destroy()


app = App()
app.mainloop()

