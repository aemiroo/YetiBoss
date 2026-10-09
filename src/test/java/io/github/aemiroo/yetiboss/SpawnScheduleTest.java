package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;
class SpawnScheduleTest {
 @TempDir Path dir;
 @Test void warningsAndNextSlotSurviveRestart() throws Exception {
  long interval=10800000,now=1000000;Path file=dir.resolve("schedule.properties");
  var s=new SpawnSchedule(file,now,interval);long next=s.next();
  assertEquals(List.of(15),s.warnings(next-900000,List.of(15,5)));
  s=new SpawnSchedule(file,now+1000,interval);
  assertTrue(s.warnings(next-600000,List.of(15,5)).isEmpty());
  assertEquals(List.of(5),s.warnings(next-300000,List.of(15,5)));
  s.advance(next,interval);assertEquals(next+interval,new SpawnSchedule(file,next,interval).next());
 }
 @Test void downtimeProducesOneSlotAndOnlyNearestWarning() throws Exception {
  var s=new SpawnSchedule(dir.resolve("s"),1000,10800000);long next=s.next();
  assertEquals(List.of(5),s.warnings(next-60000,List.of(15,5)));
  assertTrue(s.warnings(next,List.of(15,5)).isEmpty());
  s.advance(next+10800000*4+100,10800000);assertEquals(next+10800000*5,s.next());
 }
}
