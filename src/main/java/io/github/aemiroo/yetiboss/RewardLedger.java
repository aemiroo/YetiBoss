package io.github.aemiroo.yetiboss;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import org.bukkit.configuration.InvalidConfigurationException;
import org.bukkit.configuration.file.YamlConfiguration;
final class RewardLedger {
    private final Path file;
    private YamlConfiguration yaml=new YamlConfiguration();
    RewardLedger(Path file) throws IOException {
        this.file=file;
        if(Files.exists(file)) {
            try { yaml.load(file.toFile()); }
            catch(InvalidConfigurationException e) { throw new IOException("Invalid rewards.yml",e); }
        }
        if(yaml.getConfigurationSection("pending")!=null)
            for(String id:yaml.getConfigurationSection("pending").getKeys(false)) {
                try { UUID.fromString(id); } catch(IllegalArgumentException e) { throw new IOException("Invalid reward UUID",e); }
                if(yaml.getInt("pending."+id+".xp",-1)<0) throw new IOException("Invalid queued XP");
            }
    }
    private YamlConfiguration copy() {
        YamlConfiguration result=new YamlConfiguration();
        try { result.loadFromString(yaml.saveToString()); }
        catch(InvalidConfigurationException e) { throw new IllegalStateException(e); }
        return result;
    }
    void queue(UUID encounter,Set<UUID> players,int xp) throws IOException {
        if(yaml.getBoolean("completed."+encounter)) return;
        YamlConfiguration next=copy();
        next.set("completed."+encounter,true);
        for(UUID id:players) {
            String key="pending."+id;
            next.set(key+".yeti",true);
            long total=(long)next.getInt(key+".xp",0)+xp;
            next.set(key+".xp",(int)Math.min(Integer.MAX_VALUE,total));
        }
        AtomicYaml.save(next,file); yaml=next;
    }
    boolean hasYeti(UUID id) { return yaml.getBoolean("pending."+id+".yeti"); }
    int xp(UUID id) { return yaml.getInt("pending."+id+".xp",0); }
    void consume(UUID id) throws IOException {
        YamlConfiguration next=copy();
        next.set("pending."+id,null);
        AtomicYaml.save(next,file);yaml=next;
    }
}
