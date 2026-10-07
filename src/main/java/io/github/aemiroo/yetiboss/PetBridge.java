package io.github.aemiroo.yetiboss;
import java.lang.reflect.*;
import java.util.UUID;
import org.bukkit.entity.Player;
import org.bukkit.plugin.Plugin;
final class PetBridge {
    private final Plugin plugin;
    private final Method unlock,ready;
    PetBridge(Plugin plugin) throws ReflectiveOperationException {
        this.plugin=plugin;
        unlock=plugin.getClass().getMethod("unlockYeti",UUID.class);
        ready=plugin.getClass().getMethod("isPetPackReady",Player.class);
    }
    void unlock(UUID id) throws ReflectiveOperationException { unlock.invoke(plugin,id); }
    boolean ready(Player player) {
        try { return Boolean.TRUE.equals(ready.invoke(plugin,player)); }
        catch(ReflectiveOperationException e) { return false; }
    }
}
