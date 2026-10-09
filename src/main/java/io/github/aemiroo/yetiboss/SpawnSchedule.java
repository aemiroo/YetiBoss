package io.github.aemiroo.yetiboss;
import java.io.*;
import java.nio.file.*;
import java.util.*;
/** Wall-clock schedule: persisted warning deduplication and no catch-up bursts. */
final class SpawnSchedule {
    private final Path file;
    private long next;
    private final Set<Integer> warned=new HashSet<>();
    SpawnSchedule(Path file,long now,long interval) throws IOException {
        this.file=file;Properties p=new Properties();
        if(Files.exists(file))try(var in=Files.newInputStream(file)){p.load(in);}
        try {
            next=Long.parseLong(p.getProperty("next",Long.toString(now+interval)));
            if(next<=0)throw new NumberFormatException();
            for(String s:p.getProperty("warned","").split(","))if(!s.isBlank())warned.add(Integer.parseInt(s));
        } catch(NumberFormatException ex){throw new IOException("Invalid spawn schedule state",ex);}
        save();
    }
    long next(){return next;}
    List<Integer> warnings(long now,List<Integer> minutes) throws IOException {
        if(now>=next)return List.of();
        List<Integer> due=new ArrayList<>();
        for(int m:minutes)if(next-now<=m*60000L&&!warned.contains(m))due.add(m);
        // If the server comes online late, send only the nearest warning.
        if(due.isEmpty())return due;
        int nearest=Collections.min(due);warned.addAll(due);save();return List.of(nearest);
    }
    void advance(long now,long interval) throws IOException {
        next+=Math.max(1,(now-next)/interval+1)*interval;warned.clear();save();
    }
    private void save() throws IOException {
        Files.createDirectories(file.getParent());Properties p=new Properties();p.setProperty("next",Long.toString(next));
        p.setProperty("warned",String.join(",",warned.stream().sorted().map(String::valueOf).toList()));
        Path temp=file.resolveSibling(file.getFileName()+".tmp");
        try(var out=Files.newOutputStream(temp)){p.store(out,"YetiBoss automatic spawn schedule");}
        try{Files.move(temp,file,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}
        catch(AtomicMoveNotSupportedException ex){Files.move(temp,file,StandardCopyOption.REPLACE_EXISTING);}
    }
}
