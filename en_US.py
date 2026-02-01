import sys
import winreg
import os
import shutil
import msvcrt
import subprocess
from fontTools.ttLib import TTFont
import tkinter as tk
from tkinter import filedialog
import zipfile

class Logger(object):
	def __init__(self):
		self.terminal = sys.stdout
		self.log = []

	def write(self, message):
		self.terminal.write(message)
		self.log.append(message)

	def flush(self):
		self.terminal.flush()

	def get_logs(self):
		# Strip ANSI escape sequences
		import re
		ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
		return ansi_escape.sub('', "".join(self.log))

	def clear(self):
		"""Clear the log buffer"""
		self.log = []

# Initialize Logger
sys_logger = Logger()
sys.stdout = sys_logger

def copy_to_clipboard(text):
	"""Copies text to the clipboard"""
	try:
		# Use Windows built-in clip command
		# Note: clip command may have encoding issues with pipe input, forcing GBK encoding here for Windows compatibility
		process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, text=False)
		process.communicate(input=text.encode('gbk', errors='ignore'))
	except Exception:
		pass

def normalize_path(path):
	return path.replace('/', '\\') if path else None

def wait_for_enter(prompt):
	print(prompt, end='', flush=True)
	while True:
		if msvcrt.getch() in [b'\r', b'\n']:
			sys.stdout.write('\n')
			break
	print()

def select_file_dialog(title, filetypes):
	root = tk.Tk()
	root.withdraw()
	root.attributes('-topmost', True)
	res = filedialog.askopenfilename(title=title, filetypes=filetypes)
	root.destroy()
	return normalize_path(res)

def select_dir_dialog(title):
	root = tk.Tk()
	root.withdraw()
	root.attributes('-topmost', True)
	res = filedialog.askdirectory(title=title)
	root.destroy()
	return normalize_path(res)

def is_valid_install_location(path):
	return bool(path) and os.path.exists(path) and path.endswith('Counter-Strike Global Offensive')

def get_fonts_paths(install_location):
	csgo_fonts = os.path.join(install_location, 'game', 'csgo', 'panorama', 'fonts')
	core_fonts = os.path.join(install_location, 'game', 'core', 'panorama', 'fonts', 'conf.d')
	ui_font = os.path.join(csgo_fonts, 'stratum2.uifont')
	return csgo_fonts, core_fonts, ui_font

def ensure_directory(path, missing_msg, created_msg):
	if not os.path.exists(path):
		print(missing_msg)
		os.makedirs(path, exist_ok=True)
		print(created_msg)

def remove_existing_fonts(csgo_fonts, ui_font, ui_msg, ui_err_msg, ttf_msg_format, ttf_err_msg_format):
	if os.path.exists(ui_font):
		try:
			os.remove(ui_font)
			print(ui_msg)
		except Exception as e:
			print_error(ui_err_msg, e)
	for file in os.listdir(csgo_fonts):
		if file.endswith('.ttf'):
			try:
				os.remove(os.path.join(csgo_fonts, file))
				print(ttf_msg_format.format(file=file))
			except Exception as e:
				print_error(ttf_err_msg_format.format(file=file), e)

def write_fonts_conf(csgo_fonts, safe_font_name, ui_scale, success_msg, error_msg):
	try:
		with open(os.path.join(csgo_fonts, 'fonts.conf'), 'w', encoding='utf-8') as f:
			f.write(f"""<?xml version='1.0'?>
<!DOCTYPE fontconfig SYSTEM 'fonts.dtd'>
<fontconfig>

	<dir prefix="default">../../csgo/panorama/fonts</dir>
	<dir>WINDOWSFONTDIR</dir>
	<dir>~/.fonts</dir>
	<dir>/usr/share/fonts</dir>
	<dir>/usr/local/share/fonts</dir>
	<dir prefix="xdg">fonts</dir>

	<fontpattern>Arial</fontpattern>
	<fontpattern>.uifont</fontpattern>
	<fontpattern>notosans</fontpattern>
	<fontpattern>notoserif</fontpattern>
	<fontpattern>notomono-regular</fontpattern>
	<fontpattern>{safe_font_name}</fontpattern>
	<fontpattern>.ttf</fontpattern>
	<fontpattern>FONTFILENAME</fontpattern>
	
	<cachedir>WINDOWSTEMPDIR_FONTCONFIG_CACHE</cachedir>
	<cachedir>~/.fontconfig</cachedir>

	<!-- Vietnamese language support -->
	<match>
		<test name="lang">
			<string>vi-vn</string>
		</test>
		<test name="family" compare="contains">
			<string>Stratum2</string>
		</test>
		<test qual="all" name="family" compare="not_contains">
			<string>TF</string>
		</test>
		<test qual="all" name="family" compare="not_contains">
			<string>Mono</string>
		</test>
		<test qual="all" name="family" compare="not_contains">
			<string>ForceStratum2</string>
		</test>
		<edit name="weight" mode="assign">
			<if>
				<contains>
					<name>family</name>
					<string>Stratum2 Black</string>
				</contains>
				<int>210</int>
				<name>weight</name>
			</if>
		</edit>
		<edit name="slant" mode="assign">
			<if>
				<contains>
					<name>family</name>
					<string>Italic</string>
				</contains>
				<int>100</int>
				<name>slant</name>
			</if>
		</edit>
		<edit name="pixelsize" mode="assign">
			<if>
				<or>
					<contains>
						<name>family</name>
						<string>Condensed</string>
					</contains>
					<less_eq>
						<name>width</name>
						<int>75</int>
					</less_eq>
				</or>
				<times>
					<name>pixelsize</name>
					<double>0.7</double>
				</times>
				<times>
					<name>pixelsize</name>
					<double>0.9</double>
				</times>
			</if>
		</edit>
		<edit name="family" mode="assign" binding="same">
			<string>notosans</string>
		</edit>
	</match>

	<selectfont> 
		<rejectfont> 
			<pattern> 
				<patelt name="fontformat" > 
					<string>Type 1</string> 
				</patelt> 
			</pattern> 
		</rejectfont> 
	</selectfont> 

	<match target="font" >
		<edit name="embeddedbitmap" mode="assign">
			<bool>false</bool>
		</edit>
	</match>

	<match target="pattern" >
		<edit name="prefer_outline" mode="assign">
			<bool>true</bool>
		</edit>
	</match>

	<match target="pattern" >
		<edit name="do_substitutions" mode="assign">
			<bool>true</bool>
		</edit>
	</match>

	<match target="font">
		<edit name="force_autohint" mode="assign">
			<bool>false</bool>
		</edit>
	</match>

	<include>../../../core/panorama/fonts/conf.d</include>

	<!-- Adjust HUD font size (Money, Health, Ammo) -->
	<match target="font">
		<test name="family" compare="contains">
			<string>Stratum2</string>
		</test>
		<test name="family" compare="contains">
			<string>{safe_font_name}</string>
		</test>
		<edit name="pixelsize" mode="assign">
			<times>
				<name>pixelsize</name>
				<double>{ui_scale}</double>
			</times>
		</edit>
	</match>
	
	<!-- Custom fonts -->
	<match>
		<test name="family">
			<string>Stratum2</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>
	
	<match>
		<test name="family">
			<string>Stratum2 Bold</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>
	
	<match>
		<test name="family">
			<string>Arial</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>
	
	<match>
		<test name="family">
			<string>Times New Roman</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>
	
	<match>
		<test name="family">
			<string>Courier New</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>

	<match>
		<test name="family">
			<string>notosans</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>
	
	<match>
		<test name="family">
			<string>notoserif</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>
	
	<match>
		<test name="family">
			<string>notomono-regular</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>

	<match>
		<test name="family">
			<string>noto</string>
		</test>
		<edit name="family" mode="append" binding="strong">
			<string>{safe_font_name}</string>
		</edit>
	</match>

</fontconfig>""")
		print(success_msg)
	except Exception as e:
		print_error(error_msg, e)

def write_repl_conf(core_fonts, safe_font_name, ui_scale, success_msg, error_msg):
	try:
		with open(os.path.join(core_fonts, '42-repl-global.conf'), 'w', encoding='utf-8') as f:
			f.write(f"""<?xml version='1.0'?>
<!DOCTYPE fontconfig SYSTEM 'fonts.dtd'>
<fontconfig>

	<match target="font">
		<test name="family" compare="contains"><string>Stratum2</string></test>
		<edit name="pixelsize" mode="assign">
			<times><name>pixelsize</name><double>{ui_scale}</double></times>
		</edit>
	</match>
	<match target="font">
		<test name="family" compare="contains"><string>{safe_font_name}</string></test>
		<edit name="pixelsize" mode="assign">
			<times><name>pixelsize</name><double>{ui_scale}</double></times>
		</edit>
	</match>
""")
		fonts_to_replace = ['Stratum2', 'Stratum2 Bold', 'Arial', 'Times New Roman', 'Courier New', 'notosans', 'notoserif', 'notomono-regular', 'noto']
		for font_to_repl in fonts_to_replace:
			f.write(f"""
	<match target="font">
		<test name="family"><string>{font_to_repl}</string></test>
		<edit name="family" mode="assign"><string>{safe_font_name}</string></edit>
	</match>
	<match target="pattern">
		<test name="family"><string>{font_to_repl}</string></test>
		<edit name="family" mode="prepend" binding="strong"><string>{safe_font_name}</string></edit>
	</match>""")
		f.write("\n</fontconfig>")
		print(success_msg)
	except Exception as e:
		print_error(error_msg, e)

def read_menu_key(valid_keys, enter_label):
	try:
		while True:
			char = msvcrt.getch()
			if char in valid_keys:
				if char in [b'\r', b'\n']:
					sys.stdout.write(f'\033[92m[{enter_label}]\033[0m\n\n')
					return ""
				decoded_char = char.decode('utf-8')
				sys.stdout.write(f'\033[92m{decoded_char}\033[0m\n\n')
				return decoded_char.strip()
	except:
		return ""

def get_auto_install_location():
	try:
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Steam App 730')
		return winreg.QueryValueEx(key, 'InstallLocation')[0]
	except FileNotFoundError:
		return None

def finish_execution(exit_code=0):
	"""Displays final output and performs actions based on user choice"""
	try:
		print('\nTask completed, Press [\033[92mEnter\033[0m] to copy execution logs to clipboard, or close directly', end='', flush=True)
		while True:
			char = msvcrt.getch()
			if char in [b'\r', b'\n']:
				sys.stdout.write('\n')
				copy_to_clipboard(sys_logger.get_logs())
				print('Logs have been successfully copied to the clipboard')
				break
	except (EOFError, KeyboardInterrupt):
		pass
	sys.exit(exit_code)

def print_error(message, exception=None):
	"""Print brief error message"""
	print(f'Exception: {message}')
	if exception:
		print(f'Diagnostic Details: {str(exception)}')

def verify_files(csgo_fonts, font_name):
	"""Verify if files are correctly installed"""
	font_file = os.path.join(csgo_fonts, f"{font_name}.ttf")
	conf_file = os.path.join(csgo_fonts, 'fonts.conf')
	
	print('Performing consistency check on installation results')
	if not os.path.exists(font_file):
		print(f'Validation failed: Could not locate target font file {font_file}')
		return False
	if not os.path.exists(conf_file):
		print(f'Validation failed: Could not locate required configuration file {conf_file}')
		return False
	if os.path.getsize(font_file) == 0:
		print(f'Validation failed: Target font file size is abnormal (0 bytes)')
		return False
	
	print('Validation complete, all necessary files are ready')
	return True

def create_backup(install_location):
	"""Create a backup zip file"""
	backup_path = os.path.join(install_location, 'backup_original_fonts.zip')
	
	if os.path.exists(backup_path):
		return # Backup already exists

	print('Backing up')
	csgo_fonts, core_fonts, _ = get_fonts_paths(install_location)
	
	try:
		with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
			# Backup csgo_fonts
			if os.path.exists(csgo_fonts):
				for root, dirs, files in os.walk(csgo_fonts):
					for file in files:
						file_path = os.path.join(root, file)
						arcname = os.path.join('csgo_fonts', os.path.relpath(file_path, csgo_fonts))
						zf.write(file_path, arcname)
			
			# Backup core_fonts
			if os.path.exists(core_fonts):
				for root, dirs, files in os.walk(core_fonts):
					for file in files:
						file_path = os.path.join(root, file)
						arcname = os.path.join('core_fonts', os.path.relpath(file_path, core_fonts))
						zf.write(file_path, arcname)
			
		print(f'Backup success, \033[90m{backup_path}\033[0m')
	except Exception as e:
		print_error("Backup failed", e)

def restore_backup(install_location, backup_path_override=None):
	"""Restore from backup"""
	backup_path = backup_path_override if backup_path_override else os.path.join(install_location, 'backup_original_fonts.zip')
	
	if not os.path.exists(backup_path):
		print(f'No restoration file found at: {backup_path}')
		return False

	print(f'Restoring initial game fonts from {os.path.basename(backup_path)}')
	csgo_fonts, core_fonts, _ = get_fonts_paths(install_location)

	try:
		# Cleanup before restoring
		if os.path.exists(csgo_fonts):
			for item in os.listdir(csgo_fonts):
				item_path = os.path.join(csgo_fonts, item)
				if os.path.isdir(item_path):
					shutil.rmtree(item_path)
				else:
					os.remove(item_path)
		
		with zipfile.ZipFile(backup_path, 'r') as zf:
			for item in zf.infolist():
				if item.filename.startswith('csgo_fonts/'):
					rel_path = item.filename[len('csgo_fonts/'):]
					if not rel_path: continue
					target_path = os.path.join(csgo_fonts, rel_path)
					os.makedirs(os.path.dirname(target_path), exist_ok=True)
					with zf.open(item) as source, open(target_path, 'wb') as target:
						shutil.copyfileobj(source, target)
				elif item.filename.startswith('core_fonts/'):
					rel_path = item.filename[len('core_fonts/'):]
					if not rel_path: continue
					target_path = os.path.join(core_fonts, rel_path)
					os.makedirs(os.path.dirname(target_path), exist_ok=True)
					with zf.open(item) as source, open(target_path, 'wb') as target:
						shutil.copyfileobj(source, target)
		
		# Cleanup custom config if not in backup
		repl_conf = os.path.join(core_fonts, '42-repl-global.conf')
		with zipfile.ZipFile(backup_path, 'r') as zf:
			if 'core_fonts/42-repl-global.conf' not in zf.namelist():
				if os.path.exists(repl_conf):
					os.remove(repl_conf)
					print('Cleaned custom config')

		print('Restore complete')
		return True
	except Exception as e:
		print_error("Restore failed", e)
		return False

# Enable ANSI escape sequences
os.system('')

def is_game_running():
	"""Check if CS2 process is running"""
	try:
		# Check process using tasklist
		output = subprocess.check_output('tasklist /FI "IMAGENAME eq cs2.exe" /NH', shell=True, stderr=subprocess.DEVNULL).decode('gbk', errors='ignore')
		return 'cs2.exe' in output.lower()
	except:
		return False

def get_font_name(file_path):
	"""Get font name from font file"""
	try:
		font = TTFont(file_path)
		font_name = next((record.toUnicode().strip() 
			for record in font['name'].names 
			if record.nameID == 1 and record.platformID == 3), None)
		return font_name
	except Exception:
		return None

# Check input arguments
input_file = sys.argv[1] if len(sys.argv) == 2 else None
font_name = None

if input_file and os.path.isfile(input_file):
	# Handle auto-restore logic
	if os.path.basename(input_file).lower() == 'backup_original_fonts.zip':
		print('\nBackup zip detected, preparing for auto-restore')
		# Try to get game installation path
		install_location = get_auto_install_location()
		
		if not install_location:
			print('\nAuto-detection of game path failed, Please specify the path manually')
			install_location = select_dir_dialog("Select Counter-Strike Global Offensive folder for restore")
		
		if is_valid_install_location(install_location):
			if restore_backup(install_location, input_file):
				finish_execution(0)
			else:
				input('\nRestoration failed, Press Enter to exit')
				finish_execution(1)
		else:
			input('\nInvalid path or no path selected, Press Enter to exit')
			finish_execution(1)

	# Handle font file
	if input_file.endswith(('.ttf', '.otf')):
		font_name = get_font_name(input_file)
		if not font_name:
			print_error(f'"{os.path.basename(input_file)}" is an unsupported font')
			input('\nPlease send the error details above to the developer, Press Enter to exit')
			finish_execution(1)

# Try to get game installation path from registry
auto_install_location = get_auto_install_location()

# Initialize installation location as the auto-detected one
install_location = auto_install_location

# Initialize scaling rate
ui_scale = 1.0

# Game installation path input and verification
while True:
	# Clear screen for a clean menu
	os.system('cls' if os.name == 'nt' else 'clear')
	sys_logger.clear()  # Clear log before redraw to ensure clipboard only has final state
	
	print("CS2 Font Changer v3.0 | Author: Cairl\n")

	if is_game_running():
		print('\033[93mNote: Counter-Strike 2 is currently running, which may affect the font replacement, It is recommended to close the game before proceeding\033[0m')
	
	# 1. Game Path and Backup Detection
	has_backup = False
	if install_location:
		backup_path = os.path.join(install_location, 'backup_original_fonts.zip')
		has_backup = os.path.exists(backup_path)

	# 2. Menu Display Logic
	can_start = bool(input_file) and is_valid_install_location(install_location)
	print(f"\033[96m•\033[0m Press [\033[92m1\033[0m] to {'re-import font' if input_file else 'select font to import'}, current: \033[90m{font_name or 'Not Selected'}\033[0m")
	print(f"\033[96m•\033[0m Press [\033[92m2\033[0m] to select game path, current: \033[90m{install_location or 'Not Identified'}\033[0m")
	print(f"\033[96m•\033[0m Press [\033[92m3\033[0m] to adjust UI scale, current: \033[90m{ui_scale}\033[0m")
	if has_backup:
		print(f"\033[96m•\033[0m Press [\033[92m0\033[0m] to restore default fonts, Note: A restoration file is automatically created in the game root during the first run, and restoration requires this file to exist")
	if can_start:
		print(f"\n\033[96m•\033[0m Press [\033[92mEnter\033[0m] to start font replacement")
	
	sys.stdout.write('\n> ')
	sys.stdout.flush()
	
	valid_keys = [b'1', b'2', b'3']
	if has_backup:
		valid_keys.append(b'0')
	if can_start:
		valid_keys.extend([b'\r', b'\n'])

	user_input = read_menu_key(valid_keys, "Enter")
	
	sys.stdout.flush()

	if user_input == '1':
		selected_file = select_file_dialog(
			"Select Font or Restoration File",
			[("Supported Files", "*.ttf;*.otf;*.zip"), ("Font Files", "*.ttf;*.otf"), ("Restoration File", "backup_original_fonts.zip")]
		)
		if selected_file:
			input_file = selected_file
			if input_file.lower().endswith('.zip'):
				if os.path.basename(input_file) == 'backup_original_fonts.zip':
					font_name = "Restoration File (ZIP)"
				else:
					print_error(f'Selected ZIP file name is incorrect, Should be "backup_original_fonts.zip"')
					input_file = None
					wait_for_enter('Press Enter to return to main menu')
			else:
				font_name = get_font_name(input_file)
				if not font_name:
					print_error(f'Selected file "{os.path.basename(input_file)}" is not a valid font format')
					input_file = None
					wait_for_enter('Press Enter to return to main menu')
		continue

	elif user_input == '2':
		selected_path = select_dir_dialog("Select Counter-Strike Global Offensive folder")
		if selected_path:
			install_location = selected_path
		else:
			continue

	elif user_input == '3':
		while True:
			try:
				val = input('\033[93m•\033[0m Enter UI scale (suggested 0.9 to 1.1): ')
				if not val: break
				ui_scale = float(val)
				print()
				break
			except ValueError:
				print('Please enter a valid number')
		continue

	elif user_input == '0' and has_backup:
		# Restore logic remains the same, but messages are updated
		if not install_location:
			print('Please specify the game installation path before running restoration')
			selected_path = select_dir_dialog("Select Counter-Strike Global Offensive folder for restoration")
			if selected_path:
				install_location = selected_path
			else:
				input('Operation cancelled, Press Enter to return')
				continue
		
		if is_valid_install_location(install_location):
			if restore_backup(install_location):
				finish_execution(0)
			else:
				input('Restoration failed, Press Enter to return to main menu and try manually')
				continue
		else:
			input('Invalid path specified, Please ensure you select the correct game root directory')
			continue

	elif user_input == "":
		# Empty input on Enter starts operation
		if not input_file:
			input('No font source file loaded, Cannot perform configuration, Press 1 to import font first')
			continue
		if not is_valid_install_location(install_location):
			input('Game path configuration incorrect or not yet set, Please confirm path info first')
			continue
		
		# Validation passed, create backup and break loop to start
		create_backup(install_location)
		break

	else:
		input('Unrecognized command, Press Enter to refresh menu')
		continue

# Construct target paths
csgo_fonts, core_fonts, ui_font = get_fonts_paths(install_location)

ensure_directory(csgo_fonts, f'Font directory missing: {csgo_fonts}', 'Created font directory automatically')
ensure_directory(core_fonts, f'Core configuration directory missing: {core_fonts}', 'Created core configuration directory automatically')

remove_existing_fonts(
	csgo_fonts,
	ui_font,
	'Cleaning up legacy UI font index files',
	'Failed to clean up legacy UI font index',
	'Removing conflicting legacy font: {file}',
	'Failed to remove legacy font: {file}'
)

# Copy new font file
try:
	safe_font_name = font_name  # Font name for the configuration file
	shutil.copy(input_file, os.path.join(csgo_fonts, f"{font_name}.ttf"))
	print(f'Deployed new font file to target: {font_name}.ttf')
except Exception as e:
	print_error("Failed to deploy font file", e)
	finish_execution(1)

write_fonts_conf(csgo_fonts, safe_font_name, ui_scale, '\nGenerating local font configuration: fonts.conf', 'Failed to generate fonts.conf')
write_repl_conf(core_fonts, safe_font_name, ui_scale, 'Generating global font mapping: 42-repl-global.conf', 'Failed to generate 42-repl-global.conf')

if verify_files(csgo_fonts, font_name):
	print('\nAll configuration tasks have been successfully executed, Please launch Counter-Strike 2 to see the new font')
	finish_execution(0)
else:
	print('\nSome operations might have failed during execution, Please review the error messages above')
	finish_execution(1)
