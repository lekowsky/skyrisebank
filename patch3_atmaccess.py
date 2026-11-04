import pathlib, sys
p = pathlib.Path('/home/user/SkyRiseBank/src/main/java/pl/skyrise/bank/atm/AtmAccess.java')
t = p.read_text(encoding='utf-8')

old_import = 'import pl.skyrise.bank.model.BankAccountType;'
new_import = '''import pl.skyrise.bank.gui.BankGui;
import pl.skyrise.bank.model.BankAccountType;'''
if old_import not in t:
    print('!! BRAK import'); sys.exit(1)
t = t.replace(old_import, new_import)

old_extra_imports = 'import java.util.Optional;'
new_extra_imports = '''import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;'''
if old_extra_imports not in t:
    print('!! BRAK extra import'); sys.exit(1)
t = t.replace(old_extra_imports, new_extra_imports)

old_class_start = 'public final class AtmAccess {\n\n    private AtmAccess() {\n    }'
new_class_start = '''public final class AtmAccess {

    private static final Map<UUID, Long> COOLDOWN = new ConcurrentHashMap<>();
    private static final Map<UUID, Long> PIN_VERIFIED = new ConcurrentHashMap<>();
    private static final long COOLDOWN_MS = 2000L;
    private static final long BYPASS_MS = 120_000L;

    private AtmAccess() {
    }

    public static void markVerified(UUID playerId) {
        if (playerId == null) {
            return;
        }
        PIN_VERIFIED.put(playerId, System.currentTimeMillis() + BYPASS_MS);
    }

    private static boolean hasValidBypass(UUID playerId) {
        if (playerId == null) {
            return false;
        }
        Long expiry = PIN_VERIFIED.get(playerId);
        if (expiry == null) {
            return false;
        }
        if (System.currentTimeMillis() > expiry) {
            PIN_VERIFIED.remove(playerId);
            return false;
        }
        return true;
    }

    private static boolean isOnCooldown(Player player) {
        long now = System.currentTimeMillis();
        UUID id = player.getUniqueId();
        Long last = COOLDOWN.get(id);
        if (last != null && now - last < COOLDOWN_MS) {
            return true;
        }
        COOLDOWN.put(id, now);
        return false;
    }'''
if old_class_start not in t:
    print('!! BRAK class start'); sys.exit(1)
t = t.replace(old_class_start, new_class_start)

old_use_start = '''    public static void use(SkyRiseBankPlugin plugin, Player player, Atm atm) {
        if (plugin == null || player == null || !player.isOnline()) {
            return;
        }'''
new_use_start = '''    public static void use(SkyRiseBankPlugin plugin, Player player, Atm atm) {
        if (plugin == null || player == null || !player.isOnline()) {
            return;
        }
        if (isOnCooldown(player)) {
            return;
        }'''
if old_use_start not in t:
    print('!! BRAK use start'); sys.exit(1)
t = t.replace(old_use_start, new_use_start)

# modify inside thenAccept found.isEmpty block to check bypass
old_verify = '''                    if (found.isEmpty()) {
                        notify(plugin, player, atm, "atm.no-account");
                        return;
                    }
                    // Karta przyłożona - prosimy o PIN (karta decyduje o koncie).
                    PinDialog.openVerify(plugin, player, atm, found.get());'''
new_verify = '''                    if (found.isEmpty()) {
                        notify(plugin, player, atm, "atm.no-account");
                        return;
                    }
                    if (hasValidBypass(player.getUniqueId())) {
                        plugin.text().send(player, "atm.access-granted");
                        BankGui.openAccounts(plugin, player, found.get().owner());
                        return;
                    }
                    PinDialog.openVerify(plugin, player, atm, found.get());'''
if old_verify not in t:
    print('!! BRAK verify block'); sys.exit(1)
t = t.replace(old_verify, new_verify)

p.write_text(t, encoding='utf-8')
print('ok atmaccess')
