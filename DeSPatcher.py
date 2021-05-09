import hashlib
import json
import os
import sys
import tkinter.filedialog
import tkinter as tk

from diff_match_patch import diff_match_patch
from shutil import copyfile, move

BASE_DIR = os.path.dirname(sys.argv[0])

DATA_PATH = os.path.join(BASE_DIR, 'data.json')
if os.path.isfile(DATA_PATH):
    with open('data.json', 'r') as f:
        DATA = json.loads(f.read())
else:
    DATA = {
        'root-dir': BASE_DIR,
        'window': {
            'width': 750,
            'height': 540
        }
    }

SCRIPT_DIR = os.path.join(DATA['root-dir'], 'script').replace('\\', '/')

DMP = diff_match_patch()

log_text = ''


def log_and_print(text):
    global log_text
    print(text)
    log_text += text + '\n'


def get_mods():
    mod_dir = os.path.join(BASE_DIR, 'mods')
    mods = []
    if not os.path.isdir(mod_dir):
        os.mkdir(mod_dir)
        return mods
    subdir_names = [f for f in os.listdir(mod_dir) if os.path.isdir(os.path.join(mod_dir, f))]
    for subdir_name in subdir_names:
        subdir = os.path.join(mod_dir, subdir_name)
        data_file = os.path.join(subdir, 'data.json')
        if not os.path.isfile(data_file):
            continue
        with open(data_file, 'r') as f:
            mod = json.load(f)
            mod['patch-name'] = subdir_name
            mods.append(mod)
    return mods


def generate_patches(log_var):
    global log_text
    log_text = ''
    data_file = tkinter.filedialog.askopenfile(filetypes=[('Mod data file', '*.json')])
    if not data_file:
        return None
    data_path = data_file.name
    data = json.load(data_file)
    patch_dir = os.path.dirname(data_path)
    for dir_name in data['files']:
        files = data['files'][dir_name]
        for file_name in files:
            modified_path = os.path.join(DATA['root-dir'], dir_name, file_name)
            bak_path = modified_path + '.bak'
            patch_name = f'{dir_name}---{file_name}.patch'
            if create_patch(bak_path, modified_path, 'hex', patch_dir, patch_name) is None:
                continue
            unmodified_hash = get_hash(bak_path)
            modified_hash = get_hash(modified_path)
            data['files'][dir_name][file_name] = [unmodified_hash, modified_hash]
    data_file.close()
    with open(data_path, 'w+') as f:
        json.dump(data, f, indent=2)

    log_var.set(log_text)


def ask_open_file():
    file = tk.filedialog.askopenfile()
    if file:
        file_name = file.name
        file.close()
        return file_name
    else:
        file.close()
        return None


def generate_manual_patch(mode='hex'):
    unmodified_file_path = ask_open_file()
    modified_file_path = ask_open_file()
    if not all([unmodified_file_path, modified_file_path]):
        return None
    else:
        create_patch(unmodified_file_path, modified_file_path, mode)
        
        
def load_file(path, patch_mode):
    _, name = os.path.split(path)
    try:
        data = None
        if patch_mode == 'hex':
            with open(path, 'rb') as f:
                data = f.read().hex()
        if patch_mode == 'text':
            with open(path, 'r', encoding='shiftjis') as f:
                data = f.read()
        return data
    except FileNotFoundError:
        log_and_print(f'Unmodified file not found: {name}')
        return None


def create_patch(unmodified, modified, patch_mode, mod_dir=None, patch_name=None):
    unmodified_data = load_file(unmodified, patch_mode)
    modified_data = load_file(modified, patch_mode)

    if not all([unmodified_data, modified_data]):
        return None

    patches = DMP.patch_make(unmodified_data, modified_data)
    diff = DMP.patch_toText(patches)

    path, name = os.path.split(modified)
    if mod_dir is None:
        mod_dir = path
    if patch_name is None:
        patch_name = os.path.split(name)[1].split('.')[0] + '.patch'
    if not os.path.isdir(mod_dir):
        os.mkdir(mod_dir)

    patch_path = os.path.join(mod_dir, patch_name)
    with open(patch_path, 'w+') as f:
        f.write(diff)

    log_and_print(f'Patch file generated: {os.path.split(path)[1]}/{patch_name}')


def get_hash(filepath):
    sha = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(sha.block_size)
            if not data:
                break
            sha.update(data)
    return sha.hexdigest()


def check_patchable(file_path, hash_list, mod_hash, patch_path):
    global log_text
    _, file_name = os.path.split(file_path)
    if not os.path.isfile(file_path):
        log_and_print(f'{file_name} not found, skipping')
        return False
    else:
        hash = get_hash(file_path)
        if hash not in hash_list:  # file is not in its expected default state
            if hash == mod_hash:
                log_and_print(f'{file_name} already patched, skipping file')
            else:
                log_and_print(f'{file_name} is not in it\'s default state, please remove patches first')
            return False
    if not os.path.isfile(patch_path):
        _, patch_name = os.path.split(patch_path)
        log_and_print(f'{patch_name} not found, skipping file')
        return False
    return True


def patch_file(unmodified_path, patch_path, *_):
    global log_text
    _, unmodified_name = os.path.split(unmodified_path)
    unmodified_bak_path = unmodified_path + '.bak'
    unmodified_bak_name = unmodified_name + '.bak'
    with open(unmodified_path, 'rb') as f:
        unmodified_data = f.read().hex()
    if os.path.isfile(unmodified_bak_path):
        log_and_print(f'{unmodified_bak_name} already exists, not overwriting')
    else:
        copyfile(unmodified_path, unmodified_bak_path)
    with open(patch_path, 'r') as f:
        patch_data = f.read()
    patches = DMP.patch_fromText(patch_data)
    modified_data, _ = DMP.patch_apply(patches, unmodified_data)
    with open(unmodified_path, 'wb') as f:
        f.write(bytes.fromhex(modified_data))
        log_and_print(f'Applying patch to {unmodified_name}')


def save_data():
    with open('data.json', 'w+') as f:
        json.dump(DATA, f, indent=4)


# -------------------------------------------------------------
# ----------------------- W I D G E T S -----------------------
# -------------------------------------------------------------

def get_geometry(settings):
    if all([(key in settings['window']) for key in ['x', 'y']]):
        geometry = '{}x{}+{}+{}'.format(
            settings['window']['width'], settings['window']['height'],
            settings['window']['x'], settings['window']['y']
        )
    else:
        geometry = '{}x{}'.format(
            settings['window']['width'],
            settings['window']['height']
        )
    return geometry


def config_grids(widget, rows=None, columns=None):
    if rows is None:
        rows = [1]
    if columns is None:
        columns = [1]
    [widget.rowconfigure(i, weight=w) for i, w in enumerate(rows)]
    [widget.columnconfigure(i, weight=w) for i, w in enumerate(columns)]


def update_button(widget, text, state='normal'):
    widget.config(text=f'{widget.default_text} {text}', state=state)


def update_text(widget, text):
    widget.config(state='normal')
    widget.delete('1.0', 'end')
    widget.insert('end', text)
    widget.config(state='disabled')


def close_window(root):
    w = root.winfo_width()
    h = root.winfo_height()
    x = root.winfo_x()
    y = root.winfo_y()
    DATA['window'] = {
        'width': w,
        'height': h + 20,
        'x': x,
        'y': y
    }
    save_data()
    root.destroy()


class Menubar(tk.Menu):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.file_menu = tk.Menu(self, tearoff=0)

        self.file_menu.add_command(label='Restart', command=self.master.restart)
        self.file_menu.add_command(label='Quit', command=self.master.quit)

        self.mods_menu = tk.Menu(self, tearoff=0)
        self.mods_menu.add_command(label='Generate patches', command=lambda: generate_patches(self.master.log_var))
        self.mods_menu.add_command(label='Manual hex patch', command=generate_manual_patch)
        self.mods_menu.add_command(label='Manual text patch', command=lambda: generate_manual_patch('text'))

        self.mods_menu.add_separator()

        self.mods_menu.add_command(label='Refresh mods', command=self.populate_mods_menu)
        # self.add_cascade(label='File', menu=self.file_menu)
        self.add_cascade(label='Mods', menu=self.mods_menu)

        self.mods_menu.add_separator()
        self.populate_mods_menu()

    def populate_mods_menu(self):
        self.master.mods = get_mods()
        self.master.set_mod(self.master.mods[0]['patch-name'])
        if not self.master.mods:
            self.mods_menu.add_command(label='No mods found', command=lambda: None, state='disabled')
        for mod in self.master.mods:
            label = mod['patch-name']
            self.mods_menu.add_command(label=label, command=lambda: self.master.set_mod(label))


class MainWindow(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master

        font = {'font': 'Calibri 11'}

        self.config(bg='gray20')

        self.master.title('Demon\'s Souls Patcher')

        self.pack(fill='both', expand=True)

        config_grids(self, rows=[1, 0, 0, 0, 0], columns=[1, 0])

        self.restart_flag = False

        self.mod_frame = tk.Frame(self, bg='gray20')
        self.mod_frame.grid(row=0, column=0, columns=2, sticky='nsew')

        self.selected_mod_label = tk.Text(
            self.mod_frame, bg='gray20', fg='gray90', **font, wrap='word', state='disabled', height=2
        )
        self.selected_mod_label.insert(tk.END, 'Select a mod from the menu above')
        self.selected_mod_label.grid(row=0, column=0, sticky='new')

        self.description_label = tk.Text(
            self.mod_frame, bg='gray20', fg='gray90', **font, wrap='word', state='disabled'
        )
        self.description_label.grid(row=1, column=0, sticky='new')

        config_grids(self.mod_frame, rows=[0, 1])

        self.log_frame = tk.Frame(self, bg='gray30')
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')

        config_grids(self.log_frame)

        self.log_var = tk.StringVar()
        self.log_var.set('Browse to the game\'s script directory (PS3_GAME/USRDIR/script),\nand then apply patches')

        self.log_label = tk.Label(
            self.log_frame, bg='gray30', fg='gray90', textvariable=self.log_var,
            padx=10, pady=10, justify='left', **font
        )
        self.log_label.grid(row=0, column=0, sticky='nsew')

        self.dir_var = tk.StringVar()
        self.dir_var.set(SCRIPT_DIR if SCRIPT_DIR else BASE_DIR)
        self.dir_var.trace('w', self.check_dir)

        self.dir_entry = tk.Entry(self, textvariable=self.dir_var)
        self.dir_entry.grid(
            row=2, column=0, sticky='nsew', padx=(10, 10), pady=(10, 10)
        )

        button_style = {'relief': 'flat', 'pady': 10, 'bg': 'gray80'}
        button_grid = {
            'sticky': 'nsew', 'padx': (10, 10),
            'pady': (10, 10)
        }

        self.dir_browse_button = tk.Button(
            self, text='Browse', command=self.browse_directory,
            relief='flat', pady=2, bg='gray80'
        )
        self.dir_browse_button.grid(row=2, column=1, **button_grid)

        self.apply_patches_button = tk.Button(
            self, text='', command=self.apply_patches,
            **button_style
        )
        self.apply_patches_button.default_text = 'Apply patches'
        self.apply_patches_button.grid(
            row=3, column=0, columnspan=2, **button_grid
        )

        self.remove_patches_button = tk.Button(
            self, text='', command=self.remove_patches,
            **button_style
        )
        self.remove_patches_button.default_text = 'Remove patches'
        self.remove_patches_button.grid(
            row=4, column=0, columnspan=2, **button_grid
        )

        self.mod = None

        self.mod_creation_window = None

        self.menu_bar = Menubar(self)
        self.master.config(menu=self.menu_bar)

        self.check_dir()

        if 'window' not in DATA:
            self.master.geometry('640x480')
        else:
            self.master.geometry(get_geometry(DATA))

    def set_mod(self, mod_name):
        mod = next((m for m in self.mods if m['patch-name'] == mod_name), None)
        self.mod = mod

        name = ''
        if 'name' in self.mod:
            name = self.mod['name']
        self.selected_mod_label.config(state='normal')
        update_text(self.selected_mod_label, f'Current mod: {name}')

        description = ''
        if 'description' in self.mod:
            description = self.mod['description']
        update_text(self.description_label, description)

        self.check_dir()

    def browse_directory(self):
        directory = tk.filedialog.askdirectory(initialdir=BASE_DIR)
        if os.path.isdir(directory):
            self.dir_var.set(directory)

    def apply_patches(self):
        global log_text
        log_text = ''

        if not self.check_dir():
            print('Error')
            return '\nERROR\n'

        for path_name in self.mod['files']:
            root_dir = DATA['root-dir']
            patch_dir = os.path.join(BASE_DIR, 'mods', self.mod['patch-name'])
            file_dir = os.path.join(root_dir, path_name)
            patches = self.mod['files'][path_name]
            for file_name in patches:
                file_path = os.path.join(file_dir, file_name)
                default_hash, modified_hash = patches[file_name]
                patch_path = os.path.join(patch_dir, f'{path_name}---{file_name}.patch')

                patchable = check_patchable(file_path, default_hash, modified_hash, patch_path)
                if patchable is False:
                    continue

                patch_file(file_path, patch_path)

        log_text += 'Done'
        self.log_var.set(log_text)

        self.check_dir()

    def remove_patches(self):
        global log_text
        log_text = ''

        if not self.check_dir():
            print('Error')
            return '\nERROR\n'

        self.log_var.set(log_text)

        for path_name in self.mod['files']:
            root_dir = DATA['root-dir']
            file_dir = os.path.join(root_dir, path_name)
            patches = self.mod['files'][path_name]
            for file_name in patches:
                file_path = os.path.join(file_dir, file_name)
                bak_name = file_name + '.bak'
                bak_path = file_path + '.bak'
                if not os.path.isfile(bak_path):
                    print(f'Missing backup file {bak_name}')
                    log_text += f'Missing backup file {bak_name}\n'
                else:
                    move(bak_path, file_path)
                    print(f'Restored {file_name}')
                    log_text += f'Restored {file_name}\n'

        log_text += 'Done'
        self.log_var.set(log_text)

        self.check_dir()

    def check_dir(self, *_):
        dir = self.dir_var.get()
        self.dir_entry.xview('end')

        successful = False

        if not os.path.isdir(dir):
            update_button(self.apply_patches_button, '(invalid directory)', 'disabled')
            update_button(self.remove_patches_button, '(invalid directory)', 'disabled')
            return False

        if dir != DATA['root-dir']:
            DATA['root-dir'], _ = os.path.split(dir)
            save_data()

        active_files, backups = [], []
        for dir_name in self.mod['files']:
            dir = os.path.join(DATA['root-dir'], dir_name)
            file_names = self.mod['files'][dir_name]
            for file_name in file_names:
                file_path = os.path.join(dir, file_name)
                active_files.append(os.path.isfile(file_path))
                bak_path = file_path + '.bak'
                backups.append(os.path.isfile(bak_path))

        if any(active_files):
            update_button(self.apply_patches_button, '(backups will be generated)')
            successful = True
        else:
            update_button(self.apply_patches_button, '(files to patch not found)', 'disabled')

        if not self.mod:
            update_button(self.apply_patches_button, '(no mod selected)')

        if any(backups):
            update_button(self.remove_patches_button, '(return game to retail state)')
            successful = True
        else:
            update_button(self.remove_patches_button, '(backup files not found)', 'disabled')

        return successful

    def quit(self):
        close_window(self.master)
        # self.master.destroy()

    def restart(self):
        self.quit()
        self.restart_flag = True


if __name__ == '__main__':
    root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', lambda: close_window(root))
    root.iconbitmap(os.path.join(BASE_DIR, 'icon.ico'))
    window = MainWindow(root)
    root.mainloop()

    if window.restart_flag:
        os.system(__file__)
