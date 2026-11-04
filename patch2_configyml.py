import pathlib, sys
p = pathlib.Path('/home/user/SkyRiseBank/src/main/resources/config.yml')
t = p.read_text(encoding='utf-8')

# 1. title
old_title = '    title: "<dark_gray>SkyRiseBank <gray>» <white>Wybór konta"'
new_title = '    title: "<dark_gray>SkyRiseBank <gray>» <white>Wybierz konta"'
if old_title not in t:
    print('!! BRAK title'); sys.exit(1)
t = t.replace(old_title, new_title)

# 2. card lore remove last line
old_lore = '''  lore:
    - ""
    - "<gray>Właściciel: <white><player></white>"
    - "<gray>Numer konta: <white><number></white>"
    - "<gray>Rodzaj: <white><type></white>"
    - "<gray>Utworzono: <white><created></white>"
    - ""
    - "<dark_gray>Trzymaj kartę w ręce przy bankomacie."'''
new_lore = '''  lore:
    - ""
    - "<gray>Właściciel: <white><player></white>"
    - "<gray>Numer konta: <white><number></white>"
    - "<gray>Rodzaj: <white><type></white>"
    - "<gray>Utworzono: <white><created></white>"'''
if old_lore not in t:
    print('!! BRAK lore'); sys.exit(1)
t = t.replace(old_lore, new_lore)

p.write_text(t, encoding='utf-8')
print('ok config.yml')
