package io.github.aemiroo.yetiboss;
import java.io.*;
import java.nio.file.*;
import java.util.*;
/** First pre-join position is retained until a successful return. */
final class ReturnTrips {
 record Trip(UUID encounter,UUID world,double x,double y,double z,float yaw,float pitch,long due) {
  Trip returning(long time){return new Trip(encounter,world,x,y,z,yaw,pitch,time);}
 }
 private final Path file;
 private Map<UUID,Trip> trips=new HashMap<>();
 ReturnTrips(Path file,long now) throws IOException {
  this.file=file;Properties p=new Properties();if(Files.exists(file))try(var in=Files.newInputStream(file)){p.load(in);}
  try {
   for(String key:p.stringPropertyNames()) {
    String[] v=p.getProperty(key).split(",");if(v.length!=8)throw new IllegalArgumentException();
    Trip t=new Trip(UUID.fromString(v[0]),UUID.fromString(v[1]),Double.parseDouble(v[2]),Double.parseDouble(v[3]),Double.parseDouble(v[4]),Float.parseFloat(v[5]),Float.parseFloat(v[6]),Long.parseLong(v[7]));
    if(!Double.isFinite(t.x)||!Double.isFinite(t.y)||!Double.isFinite(t.z)||!Float.isFinite(t.yaw)||!Float.isFinite(t.pitch)||t.due<0)throw new IllegalArgumentException();
    trips.put(UUID.fromString(key),t.due==0?t.returning(now):t);
   }
  } catch(IllegalArgumentException ex){throw new IOException("Invalid return-trip state",ex);}
  save(new HashMap<>(trips));
 }
 Trip get(UUID player){return trips.get(player);}
 Map<UUID,Trip> ready(long now){Map<UUID,Trip> ready=new HashMap<>();trips.forEach((id,t)->{if(t.due>0&&t.due<=now)ready.put(id,t);});return ready;}
 void remember(UUID player,Trip trip) throws IOException {
  if(trips.containsKey(player))return;
  Map<UUID,Trip> next=new HashMap<>(trips);next.put(player,trip);save(next);
 }
 void finish(UUID encounter,long due) throws IOException {
  Map<UUID,Trip> next=new HashMap<>(trips);next.replaceAll((id,t)->t.encounter.equals(encounter)&&t.due==0?t.returning(due):t);save(next);
 }
 void remove(UUID player,Trip expected) throws IOException {
  if(!Objects.equals(trips.get(player),expected))return;
  Map<UUID,Trip> next=new HashMap<>(trips);next.remove(player);save(next);
 }
 private void save(Map<UUID,Trip> next) throws IOException {
  Properties p=new Properties();next.forEach((id,t)->p.setProperty(id.toString(),t.encounter+","+t.world+","+t.x+","+t.y+","+t.z+","+t.yaw+","+t.pitch+","+t.due));
  Files.createDirectories(file.getParent());Path temp=file.resolveSibling(file.getFileName()+".tmp");
  try(var out=Files.newOutputStream(temp)){p.store(out,"YetiBoss saved announcement teleport origins");}
  try{Files.move(temp,file,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}catch(AtomicMoveNotSupportedException ex){Files.move(temp,file,StandardCopyOption.REPLACE_EXISTING);}
  trips=next;
 }
}
