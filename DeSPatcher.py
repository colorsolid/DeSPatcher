import hashlib
import json
import os
import sys
import tkinter.filedialog
import tkinter as tk

from diff_match_patch import diff_match_patch
from shutil import copyfile, move

try:
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
except NameError:
    BASE_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

FILE_NUMS = [1, 2, 3, 4, 5, 6, 8]

DATA_PATH = os.path.join(BASE_DIR, 'data.json')
if os.path.isfile(DATA_PATH):
    with open('data.json', 'r') as f:
        DATA = json.loads(f.read())
else:
    DATA = {}

if 'script-dir' not in DATA:
    DATA['script-dir'] = ''
SCRIPT_DIR = DATA['script-dir']

DEFAULT_HASHES = [
    [
        '753b3e80024c71336f01e1cae7f28cc1f527668cb9b9d1186eac35e9fe59c78c',
        '2e03737ffb6c81230946e4e209045b2c1c0c743eac8d949d506f6b0c23ba71bc'
    ],
    [
        'cae0b75b6f317adceb84713a0b9ec665ac197c6967fea32c3ca5485e8f9c3ae7',
        'd315761bc499a307b1f4b60f85cf338fc122db8cda43a9015b6163bd98880059'
    ],
    [
        '9a262026c4c62c349bcb34e828866467740b65e71f74d5d181c7c62bd5363f0e',
        'dd7be02320c81fddd90da278725d11eb2dc25870b02dff782a0531da3d891189'
    ],
    [
        '8a8d37ae77c70ccdf58744869d941957f4ea996e738f171685caa221adee5abf',
        'f93e98e18c5c5c981fc21fb2592b33c5d6997c05dfe85557f7a45ae2df047071'
    ],
    [
        '7878d9aead49e683a57247d133a63c6b5ec001547c9050cc8fbdcf6b24d049be',
        '425b07d98da7db0e586ffe5cc0ad9bb41047ecef22059bc1b190f73dbcbdbc0b'
    ],
    [
        '3238a4f554c48137e3e8953dd685ac7fc93fed6e86e79278b246c61cf66e32ca',
        '9fa313e61cea55a45a73fc128702e64a66e5d4be74a62a5d3a5bc09d0e0af713'
    ],
    [
        '3266881bf0fbe5a990ce0e1adf13f8dd22714d087aa5fa59f2e0830549f022ac'
        '120fead9a61067c7acbdc6dde154dff990136a14fe7f8a5cca2b1bfbeb9bb4dd'
    ]
]

DMP = diff_match_patch()

def get_hash(filepath):
    sha = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(sha.block_size)
            if not data:
                break
            sha.update(data)
    return sha.hexdigest()


def gen_patches(mod_name, window):
    hashes = {}
    mods_root_dir = os.path.join(BASE_DIR, 'mods')
    if not os.path.isdir(mods_root_dir):
        os.mkdir(mods_root_dir)
    mod_dir = os.path.join(BASE_DIR, 'mods', mod_name)
    for i, num in enumerate(FILE_NUMS):
        sdat_name = f'm0{num}.luabnd.dcx.sdat'
        sdat_path = os.path.join(SCRIPT_DIR, sdat_name)
        bak_path = sdat_path + '.bak'
        print(get_hash(sdat_path), DEFAULT_HASHES[i])
        if not os.path.isfile(sdat_path) \
        or not os.path.isfile(bak_path) \
        or get_hash(sdat_path) in DEFAULT_HASHES[i]:
            continue
        try:
            hashes[num] = get_hash(sdat_path)
            with open(sdat_path, 'rb') as f:
                modded_data = f.read().hex()
            with open(bak_path, 'rb') as f:
                unmodded_data = f.read().hex()
            patches = DMP.patch_make(unmodded_data, modded_data)
            diff = DMP.patch_toText(patches)
            patch_name = os.path.split(sdat_name)[1].split('.')[0] + '.patch'
            if not os.path.isdir(mod_dir):
                os.mkdir(mod_dir)
            patch_path = os.path.join(mod_dir, patch_name)
            with open(patch_path, 'w+') as f:
                f.write(diff)
        except FileNotFoundError as e:
            raise(e)
            print('file not found:', num)
    with open(os.path.join(mod_dir, 'data.json'), 'w+') as f:
        json.dump({'hashes': hashes}, f, indent=2)
    window.master.menu_bar.populate_mods_menu()
    window.destroy()


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
            mod['name'] = subdir_name
            mods.append(mod)
    return mods


def config_grids(widget, rows=[1], columns=[1]):
    [widget.rowconfigure(i, weight=w) for i, w in enumerate(rows)]
    [widget.columnconfigure(i, weight=w) for i, w in enumerate(columns)]


def resource_path(filename):
    try:
        base_dir = sys._MEIPASS
    except AttributeError:
        base_dir = BASE_DIR
    return os.path.join(base_dir, filename)


def save_data():
    with open('data.json', 'w+') as f:
        json.dump(DATA, f, indent=2)


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


def set_mod(mod_name, window):
    mod = next((m for m in window.mods if m['name'] == mod_name), None)
    window.selected_mod = mod
    window.selected_mod_label.config(text=f'Current mod: {mod_name}')
    description = ''
    if 'description' in window.selected_mod:
        description = window.selected_mod['description']
    window.description_label.config(text=description)
    window.check_dir()


# -------------------------------------------------------------
# -------------------- M A I N W I N D O W --------------------
# -------------------------------------------------------------


class Menubar(tk.Menu):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.file_menu = tk.Menu(self, tearoff=0)

        self.file_menu.add_command(label='Restart', command=self.master.restart)
        self.file_menu.add_command(label='Quit', command=self.master.quit)

        self.mods_menu = tk.Menu(self, tearoff=0)
        self.mods_menu.add_command(label='Refresh mods', command=self.populate_mods_menu)
        self.mods_menu.add_command(label='Generate patches', command=self.master.prompt_mod_name)

        # self.add_cascade(label='File', menu=self.file_menu)
        self.add_cascade(label='Mods', menu=self.mods_menu)

        self.mods_menu.add_separator()
        self.populate_mods_menu()


    def populate_mods_menu(self):
        self.master.mods = get_mods()
        self.mods_menu.delete(3, 'end')
        if not self.master.mods:
            self.mods_menu.add_command(label='No mods found', command=lambda: None, state='disabled')
        for mod in self.master.mods:
            label = mod['name']
            self.mods_menu.add_command(label=label, command=lambda label=label: set_mod(label, self.master))


class MainWindow(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master

        font = {'font': 'Consolas 11'}

        self.config(bg='gray20')

        self.master.title('Demon\'s Souls Patcher')

        self.pack(fill='both', expand=True)

        config_grids(self, rows=[0, 1, 0, 0, 0], columns=[1, 0])

        self.restart_flag = False

        self.mod_frame = tk.Frame(self, bg='gray20')
        self.mod_frame.grid(row=0, column=0, columns=2, sticky='nsew')

        self.selected_mod_label = tk.Label(
            self.mod_frame, text='Select a mod from the menu above', bg='gray20', fg='gray90', **font
        )
        self.selected_mod_label.grid(row=0, column=0, sticky='nw')

        self.description_label = tk.Label(self.mod_frame, bg='gray20', fg='gray90', **font, justify='left')
        self.description_label.grid(row=0, column=1, sticky='new')

        config_grids(self.mod_frame, columns=[0, 1])

        self.log_var = tk.StringVar()
        self.log_var.set('Browse to the game\'s script directory (PS3_GAME/USRDIR/script),\nand then apply patches')

        self.log_frame = tk.Frame(self, bg='gray30')
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')

        config_grids(self.log_frame)

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
            self, text='Apply patches', command=self.apply_patches,
            **button_style
        )
        self.apply_patches_button.grid(
            row=3, column=0, columnspan=2, **button_grid
        )

        self.remove_patches_button = tk.Button(
            self, text='Remove patches', command=self.remove_patches,
            **button_style
        )
        self.remove_patches_button.grid(
            row=4, column=0, columnspan=2, **button_grid
        )

        self.selected_mod = None

        self.menu_bar = Menubar(self)
        self.master.config(menu=self.menu_bar)

        self.check_dir()

        if not 'window' in DATA:
            self.master.geometry('640x480')
        else:
            self.master.geometry(get_geometry(DATA))
            print(get_geometry(DATA))


    def prompt_mod_name(self):
        self.mod_name_window = tk.Toplevel(self, bg='gray20')
        self.mod_name_window.title('Enter a name for this mod')
        w = 350
        h = 50
        x = int(self.master.winfo_x() + (self.master.winfo_width() / 2) - (w / 2))
        y = int(self.master.winfo_y() + (self.master.winfo_height() / 2) - (h / 2))
        self.mod_name_window.geometry(f'{w}x{h}+{x}+{y}')
        config_grids(self.mod_name_window, columns=[1, 0])
        self.mod_name_entry = tk.Entry(self.mod_name_window, justify='center')
        self.mod_name_entry.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.mod_name_confirm = tk.Button(
            self.mod_name_window, text='Confirm',
            command=lambda: gen_patches(self.mod_name_entry.get(), self.mod_name_window),
            relief='flat', bg='gray80'
        )
        self.mod_name_confirm.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)


    def apply_patches(self):
        if not self.check_dir():
            print('error')
            return None
        log_text = ''
        self.log_var.set(log_text)
        print(self.selected_mod)
        for i, num in enumerate(FILE_NUMS):
            if not str(num) in self.selected_mod['hashes']:
                print('not', num)
                continue
            continue_flag = False
            sdat_name = f'm0{num}.luabnd.dcx.sdat'
            sdat_path = os.path.join(self.dir_var.get(), sdat_name)
            patch_dir = os.path.join(fr'mods/{self.selected_mod["name"]}')
            patch_name = f'm0{num}.patch'
            # patch_path = resource_path(os.path.join(patch_dir, patch_name))
            patch_path = os.path.join(BASE_DIR, patch_dir, patch_name)
            sdat_bak_name = sdat_name + '.bak'
            sdat_bak_path = sdat_path + '.bak'
            if not os.path.isfile(sdat_path):
                log_text += f'{sdat_name} not found, skipping\n'
                print(f'{sdat_name} not found, skipping')
                continue_flag = True
            else:
                hash = get_hash(sdat_path)
                if hash not in DEFAULT_HASHES[i]:
                    print(hash, self.selected_mod['hashes'][str(num)])
                    if hash == self.selected_mod['hashes'][str(num)]:
                        log_text += f'{sdat_name} already patched, skipping file\n'
                        print(f'{sdat_name} already patched, skipping file')
                    else:
                        log_text += f'{sdat_name} is not in it\'s default state, please remove patches first\n'
                        print(f'{sdat_name} is not in it\'s default state, please remove patches first')
                    continue_flag = True
            if not os.path.isfile(patch_path):
                log_text += f'{patch_name} not found, skipping file\n'
                print(f'{patch_name} not found, skipping file')
                continue_flag = True
            if continue_flag:
                print(log_text)
                self.log_var.set(log_text)
                continue
            with open(sdat_path, 'rb') as f:
                unmodded_data = f.read().hex()
            if os.path.isfile(sdat_bak_path):
                log_text += f'{sdat_bak_name} already exists, not overwriting\n'
                print(f'{sdat_bak_name} already exists, not overwriting')
            else:
                copyfile(sdat_path, sdat_bak_path)
            with open(patch_path, 'r') as f:
                patch_data = f.read()
            patches = DMP.patch_fromText(patch_data)
            modded_data, _ = DMP.patch_apply(patches, unmodded_data)
            with open(sdat_path, 'wb') as f:
                f.write(bytes.fromhex(modded_data))
                log_text += f'Applying patch to {sdat_name}\n'
            print(log_text)
        log_text += 'Done'
        print('Done')
        self.log_var.set(log_text)
        self.check_dir()


    def remove_patches(self):
        if not self.check_dir():
            print('Error')
            return None
        log_text = ''
        self.log_var.set(log_text)
        print('Removing patches')
        for num in FILE_NUMS:
            continue_flag = False
            sdat_name = f'm0{num}.luabnd.dcx.sdat'
            sdat_path = os.path.join(self.dir_var.get(), sdat_name)
            bak_name = sdat_name + '.bak'
            bak_path = sdat_path + '.bak'
            if not os.path.isfile(bak_path):
                print(f'Missing backup file {bak_name}')
                log_text += f'Missing backup file {bak_name}\n'
            else:
                move(bak_path, sdat_path)
                print(f'Restored {sdat_name}')
                log_text += f'Restored {sdat_name}\n'
        log_text += 'Done'
        self.log_var.set(log_text)
        self.check_dir()


    def browse_directory(self):
        directory = tk.filedialog.askdirectory(initialdir = BASE_DIR)
        if os.path.isdir(directory):
            self.dir_var.set(directory)


    def quit(self):
        close_window(self.master)
        # self.master.destroy()


    def restart(self):
        self.quit()
        self.restart_flag = True


    def check_dir(self, *args):
        dir = self.dir_var.get()
        successful = False
        if os.path.isdir(dir):
            files = os.listdir(dir)
            if any([f'm0{num}.luabnd.dcx.sdat' in files for num in FILE_NUMS]):
                self.apply_patches_button.config(
                    state='normal', text='Apply patches (backups will be generated)'
                )
                successful = True
            else:
                self.apply_patches_button.config(
                    state='disabled', text='Apply patches (files to patch not found)'
                )
            if not self.selected_mod:
                self.apply_patches_button.config(
                    state='disabled', text='Apply patches (no mod selected)'
                )
                print(self.selected_mod)
            if any(
                [f'm0{num}.luabnd.dcx.sdat.bak' in files for num in FILE_NUMS]
            ):
                self.remove_patches_button.config(
                    state='normal', text='Remove patches (return game to retail state)'
                )
                successful = True
            else:
                self.remove_patches_button.config(
                    state='disabled', text='Remove patches (backup files not found)'
                )
        else:
            self.apply_patches_button.config(
                state='disabled', text='Apply patches (invalid directory)'
            )
            self.remove_patches_button.config(
                state='disabled', text='Remove patches(invalid directory)'
            )
        self.dir_entry.xview('end')
        if successful:
            if dir != DATA['script-dir']:
                DATA['script-dir'] = dir
                SCRIPT_DIR = DATA['script-dir']
                save_data()
        return successful


if __name__ == '__main__':
    root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', lambda: close_window(root))
    # root.iconbitmap(resource_path('icon.ico'))
    root.iconbitmap(os.path.join(BASE_DIR, 'icon.ico'))
    window = MainWindow(root)
    root.mainloop()

    if window.restart_flag:
        os.system(__file__)
