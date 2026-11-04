import pathlib, sys
p = pathlib.Path('/home/user/SkyRiseBank/src/main/java/pl/skyrise/bank/dialog/PinDialog.java')
t = p.read_text(encoding='utf-8')

old_import = 'import pl.skyrise.bank.atm.Atm;'
new_import = 'import pl.skyrise.bank.atm.AtmAccess;\nimport pl.skyrise.bank.atm.Atm;'
if old_import not in t:
    print('!! BRAK atm import'); sys.exit(1)
t = t.replace(old_import, new_import)

old_success = '''        if (plugin.bankAccounts().verifyPin(account, pin)) {
            player.closeDialog();
            plugin.text().send(player, "atm.access-granted");
            // Otwieramy konto z karty - może należeć do kogoś innego niż oglądający.
            BankGui.openAccounts(plugin, player, account.owner());
            return;
        }'''
new_success = '''        if (plugin.bankAccounts().verifyPin(account, pin)) {
            AtmAccess.markVerified(player.getUniqueId());
            player.closeDialog();
            plugin.text().send(player, "atm.access-granted");
            BankGui.openAccounts(plugin, player, account.owner());
            return;
        }'''
if old_success not in t:
    print('!! BRAK success block'); sys.exit(1)
t = t.replace(old_success, new_success)

p.write_text(t, encoding='utf-8')
print('ok pindialog')
