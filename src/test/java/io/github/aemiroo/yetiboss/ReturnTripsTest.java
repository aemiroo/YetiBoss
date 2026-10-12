package io.github.aemiroo.yetiboss;
import java.nio.file.Path;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
class ReturnTripsTest {
 @TempDir Path dir;
 @Test void repeatedJoinRetainsFirstOriginAndCompletionHasGracePeriod() throws Exception {
  var store=new ReturnTrips(dir.resolve("trips"),1000);UUID p=UUID.randomUUID(),e=UUID.randomUUID(),w=UUID.randomUUID();
  var first=new ReturnTrips.Trip(e,w,1.5,70,-20,90,25,0);store.remember(p,first);
  store.remember(p,new ReturnTrips.Trip(e,w,500,80,300,0,0,0));assertEquals(first,store.get(p));
  store.finish(e,31000);assertTrue(store.ready(30000).isEmpty());assertEquals(1,store.ready(31000).size());
  var resumed=new ReturnTrips(dir.resolve("trips"),2000);assertEquals(first.returning(31000),resumed.get(p));
  resumed.remove(p,first);assertNotNull(resumed.get(p));resumed.remove(p,resumed.get(p));assertNull(new ReturnTrips(dir.resolve("trips"),32000).get(p));
 }
 @Test void restartRecoversUnfinishedVisitsWithoutChangingDestination() throws Exception {
  var store=new ReturnTrips(dir.resolve("trips"),1000);UUID p=UUID.randomUUID();var t=new ReturnTrips.Trip(UUID.randomUUID(),UUID.randomUUID(),-10,80,2.5,180,15,0);
  store.remember(p,t);var restarted=new ReturnTrips(dir.resolve("trips"),2000);assertEquals(t.returning(2000),restarted.get(p));assertEquals(1,restarted.ready(2000).size());
 }
}
