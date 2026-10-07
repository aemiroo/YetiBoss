package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class WardenStrikeGateTest {
    @Test void meleeHitsWhenCooldownExpires() {
        assertFalse(WardenStrikeGate.allowed(true,true,59,60));
        assertTrue(WardenStrikeGate.allowed(true,true,60,60));
        assertTrue(WardenStrikeGate.allowed(true,true,61,60));
    }
    @Test void sonicBoomAndNonParticipantsNeverReceiveNativeDamage() {
        assertFalse(WardenStrikeGate.allowed(false,true,100,0));
        assertFalse(WardenStrikeGate.allowed(true,false,100,0));
        assertFalse(WardenStrikeGate.allowed(false,false,100,0));
    }
}
