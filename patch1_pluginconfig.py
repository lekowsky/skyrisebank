import pathlib, re, sys
p = pathlib.Path('/home/user/SkyRiseBank/src/main/java/pl/skyrise/bank/config/PluginConfig.java')
t = p.read_text(encoding='utf-8')

old_title = 'config.getString(path + ".title", "<dark_gray>SkyRiseBank <gray>» <white>Wybór konta")'
new_title = 'config.getString(path + ".title", "<dark_gray>SkyRiseBank <gray>» <white>Wybierz konta")'
if old_title not in t:
    print('!! BRAK ANCHORA title'); sys.exit(1)
t = t.replace(old_title, new_title)

old_slots = 'Gui.slots(config, path + ".slots", List.of(10, 11, 12, 13))'
new_slots = 'Gui.slots(config, path + ".slots", List.of(10, 12, 14, 16))'
if old_slots not in t:
    print('!! BRAK ANCHORA slots'); sys.exit(1)
t = t.replace(old_slots, new_slots)

old_lore_block = '''            if (lore.isEmpty()) {
                lore = List.of("",
                        "<gray>Właściciel: <white><player></white>",
                        "<gray>Numer konta: <white><number></white>",
                        "<gray>Rodzaj: <white><type></white>",
                        "<gray>Utworzono: <white><created></white>",
                        "",
                        "<dark_gray>Trzymaj kartę w ręce przy bankomacie.");
            }'''
new_lore_block = '''            if (lore.isEmpty()) {
                lore = List.of("",
                        "<gray>Właściciel: <white><player></white>",
                        "<gray>Numer konta: <white><number></white>",
                        "<gray>Rodzaj: <white><type></white>",
                        "<gray>Utworzono: <white><created></white>");
            }'''
if old_lore_block not in t:
    print('!! BRAK ANCHORA lore block'); sys.exit(1)
t = t.replace(old_lore_block, new_lore_block)

p.write_text(t, encoding='utf-8')
print('ok pluginconfig')
