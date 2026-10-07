package io.github.aemiroo.yetiboss;
import java.io.*;
import java.nio.file.*;
import org.bukkit.configuration.file.YamlConfiguration;
final class AtomicYaml {
    static void save(YamlConfiguration yaml,Path file) throws IOException {
        Path parent=file.toAbsolutePath().getParent();
        Files.createDirectories(parent);
        Path temp=Files.createTempFile(parent,"rewards-",".tmp");
        try {
            yaml.save(temp.toFile());
            try { Files.move(temp,file,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING); }
            catch(AtomicMoveNotSupportedException e) { Files.move(temp,file,StandardCopyOption.REPLACE_EXISTING); }
        } finally { Files.deleteIfExists(temp); }
    }
}
