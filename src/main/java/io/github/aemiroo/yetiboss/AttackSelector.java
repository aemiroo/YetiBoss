package io.github.aemiroo.yetiboss;

import java.util.*;
import java.util.random.RandomGenerator;

final class AttackSelector {
    enum Attack {
        ICE_BALL("ice-ball"), SWIPE("swipe"), SLAM("slam"), BARRAGE("barrage"), SNOW_GOLEMS("snow-golems"), GRAB_SLAM("grab-slam"), ROAR("roar");
        final String key;
        Attack(String key) { this.key=key; }
    }
    private final Map<Attack,Long> ready = new EnumMap<>(Attack.class);
    private Attack last;
    Optional<Attack> choose(long tick, boolean enraged, double distance,
                            double swipeRange, double slamRange,
                            Map<Attack,Integer> weights, RandomGenerator random) {
        List<Attack> options = new ArrayList<>();
        for (Attack attack : Attack.values()) {
            if (attack==last || ready.getOrDefault(attack,0L)>tick) continue;
            if (attack==Attack.BARRAGE && !enraged) continue;
            if (attack==Attack.SWIPE && distance>swipeRange) continue;
            if ((attack==Attack.SLAM || attack==Attack.ROAR) && distance>slamRange) continue;
            if (weights.getOrDefault(attack,0)>0) options.add(attack);
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
