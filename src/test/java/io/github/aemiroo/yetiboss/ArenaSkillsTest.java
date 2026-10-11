package io.github.aemiroo.yetiboss;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ArenaSkillsTest {
 @Test void icefallGrowsWithTheRaidAndCapsEntityLoad() {
  assertEquals(0,ArenaSkills.icefallScale(0).maximumDrops());
  assertEquals(4,ArenaSkills.icefallScale(1).maximumDrops());
  assertEquals(6,ArenaSkills.icefallScale(1).radius());
  assertEquals(8.25,ArenaSkills.icefallScale(4).radius());
  assertEquals(11.25,ArenaSkills.icefallScale(8).radius());
  assertEquals(17.25,ArenaSkills.icefallScale(16).radius());
  assertEquals(10,ArenaSkills.icefallScale(4).maximumDrops());
  assertEquals(18,ArenaSkills.icefallScale(8).maximumDrops());
  assertEquals(30,ArenaSkills.icefallScale(16).maximumDrops());
  assertEquals(32,ArenaSkills.icefallScale(Integer.MAX_VALUE).maximumDrops());
  assertEquals(18,ArenaSkills.icefallScale(Integer.MAX_VALUE).radius());
  for(int n=1;n<100;n++) {
   var before=ArenaSkills.icefallScale(n);var after=ArenaSkills.icefallScale(n+1);
   assertTrue(after.maximumDrops()>=before.maximumDrops());assertTrue(after.radius()>=before.radius());
   assertTrue(after.maximumDrops()<=32);assertTrue(after.radius()<=18);
  }
 }
 @Test void scatteredIceStaysInTheDiskAndAvoidsDuplicateMarkers() {
  assertEquals(0,ArenaSkills.scatterDistance(0,12));assertEquals(12,ArenaSkills.scatterDistance(1,12));
  assertEquals(6,ArenaSkills.scatterDistance(.25,12));
  assertFalse(ArenaSkills.separated(1,0,1));assertTrue(ArenaSkills.separated(2,0,0));
  assertTrue(ArenaSkills.separated(0,4,0));
 }
 @Test void fallAcceleratesAndClampsAtGround() {
  assertEquals(0,ArenaSkills.fall(-20));assertEquals(0,ArenaSkills.fall(0));
  assertEquals(.25,ArenaSkills.fall(10));assertEquals(1,ArenaSkills.fall(20));assertEquals(1,ArenaSkills.fall(40));
  assertTrue(ArenaSkills.fall(20)-ArenaSkills.fall(10)>ArenaSkills.fall(10)-ArenaSkills.fall(0));
  assertTrue(ArenaSkills.WAVE_INTERVAL>ArenaSkills.ICE_WARNING+ArenaSkills.ICE_FALL);
 }
 @Test void tenSecondSpinHealsGraduallyAndHitsOncePerSecond() {
  double total=0;int pulses=0;
  for(int age=1;age<=200;age++) {
   double delta=ArenaSkills.healing(age)-ArenaSkills.healing(age-1);
   assertEquals(.005,delta,1e-9);total+=delta;if(ArenaSkills.pulse(age))pulses++;
  }
  assertEquals(1,total,1e-9);assertEquals(10,pulses);
  assertFalse(ArenaSkills.pulse(0));assertFalse(ArenaSkills.pulse(220));assertEquals(1,ArenaSkills.healing(300));
 }
 @Test void broadCoreFitsTorsoAndExcludesGroundAndAntlers() {
  double width=ArenaSkills.hitboxWidth(6.4),bottom=ArenaSkills.hitboxOffset(6.4);
  assertEquals(3.84,width,1e-9);assertTrue(bottom>1);assertTrue(bottom+width<5.1);
  assertEquals(width*.75,ArenaSkills.hitboxWidth(4.8),1e-9);
 }
 @Test void specialMovesRespectCooldownAndConfiguredDisable() {
  var selector=new AttackSelector();var random=new Random(1);
  var whirl=AttackSelector.Attack.WHIRLWIND;var ice=AttackSelector.Attack.ICEFALL;
  var weights=Map.of(whirl,1,ice,1);
  var first=selector.chooseSequence(0,false,10,5,7,weights,random,false).orElseThrow();
  selector.used(first,0,1000);
  var second=selector.chooseSequence(1,false,10,5,7,weights,random,false).orElseThrow();
  assertNotEquals(first,second);selector.used(second,1,1000);
  assertTrue(selector.chooseSequence(500,true,10,5,7,weights,random,false).isEmpty());
  assertTrue(new AttackSelector().chooseSequence(0,true,10,5,7,Map.of(whirl,0,ice,0),random,false).isEmpty());
 }
}
