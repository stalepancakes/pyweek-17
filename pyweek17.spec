# -*- mode: python -*-
a = Analysis(['pyweek17.py'],
             pathex=['pyweek17'],
             hiddenimports=[],
             hookspath=['bacon'])
pyz = PYZ(a.pure)
res_tree = Tree('res', prefix='res')
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='build/pyweek17.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               res_tree,
               strip=None,
               upx=True,
               name='dist/pyweek17')
app = BUNDLE(coll,
             name='pyweek17.app',
             icon=None)