package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class FlightPhaseTest {
 @Test void returnsToGroundAndHealsOnlyDuringHover(){
  assertEquals(0,FlightPhase.height(0,16));assertEquals(16,FlightPhase.height(40,16));assertEquals(16,FlightPhase.height(140,16));assertEquals(0,FlightPhase.height(180,16));
  assertEquals(0,FlightPhase.healProgress(40));assertEquals(.5,FlightPhase.healProgress(90));assertEquals(1,FlightPhase.healProgress(140));assertEquals(1,FlightPhase.healProgress(200));
  double total=0;for(int t=1;t<=180;t++)total+=FlightPhase.healProgress(t)-FlightPhase.healProgress(t-1);assertEquals(1,total,1e-9);
 }
 @Test void flightNeverExceedsItsHeightOrJumpsSuddenly(){
  double previous=0;for(int t=0;t<=180;t++){double h=FlightPhase.height(t,16);assertTrue(h>=0&&h<=16);assertTrue(Math.abs(h-previous)<.7);previous=h;}
 }
}
