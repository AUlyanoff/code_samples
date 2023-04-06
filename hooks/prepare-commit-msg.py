#!/usr/bin/python3

"""
    Локальный хук на коммит. Требует Python 3.9+
    Если имя комита содержит регистронезависимую подстроку "SOWA",
    то файлы Совы копируются из МДМ-а в Требования, там архивируются,
    и для архива создаётся и пушится коммит в удалённый репо Требований.
    Т.о. получаем всегда актуальную ссылку на архив по задаче 32999.
"""

import sys
import os
import shutil
import git
import zipfile
import datetime

green = "\033[1;32m"
red = "\033[1;31m"
color_off = "\033[0m"
blue = "\033[1;34m"
yellow = "\033[1;33m"

# это коммит про Сову ?
path_mdm = os.getcwd()
fcname = sys.argv[1]
if fcname is None:
    # непонятно, значит не про Сову
    sys.exit(0)
else:
    os.chdir(path_mdm)
    with open(fcname, 'r') as f:
        cname = f.read()
        # print('user commit = ', cname.upper())
    if 'SOWA' not in cname.upper():
        # не про Сову
        sys.exit(0)
    else:
        # да, это коммит про Сову
        print("autopush SOWA-zipfile stated")

# выясняем, откуда-куда копировать и архивировать и что пушим
# для этого надо тупо знать структуру папок проектов МДМ и Требований
path_from = os.path.join(path_mdm, 'src', 'json_schemas')
nfiles = os.listdir(path_from)
# print(f'from\t{color_off}{path_from}')
os.chdir('../SafePhone-requirements')
path_req = os.getcwd()
path_to = os.path.join(path_req, 'implementation', 'component', 'iosmdm', 'open_api_sowa', 'components', 'schemas')
# print(f'to\t{color_off}{path_to}')
os.chdir(path_to)
os.chdir('../../..')
path_zip = os.getcwd()
fzipname = 'sowa.zip'
# print(f"zip\t{path_zip}, {fzipname}")

# Проверяем существование репозитария МДМ
repo_mdm = None
try:
    print(f"check existence MDM repository ", end="")
    repo_mdm = git.Repo(path_mdm)
    print(f"\t...{green}ok{color_off}")
except git.exc.NoSuchPathError:
    print("Can't open MDM repository {repo_mdm}")
    sys.exit(1)

# Проверяем существование репозитария Требований
repo_req = None
try:
    print(f"check existence REQ repository ", end="")
    repo_req = git.Repo(path_req)
    print(f"\t...{green}ok{color_off}")
except git.exc.NoSuchPathError:
    print(f"Can't open REQ repository {repo_req}")
    sys.exit(2)

# Копирование свеженьких файлов Совы из МДМ в Требования
os.chdir(path_mdm)
print(f'copying started ', end='')
for nfile in nfiles:
    shutil.copy2(os.path.join(path_from, nfile), path_to)
    # print (f'{nfile}, ', end='')
print(f'\t\t...{green}ok{color_off}')

# Архивируем свеженькие json и любые yaml, обход папок рекурсивный
print(f'zip started ', end='')
sowa_zip = zipfile.ZipFile(os.path.join(path_zip, fzipname), 'w')
for folder, subfolders, files in os.walk(path_zip):
    for file in files:
        if file.endswith('.json') or file.endswith('.yaml'):
            sowa_zip.write(os.path.join(folder, file), \
            os.path.relpath(os.path.join(folder,file), path_zip), \
            compress_type = zipfile.ZIP_DEFLATED)
            # print (f'{file}, ', end='')
sowa_zip.close()
print(f'\t\t\t...{green}ok{color_off}')

# Коммитим новенький zip
os.chdir(path_req)
commit_message = 'TS-32999 SOWA autozip ' + str (datetime.datetime.now().ctime())
print(f'commit started ', end='')
repo_req.index.add(os.path.join(path_zip, fzipname))
repo_req.index.commit(commit_message)
print(f'\t\t\t...{green}ok{color_off}')

# Пушим новенький zip
print(f'push started ', end='')
repo_req.git.push()
print(f'\t\t\t...{green}ok{color_off}')

print(f"autopush SOWA zipfile ended\t...{green}ok{color_off}")
sys.exit(0)
