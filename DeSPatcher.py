import hashlib
import os
import sys
import tkinter.filedialog
import tkinter as tk

from diff_match_patch import diff_match_patch
from shutil import copyfile, move


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DMP = diff_match_patch()
FILE_NUMS = [2, 3, 4, 5, 6]
HASHES = [
    [
        'cae0b75b6f317adceb84713a0b9ec665ac197c6967fea32c3ca5485e8f9c3ae7',
        '4b57a77b897c1d7c7d24d283361d436674d79ec50ec7c62791661b170ac96dc2'
    ],
    [
        '9a262026c4c62c349bcb34e828866467740b65e71f74d5d181c7c62bd5363f0e',
        '0ccfcdb7384641b8d06d7184e1cbac6852a741088643ac93888149b27e03dd3a'
    ],
    [
        '8a8d37ae77c70ccdf58744869d941957f4ea996e738f171685caa221adee5abf',
        '849bee3f25b12cf2794803b0aba2c530e244aa7ee909b441a0ce9245615b7269'
    ],
    [
        '7878d9aead49e683a57247d133a63c6b5ec001547c9050cc8fbdcf6b24d049be',
        '07a054fdf8c34a229d89a289556b941bfb61e2c25c0161f9c0a842f5c33fdc8c'
    ],
    [
        '3238a4f554c48137e3e8953dd685ac7fc93fed6e86e79278b246c61cf66e32ca',
        '3401b36714a93bb2852f624cfdd34587a5f7ff72a098d413e79217f5aa2a938d'
    ]
]


def get_hash(filepath):
    sha = hashlib.sha256()

    with open(filepath, 'rb') as infile:
        while True:
            data = infile.read(sha.block_size)
            if not data:
                break
            sha.update(data)
    return sha.hexdigest()


def gen_patch():
    while True:
        modded = input('modded path:> ')
        if not os.path.isfile(modded):
            print('incorrect path')
            continue
        unmodded = input('unmodded path:> ')
        if not os.path.isfile(unmodded):
            print('incorrect path')
            continue
        with open(modded, 'rb') as infile:
            modded_data = infile.read().hex()
        with open(unmodded, 'rb') as infile:
            unmodded_data = infile.read().hex()
        patches = DMP.patch_make(unmodded_data, modded_data)
        diff = DMP.patch_toText(patches)
        patch_name = os.path.split(modded)[1] + '.patch'
        with open(os.path.join(BASE_DIR, patch_name), 'w+') as outfile:
            outfile.write(diff)


def config_grids(widget, rows=[1], columns=[1]):
    [widget.rowconfigure(i, weight=w) for i, w in enumerate(rows)]
    [widget.columnconfigure(i, weight=w) for i, w in enumerate(columns)]


def resource_path(filename):
    try:
        base_dir = sys._MEIPASS
    except AttributeError:
        base_dir = BASE_DIR
    return os.path.join(base_dir, filename)


def get_script_dir():
    while True:
        script_dir = input('Path to Demon\'s Souls script \
    folder (/PS3_GAME/USRDIR/script):> ')
        if not os.path.isdir(script_dir):
            print('Invalid directory')
        else:
            return script_dir


# -------------------------------------------------------------
# -------------------- M A I N W I N D O W --------------------
# -------------------------------------------------------------

class MainWindow(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master

        font = {'font': 'Consolas 11'}

        self.config(bg='gray20')

        self.master.title('Demon\'s Souls Archstone Warping Patcher')

        self.pack(fill='both', expand=True)

        config_grids(self, rows=[1, 0, 0, 0], columns=[1, 0])

        self.master.geometry('420x300')

        self.log_var = tk.StringVar()
        self.log_var.set('Select script dir, and then apply patches')

        self.log_frame = tk.Frame(self, bg='gray30')
        self.log_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        config_grids(self.log_frame)

        self.log_label = tk.Label(
            self.log_frame, bg='gray30', fg='gray90', textvariable=self.log_var,
            padx=10, pady=10, justify='left', **font
        )
        self.log_label.grid(row=0, column=0, sticky='nsew')

        self.dir_var = tk.StringVar()
        self.dir_var.set(BASE_DIR)
        self.dir_var.trace('w', self.check_dir)

        self.dir_entry = tk.Entry(self, textvariable=self.dir_var)
        self.dir_entry.grid(
            row=1, column=0, sticky='nsew', padx=(10, 10), pady=(10, 10)
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
        self.dir_browse_button.grid(row=1, column=1, **button_grid)

        self.apply_patches_button = tk.Button(
            self, text='Apply patches', command=self.apply_patches,
            **button_style
        )
        self.apply_patches_button.grid(
            row=2, column=0, columnspan=2, **button_grid
        )

        self.remove_patches_button = tk.Button(
            self, text='Remove patches', command=self.remove_patches,
            **button_style
        )
        self.remove_patches_button.grid(
            row=3, column=0, columnspan=2, **button_grid
        )

        self.check_dir()


    def apply_patches(self):
        if not self.check_dir():
            print('error')
            return None
        log_text = ''
        self.log_var.set(log_text)
        for i, num in enumerate(FILE_NUMS):
            continue_flag = False
            sdat_name = f'm0{num}.luabnd.dcx.sdat'
            sdat_path = os.path.join(self.dir_var.get(), sdat_name)
            patch_name = f'm0{num}.patch'
            patch_path = resource_path(patch_name)
            sdat_bak_name = sdat_name + '.bak'
            sdat_bak_path = sdat_path + '.bak'
            if not os.path.isfile(sdat_path):
                log_text += f'{sdat_name} not found, skipping\n'
                print(f'{sdat_name} not found, skipping')
                continue_flag = True
            else:
                hash = get_hash(sdat_path)
                if hash != HASHES[i][0]:
                    if hash == HASHES[i][1]:
                        log_text += f'{sdat_name} already patched, skipping\n'
                        print(f'{sdat_name} already patched, skipping')
                    else:
                        log_text += f'{sdat_name} does not match any known hashes, skipping\n'
                        print(f'{sdat_name} does not match any known hashes, skipping')
                    continue_flag = True
            if not os.path.isfile(patch_path):
                log_text += f'{patch_name} not found, skipping\n'
                print(f'{patch_name} not found, skipping')
                continue_flag = True
            if continue_flag:
                print(log_text)
                self.log_var.set(log_text)
                continue
            with open(sdat_path, 'rb') as infile:
                unmodded_data = infile.read().hex()
            if os.path.isfile(sdat_bak_path):
                log_text += f'{sdat_bak_name} already exists, not overwriting\n'
                print(f'{sdat_bak_name} already exists, not overwriting')
            else:
                copyfile(sdat_path, sdat_bak_path)
            with open(patch_path, 'r') as infile:
                patch_data = infile.read()
            patches = DMP.patch_fromText(patch_data)
            modded_data, _ = DMP.patch_apply(patches, unmodded_data)
            with open(sdat_path, 'wb') as outfile:
                outfile.write(bytes.fromhex(modded_data))
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
            bak_path = sdat_path + '.bak'
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
        self.cont = False
        close_window(self.master)


    def restart(self):
        self.quit()
        self.restart_flag = True


    def check_dir(self, *args):
        dir = self.dir_var.get()
        success = False
        if os.path.isdir(dir):
            files = os.listdir(dir)
            if all([f'm0{num}.luabnd.dcx.sdat' in files for num in FILE_NUMS]):
                self.apply_patches_button.config(
                    state='normal', text='Apply patches'
                )
                success = True
            else:
                self.apply_patches_button.config(
                    state='disabled', text='Apply patches (Missing .sdat files)'
                )
            if all(
                [f'm0{num}.luabnd.dcx.sdat.bak' in files for num in FILE_NUMS]
            ):
                self.remove_patches_button.config(
                    state='normal', text='Remove patches'
                )
                success = True
            else:
                self.remove_patches_button.config(
                    state='disabled', text='Remove patches (Missing .bak files)'
                )
        else:
            self.apply_patches_button.config(
                state='disabled', text='Apply patches (invalid directory)'
            )
            self.remove_patches_button.config(
                state='disabled', text='Remove patches(invalid directory)'
            )
        self.dir_entry.xview('end')
        return success


if __name__ == '__main__':
    # script_dir = get_script_dir()
    # apply_patches(script_dir)

    root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', root.destroy)
    root.iconbitmap(resource_path('icon.ico'))
    window = MainWindow(root)
    root.mainloop()
