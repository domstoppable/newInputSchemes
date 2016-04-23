# -*- mode: python -*-

import inspect, sys
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'lib/x64' if sys.maxsize > 2**32 else 'lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

a = Analysis(
	['main.py'],
	pathex=[],
	binaries=None,
	datas=[
		('lib/*.dll', 'lib'),
		('lib/x86/*.dll', 'lib/x86/'),
		('lib/x86/*.pyd', 'lib/x86/'),
		('assets/*.png', 'assets'),
		('assets/animals', 'assets/animals'),
		('assets/sounds', 'assets/sounds'),
	],
	hiddenimports=[],
	hookspath=[],
	runtime_hooks=[],
	excludes=[],
	win_no_prefer_redirects=False,
	win_private_assemblies=False,
	cipher=None
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyz, a.scripts, exclude_binaries=True, name='main', debug=False, strip=False, upx=True, console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='main')
