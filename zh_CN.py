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
		# 过滤掉 ANSI 转义序列
		import re
		ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
		return ansi_escape.sub('', "".join(self.log))

	def clear(self):
		"""清空日志缓冲区"""
		self.log = []

# 初始化日志记录器
sys_logger = Logger()
sys.stdout = sys_logger

def copy_to_clipboard(text):
	"""将文本复制到剪贴板"""
	try:
		# 使用 Windows 自带的 clip 命令
		# 注意：clip 命令在接收管道输入时可能存在编码问题，这里强制使用 utf-8 编码
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

	<!-- 调整 HUD 字体大小 (金钱、血量、弹药) -->
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
	"""显示最终回显并根据用户选择执行操作"""
	try:
		print('\n运行任务已结束，按 [\033[92m回车键\033[0m] 复制执行日志至剪贴板，或直接关闭', end='', flush=True)
		while True:
			char = msvcrt.getch()
			if char in [b'\r', b'\n']:
				sys.stdout.write('\n')
				copy_to_clipboard(sys_logger.get_logs())
				print('日志已成功复制到剪贴板')
				break
	except (EOFError, KeyboardInterrupt):
		pass
	sys.exit(exit_code)

def print_error(message, exception=None):
	"""打印简要的错误信息"""
	print(f'异常：{message}')
	if exception:
		print(f'诊断详情: {str(exception)}')

def verify_files(csgo_fonts, font_name):
	"""验证文件是否正确安装"""
	font_file = os.path.join(csgo_fonts, f"{font_name}.ttf")
	conf_file = os.path.join(csgo_fonts, 'fonts.conf')
	
	print('正在对安装结果进行一致性校验')
	if not os.path.exists(font_file):
		print(f'校验失败：未能定位到目标字体文件 {font_file}')
		return False
	if not os.path.exists(conf_file):
		print(f'校验失败：未能定位到必要的配置文件 {conf_file}')
		return False
	if os.path.getsize(font_file) == 0:
		print(f'校验失败：目标字体文件大小异常（0 字节）')
		return False
	
	print('校验完成，所有必要文件均已就绪')
	return True

def create_backup(install_location):
	"""创建备份压缩包"""
	backup_path = os.path.join(install_location, 'backup_original_fonts.zip')
	
	if os.path.exists(backup_path):
		return # 备份已存在，说明已经进行过初次修改备份

	print('正在备份')
	csgo_fonts, core_fonts, _ = get_fonts_paths(install_location)
	
	try:
		with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
			# 备份 csgo_fonts 目录
			if os.path.exists(csgo_fonts):
				for root, dirs, files in os.walk(csgo_fonts):
					for file in files:
						file_path = os.path.join(root, file)
						arcname = os.path.join('csgo_fonts', os.path.relpath(file_path, csgo_fonts))
						zf.write(file_path, arcname)
			
			# 备份 core_fonts 目录
			if os.path.exists(core_fonts):
				for root, dirs, files in os.walk(core_fonts):
					for file in files:
						file_path = os.path.join(root, file)
						arcname = os.path.join('core_fonts', os.path.relpath(file_path, core_fonts))
						zf.write(file_path, arcname)
			
		print(f'备份成功，\033[90m{backup_path}\033[0m')
	except Exception as e:
		print_error("备份失败", e)

def restore_backup(install_location, backup_path_override=None):
	"""从备份还原"""
	backup_path = backup_path_override if backup_path_override else os.path.join(install_location, 'backup_original_fonts.zip')
	
	if not os.path.exists(backup_path):
		print(f'未发现可用的备份文件：{backup_path}')
		return False

	print(f'正在从复原文件 {os.path.basename(backup_path)} 还原游戏初始字体')
	csgo_fonts, core_fonts, _ = get_fonts_paths(install_location)

	try:
		# 还原前先清理
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
		
		# 特殊处理：如果 42-repl-global.conf 是我们创建的且备份里没有，应该删除它
		repl_conf = os.path.join(core_fonts, '42-repl-global.conf')
		with zipfile.ZipFile(backup_path, 'r') as zf:
			if 'core_fonts/42-repl-global.conf' not in zf.namelist():
				if os.path.exists(repl_conf):
					os.remove(repl_conf)
					print('已清理自定义配置')

		print('还原完成')
		return True
	except Exception as e:
		print_error("还原失败", e)
		return False

# 启用 ANSI 转义序列支持
os.system('')

def is_game_running():
	"""检查 CS2 进程是否正在运行"""
	try:
		# 使用 tasklist 检查进程
		output = subprocess.check_output('tasklist /FI "IMAGENAME eq cs2.exe" /NH', shell=True, stderr=subprocess.DEVNULL).decode('gbk', errors='ignore')
		return 'cs2.exe' in output.lower()
	except:
		return False

def get_font_name(file_path):
	"""从字体文件中获取字体名称"""
	try:
		font = TTFont(file_path)
		font_name = next((record.toUnicode().strip() 
			for record in font['name'].names 
			if record.nameID == 1 and record.platformID == 3), None)
		return font_name
	except Exception:
		return None

# 检查输入的参数
input_file = sys.argv[1] if len(sys.argv) == 2 else None
font_name = None

if input_file and os.path.isfile(input_file):
	# 处理自动还原逻辑
	if os.path.basename(input_file).lower() == 'backup_original_fonts.zip':
		print('\n检测到备份压缩包，准备执行自动还原')
		# 尝试获取游戏安装路径
		install_location = get_auto_install_location()
		
		if not install_location:
			print('\n未能自动检测到游戏安装路径，请手动进行选择')
			install_location = select_dir_dialog("选择 Counter-Strike Global Offensive 文件夹以进行还原")
		
		if is_valid_install_location(install_location):
			if restore_backup(install_location, input_file):
				finish_execution(0)
			else:
				input('\n还原程序执行失败，请按回车键退出')
				finish_execution(1)
		else:
			input('\n指定的路径无效或未选择任何目录，请按回车键退出')
			finish_execution(1)

	# 处理字体文件
	if input_file.endswith(('.ttf', '.otf')):
		font_name = get_font_name(input_file)
		if not font_name:
			print_error(f'"{os.path.basename(input_file)}" 是不受支持的字体集')
			input('\n请将以上错误详情发送给开发者排查，按回车键退出程序')
			finish_execution(1)

# 尝试获取注册表中的游戏安装路径
auto_install_location = get_auto_install_location()

# 初始化安装位置为自动识别的位置
install_location = auto_install_location

# 初始化缩放倍率
ui_scale = 1.0

# 游戏安装路径输入与验证
while True:
	# 清屏以保持菜单整洁
	os.system('cls' if os.name == 'nt' else 'clear')
	sys_logger.clear()  # 每次重绘菜单前清空日志，确保复制的日志只有最后一次状态
	
	print("CS2 字体更改器 v3.0 | 作者: Cairl\n")

	if is_game_running():
		print('\033[93m注意：检测到 Counter-Strike 2 正在运行，可能会影响字体替换效果，建议先关闭游戏再进行操作\033[0m')

	# 1. 游戏路径与备份检测
	has_backup = False
	if install_location:
		backup_path = os.path.join(install_location, 'backup_original_fonts.zip')
		has_backup = os.path.exists(backup_path)

	# 2. 菜单显示逻辑
	can_start = bool(input_file) and is_valid_install_location(install_location)
	print(f"\033[96m•\033[0m 按 [\033[92m1\033[0m] {'重新导入字体' if input_file else '选择导入字体'}，当前：\033[90m{font_name or '未选择'}\033[0m")
	print(f"\033[96m•\033[0m 按 [\033[92m2\033[0m] 选择游戏路径，当前：\033[90m{install_location or '未识别'}\033[0m")
	print(f"\033[96m•\033[0m 按 [\033[92m3\033[0m] 调整 UI 缩放，当前：\033[90m{ui_scale}\033[0m")
	if has_backup:
		print(f"\033[96m•\033[0m 按 [\033[92m0\033[0m] 恢复默认字体，注意：程序首次运行时会在游戏根目录自动创建恢复文件，恢复操作需要该文件存在")
	if can_start:
		print(f"\n\033[96m•\033[0m 按 [\033[92m回车键\033[0m] 开始替换字体")
	
	sys.stdout.write('\n> ')
	sys.stdout.flush()
	
	valid_keys = [b'1', b'2', b'3']
	if has_backup:
		valid_keys.append(b'0')
	if can_start:
		valid_keys.extend([b'\r', b'\n'])

	user_input = read_menu_key(valid_keys, "回车键")
	
	sys.stdout.flush()

	if user_input == '1':
		selected_file = select_file_dialog(
			"选择字体或恢复文件",
			[("支持的文件", "*.ttf;*.otf;*.zip"), ("字体文件", "*.ttf;*.otf"), ("恢复文件", "backup_original_fonts.zip")]
		)
		if selected_file:
			input_file = selected_file
			if input_file.lower().endswith('.zip'):
				if os.path.basename(input_file) == 'backup_original_fonts.zip':
					font_name = "恢复文件 (ZIP)"
				else:
					print_error(f'所选 ZIP 文件名称不正确，应为 "backup_original_fonts.zip"')
					input_file = None
					wait_for_enter('请按回车键返回主菜单')
			else:
				font_name = get_font_name(input_file)
				if not font_name:
					print_error(f'所选文件 "{os.path.basename(input_file)}" 并非有效的字体格式')
					input_file = None
					wait_for_enter('请按回车键返回主菜单')
		continue

	elif user_input == '2':
		selected_path = select_dir_dialog("选择 Counter-Strike Global Offensive 文件夹")
		if selected_path:
			install_location = selected_path
		else:
			continue

	elif user_input == '3':
		while True:
			try:
				val = input('\033[93m•\033[0m 输入 UI 缩放倍率（推荐区间 0.9 至 1.1）：')
				if not val: break
				ui_scale = float(val)
				print()
				break
			except ValueError:
				print('请输入合法的数值')
		continue

	elif user_input == '0' and has_backup:
		# 恢复备份逻辑保持不变，但提示语更新
		if not install_location:
			print('执行还原程序前，请先指定游戏的安装路径')
			selected_path = select_dir_dialog("选择 Counter-Strike Global Offensive 文件夹以进行还原")
			if selected_path:
				install_location = selected_path
			else:
				input('操作已取消，按回车键返回')
				continue
		
		if is_valid_install_location(install_location):
			if restore_backup(install_location):
				finish_execution(0)
			else:
				input('还原失败，按回车键返回主菜单尝试手动处理')
				continue
		else:
			input('指定的路径无效，请确保选择了正确的游戏根目录')
			continue

	elif user_input == "":
		# 空输入按回车即开始操作
		if not input_file:
			input('尚未加载字体源文件，无法执行配置，请先按 1 导入字体')
			continue
		if not is_valid_install_location(install_location):
			input('游戏路径配置不正确或尚未设定，请先确认路径信息')
			continue
		
		# 验证通过，创建备份并跳出循环开始执行
		create_backup(install_location)
		break

	else:
		input('未能识别的指令，请按回车键刷新菜单')
		continue

# 构造目标路径
csgo_fonts, core_fonts, ui_font = get_fonts_paths(install_location)

ensure_directory(csgo_fonts, f'字体目录缺失：{csgo_fonts}', '已自动创建字体目录')
ensure_directory(core_fonts, f'核心配置目录缺失：{core_fonts}', '已自动创建核心配置目录')

remove_existing_fonts(
	csgo_fonts,
	ui_font,
	'正在清理旧版本的 UI 字体索引文件',
	'清理旧版本 UI 字体索引失败',
	'正在移除冲突的旧字体文件：{file}',
	'移除旧字体文件失败: {file}'
)

# 复制新字体文件
try:
	safe_font_name = font_name  # 配置文件中使用的字体名
	shutil.copy(input_file, os.path.join(csgo_fonts, f"{font_name}.ttf"))
	print(f'已将新字体文件部署至目标路径：{font_name}.ttf')
except Exception as e:
	print_error("部署字体文件失败", e)
	finish_execution(1)

write_fonts_conf(csgo_fonts, safe_font_name, ui_scale, '\n正在生成局部字体配置文件：fonts.conf', '生成 fonts.conf 失败')
write_repl_conf(core_fonts, safe_font_name, ui_scale, '正在生成全局字体映射文件：42-repl-global.conf', '生成 42-repl-global.conf 失败')

if verify_files(csgo_fonts, font_name):
	print('\n所有配置任务已成功执行，请启动 Counter-Strike 2 以查看新的字体效果')
	finish_execution(0)
else:
	print('\n配置执行过程中可能存在不完整的操作，请检查上述错误信息')
	finish_execution(1)
