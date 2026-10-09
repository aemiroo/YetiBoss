package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
class AttackSelectorTest {
    final Map<AttackSelector.Attack,Integer> weights=Map.of(
        AttackSelector.Attack.ICE_BALL,5,AttackSelector.Attack.SWIPE,4,
        AttackSelector.Attack.SLAM,2,AttackSelector.Attack.BARRAGE,3);
    @Test void rangedNormalPhaseOnlyThrowsAndWaitsUntilAnAlternativeIsPossible() {
        var selector=new AttackSelector();
        assertEquals(AttackSelector.Attack.ICE_BALL,selector.choose(0,false,20,5,7,weights,new Random(1)).orElseThrow());
        selector.used(AttackSelector.Attack.ICE_BALL,0,90);
        assertTrue(selector.choose(200,false,20,5,7,weights,new Random(1)).isEmpty());
    }
    @Test void noRepeatedAttacksAndCooldownsAreHonored() {
        var selector=new AttackSelector();var random=new Random(7);
        var nextReady=new EnumMap<AttackSelector.Attack,Long>(AttackSelector.Attack.class);
        AttackSelector.Attack last=null;
        for(long tick=0;tick<10000;tick+=5) {
            var choice=selector.choose(tick,true,2,5,7,weights,random);
            if(choice.isEmpty()) continue;
            var attack=choice.orElseThrow();
            assertNotEquals(last,attack);
            assertTrue(tick>=nextReady.getOrDefault(attack,0L));
            selector.used(attack,tick,100);nextReady.put(attack,tick+100);last=attack;
        }
    }
    @Test void barrageRequiresEnrageAndMeleeRequiresRange() {
        var selector=new AttackSelector();
        for(int i=0;i<100;i++) assertEquals(AttackSelector.Attack.ICE_BALL,
            selector.choose(0,false,20,5,7,weights,new Random(i)).orElseThrow());
        assertTrue(selector.choose(0,true,20,5,7,Map.of(AttackSelector.Attack.BARRAGE,1),new Random()).isPresent());
        assertTrue(selector.choose(0,false,20,5,7,Map.of(AttackSelector.Attack.BARRAGE,1),new Random()).isEmpty());
    }
    @Test void snowGolemsCanBeRandomlySummonedAtRangeAndCapCanDisableTheAttack() {
        var selector=new AttackSelector();
        assertEquals(AttackSelector.Attack.SNOW_GOLEMS,selector.choose(0,false,30,5,7,
            Map.of(AttackSelector.Attack.SNOW_GOLEMS,2),new Random()).orElseThrow());
        assertTrue(selector.choose(0,false,30,5,7,
            Map.of(AttackSelector.Attack.SNOW_GOLEMS,0),new Random()).isEmpty());
    }
    @Test void roarRequiresCloseRangeAndHonorsCooldown() {
        var selector=new AttackSelector();var roar=AttackSelector.Attack.ROAR;
        var only=Map.of(roar,2);
        assertTrue(selector.choose(0,false,20,5,7,only,new Random()).isEmpty());
        assertEquals(roar,selector.choose(0,false,3,5,7,only,new Random()).orElseThrow());
        selector.used(roar,0,260);
        assertTrue(selector.choose(100,false,3,5,7,only,new Random()).isEmpty());
    }
    @Test void chargeRequiresDodgeableMidRange() {
        var weights=Map.of(AttackSelector.Attack.CHARGE,1);
        for(double distance:new double[]{2,25})assertTrue(new AttackSelector().choose(0,false,distance,5,7,weights,new Random()).isEmpty());
        assertEquals(AttackSelector.Attack.CHARGE,new AttackSelector().choose(0,false,10,5,7,weights,new Random()).orElseThrow());
    }
    @Test void zeroWeightsNeverSelect() {
        assertTrue(new AttackSelector().choose(0,true,0,5,7,Map.of(),new Random()).isEmpty());
    }
    @Test void weightsGiveMultipleOutcomes() {
        Set<AttackSelector.Attack> observed=new HashSet<>();
        var random=new Random(432);
        for(int i=0;i<1000;i++) observed.add(new AttackSelector().choose(0,true,2,5,7,weights,random).orElseThrow());
        assertEquals(weights.keySet(),observed);
    }
}
