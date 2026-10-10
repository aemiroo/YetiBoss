package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class BossBalanceTest {
 @Test void defaultUpgradePreservesCustomTuning(){
  for(var t:BossBalance.TUNES){assertEquals(t.current(),BossBalance.upgrade(t.previous(),t));assertEquals(t.current(),BossBalance.upgrade(t.current(),t));assertEquals(123.456,BossBalance.upgrade(123.456,t));}
 }
 @Test void enrageReusesAttacksFasterWithoutZeroCooldowns(){
  assertEquals(220,BossBalance.cooldown(220,false,.8));assertEquals(176,BossBalance.cooldown(220,true,.8));assertEquals(1,BossBalance.cooldown(1,true,.5));
 }
}
