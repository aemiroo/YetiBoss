package io.github.aemiroo.yetiboss;
import java.util.*;
/** Encounter-local exposure; dodging for eight seconds clears all stacks. */
final class CombatPressure {
 record Exposure(int stacks,long expires) {}
 private final Map<UUID,Exposure> exposure=new HashMap<>();
 int stacks(UUID player,long tick) {
  Exposure state=exposure.get(player);
  if(state==null)return 0;
  if(tick>=state.expires){exposure.remove(player);return 0;}
  return state.stacks;
 }
 int accepted(UUID player,long tick) {
  int count=Math.min(5,stacks(player,tick)+1);
  exposure.put(player,new Exposure(count,tick+160));return count;
 }
 double multiplier(UUID player,long tick){return 1+stacks(player,tick)*.08;}
}
