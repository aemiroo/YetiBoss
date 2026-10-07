package io.github.aemiroo.yetiboss;
import java.util.*;
final class Participation {
    private final Set<UUID> participants=new HashSet<>();
    private boolean finished;
    void damage(UUID player,double acceptedDamage) {
        if(!finished && Double.isFinite(acceptedDamage) && acceptedDamage>0) participants.add(player);
    }
    Set<UUID> finish() {
        if(finished) return Set.of();
        finished=true;
        return Set.copyOf(participants);
    }
    int size() { return participants.size(); }
}
