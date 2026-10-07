package io.github.aemiroo.yetiboss;

import org.bukkit.Bukkit;
import org.bukkit.plugin.Plugin;
import java.util.UUID;

/** Optional API lookup, used once on login rather than during animation ticks. */
final class BedrockPlayers {
    private BedrockPlayers() { }
    static boolean displayBridgeEnabled() {
        Plugin geyser = Bukkit.getPluginManager().getPlugin("Geyser-Spigot");
        if (geyser == null || !geyser.isEnabled()) return false;
        try {
            ClassLoader loader = geyser.getClass().getClassLoader();
            Class<?> api = Class.forName("org.geysermc.geyser.api.GeyserApi", true, loader);
            Object instance = api.getMethod("api").invoke(null);
            Object manager = api.getMethod("extensionManager").invoke(instance);
            Class<?> managers = Class.forName("org.geysermc.geyser.api.extension.ExtensionManager", true, loader);
            Object bridge = managers.getMethod("extension", String.class).invoke(manager, "geyserdisplayentity");
            Class<?> extensions = Class.forName("org.geysermc.geyser.api.extension.Extension", true, loader);
            return bridge != null && Boolean.TRUE.equals(extensions.getMethod("isEnabled").invoke(bridge));
        } catch (ReflectiveOperationException | LinkageError ignored) { return false; }
    }
    static boolean contains(UUID uuid) {
        Plugin floodgate = Bukkit.getPluginManager().getPlugin("floodgate");
        if (floodgate != null && floodgate.isEnabled()) {
            try {
                Class<?> api = Class.forName("org.geysermc.floodgate.api.FloodgateApi", true,
                        floodgate.getClass().getClassLoader());
                Object instance = api.getMethod("getInstance").invoke(null);
                if (Boolean.TRUE.equals(api.getMethod("isFloodgatePlayer", UUID.class).invoke(instance, uuid)))
                    return true;
            } catch (ReflectiveOperationException | LinkageError ignored) { }
        }
        Plugin geyser = Bukkit.getPluginManager().getPlugin("Geyser-Spigot");
        if (geyser != null && geyser.isEnabled()) {
            try {
                Class<?> api = Class.forName("org.geysermc.geyser.api.GeyserApi", true,
                        geyser.getClass().getClassLoader());
                Object instance = api.getMethod("api").invoke(null);
                return api.getMethod("connectionByUuid", UUID.class).invoke(instance, uuid) != null;
            } catch (ReflectiveOperationException | LinkageError ignored) { }
        }
        return false;
    }
}
