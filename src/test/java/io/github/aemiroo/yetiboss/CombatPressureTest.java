package io.github.aemiroo.yetiboss;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class CombatPressureTest {
 @Test void exposureCapsAndExpiresFromLastAcceptedHit() {
  var pressure=new CombatPressure();var player=UUID.randomUUID();var other=UUID.randomUUID();
  for(int i=0;i<10;i++)pressure.accepted(player,i*10);
  assertEquals(5,pressure.stacks(player,249));assertEquals(1.4,pressure.multiplier(player,249),1e-9);
  assertEquals(1,pressure.multiplier(other,249));assertEquals(0,pressure.stacks(player,250));
  assertEquals(1,pressure.accepted(player,250));
 }
 @Test void sequencedCombatHonorsRangeDisablesAndCooldowns() {
  var selector=new AttackSelector();var random=new Random(5);
  var weights=new EnumMap<AttackSelector.Attack,Integer>(AttackSelector.Attack.class);
  for(var attack:AttackSelector.Attack.values())weights.put(attack,1);
  weights.put(AttackSelector.Attack.SNOW_GOLEMS,0);
  var ready=new EnumMap<AttackSelector.Attack,Long>(AttackSelector.Attack.class);
  AttackSelector.Attack last=null;boolean barrage=false;
  for(long tick=0;tick<5000;tick+=5) {
   var choice=selector.chooseSequence(tick,false,20,5,7,weights,random,false);
   if(choice.isEmpty())continue;
   var attack=choice.orElseThrow();
   assertTrue(Set.of(AttackSelector.Attack.ICE_BALL,AttackSelector.Attack.BARRAGE,AttackSelector.Attack.GRAB_SLAM).contains(attack));
   assertNotEquals(last,attack);assertTrue(tick>=ready.getOrDefault(attack,0L));
   barrage|=attack==AttackSelector.Attack.BARRAGE;
   selector.used(attack,tick,100);ready.put(attack,tick+100);last=attack;
  }
  assertTrue(barrage);
 }
 @Test void motherOpensWithSupportBarrage() {
  assertEquals(AttackSelector.Attack.BARRAGE,new AttackSelector().chooseSequence(0,false,10,5,7,
   Map.of(AttackSelector.Attack.BARRAGE,1,AttackSelector.Attack.ICE_BALL,1),new Random(1),true).orElseThrow());
 }
}
