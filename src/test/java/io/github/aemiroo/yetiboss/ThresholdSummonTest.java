package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ThresholdSummonTest {
    @Test void thresholdIncludes35PercentAndTriggersOnce() {
        var trigger=new ThresholdSummon();
        assertFalse(trigger.ready(.36));assertTrue(trigger.ready(.35));
        trigger.spawned();assertFalse(trigger.ready(.35));assertFalse(trigger.ready(.1));
    }
    @Test void invalidOrDeadHealthDoesNotSummonAndFailedSpawnCanRetry() {
        var trigger=new ThresholdSummon();
        assertFalse(trigger.ready(Double.NaN));assertFalse(trigger.ready(-.1));assertFalse(trigger.ready(0));
        assertTrue(trigger.ready(.3));assertTrue(trigger.ready(.3));
        assertTrue(new ThresholdSummon().ready(.3));
    }
}
