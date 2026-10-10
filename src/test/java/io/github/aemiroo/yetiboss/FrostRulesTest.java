package io.github.aemiroo.yetiboss;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class FrostRulesTest {
 @Test void rejectsIncompatibleWeaponEnchants(){
  assertTrue(FrostRules.compatible("frostfang",Set.of("sharpness","looting","mending")));
  assertFalse(FrostRules.compatible("frostfang",Set.of("fire_aspect")));
  assertFalse(FrostRules.compatible("frostfang",Set.of("knockback")));
  for(String e:List.of("flame","punch","infinity"))assertFalse(FrostRules.compatible("frostbow",Set.of(e)));
  assertTrue(FrostRules.compatible("frostbow",Set.of("power","unbreaking","mending")));
 }
 @Test void fortuneAndSilkTouchRemainExclusive(){
  assertTrue(FrostRules.compatible("frostpickaxe",Set.of("efficiency","fortune")));
  assertTrue(FrostRules.compatible("frostpickaxe",Set.of("silk_touch","mending")));
  assertFalse(FrostRules.compatible("frostpickaxe",Set.of("fortune","silk_touch")));
 }
 @Test void frostbiteCombinesWithLevelCap(){
  assertEquals(1,FrostRules.combine(0,1));assertEquals(2,FrostRules.combine(1,1));
  assertEquals(3,FrostRules.combine(2,2));assertEquals(3,FrostRules.combine(3,3));
  assertEquals(3,FrostRules.combine(3,1));
 }
 @Test void rolledAmountsStayWithinInclusiveRange(){
  Random random=new Random(42);Set<Integer> seen=new HashSet<>();
  for(int i=0;i<1000;i++){int n=FrostRules.amount(random,2,4);assertTrue(n>=2&&n<=4);seen.add(n);}
  assertEquals(Set.of(2,3,4),seen);assertEquals(1,FrostRules.amount(random,1,1));
 }
}
