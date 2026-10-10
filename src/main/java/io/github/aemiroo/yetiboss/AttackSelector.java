package io.github.aemiroo.yetiboss;

import java.util.*;
import java.util.random.RandomGenerator;

final class AttackSelector {
    enum Attack {
        ICE_BALL("ice-ball"), SWIPE("swipe"), SLAM("slam"), BARRAGE("barrage"), SNOW_GOLEMS("snow-golems"), GRAB_SLAM("grab-slam"), ROAR("roar"), CHARGE("charge"), SONIC_BOOM("sonic-boom");
        final String key;
        Attack(String key) { this.key=key; }
    }
    private final Map<Attack,Long> ready = new EnumMap<>(Attack.class);
    private Attack last;
    private int sequence;
    private boolean planned;
    private boolean support;
    Optional<Attack> chooseSequence(long tick,boolean enraged,double distance,double swipeRange,double slamRange,
            Map<Attack,Integer> weights,RandomGenerator random,boolean mother) {
        planned=true;support=mother;
        try {return choose(tick,enraged,distance,swipeRange,slamRange,weights,random);}
        finally {planned=false;}
    }
    Optional<Attack> choose(long tick, boolean enraged, double distance,
                            double swipeRange, double slamRange,
                            Map<Attack,Integer> weights, RandomGenerator random) {
        List<Attack> options = new ArrayList<>();
        for (Attack attack : Attack.values()) {
            if (attack==last || ready.getOrDefault(attack,0L)>tick) continue;
            if (attack==Attack.BARRAGE && !enraged && !planned) continue;
            if (attack==Attack.SONIC_BOOM && (distance<6 || distance>16)) continue;
            if (attack==Attack.CHARGE && (distance<6 || distance>18)) continue;
            if (attack==Attack.SWIPE && distance>swipeRange) continue;
            if ((attack==Attack.SLAM || attack==Attack.ROAR) && distance>slamRange) continue;
            if (weights.getOrDefault(attack,0)>0) options.add(attack);
        }
        if(planned&&!options.isEmpty()) {
            Attack[] pattern=support
                ?new Attack[]{Attack.BARRAGE,Attack.ROAR,Attack.GRAB_SLAM,Attack.ICE_BALL,Attack.SWIPE,Attack.SLAM}
                :enraged?new Attack[]{Attack.CHARGE,Attack.SWIPE,Attack.BARRAGE,Attack.GRAB_SLAM,Attack.SONIC_BOOM,Attack.SLAM,Attack.SNOW_GOLEMS}
                :new Attack[]{Attack.ICE_BALL,Attack.CHARGE,Attack.SWIPE,Attack.ROAR,Attack.GRAB_SLAM,Attack.BARRAGE,Attack.SLAM,Attack.SNOW_GOLEMS,Attack.SONIC_BOOM};
            for(int i=0;i<pattern.length;i++) {
                int index=Math.floorMod(sequence+i,pattern.length);
                if(options.contains(pattern[index])) {sequence=index+1;return Optional.of(pattern[index]);}
            }
        }
        int total=options.stream().mapToInt(weights::get).sum();
        if(total==0) return Optional.empty(); // Wait instead of breaking cooldowns.
        int roll=random.nextInt(total);
        for(Attack attack:options) {
            roll-=weights.get(attack);
            if(roll<0) return Optional.of(attack);
        }
        throw new IllegalStateException("Invalid attack weights");
    }
    void used(Attack attack,long tick,int cooldown) {
        last=attack;
        ready.put(attack,tick+cooldown);
    }
}
