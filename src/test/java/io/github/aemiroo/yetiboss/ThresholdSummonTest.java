package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ThresholdSummonTest {
    @Test void motherAndWardenHaveIndependentOneTimeThresholds() {
        var mother=new ThresholdSummon(.5);var warden=new ThresholdSummon();
        assertFalse(mother.ready(.51));assertTrue(mother.ready(.5));assertFalse(warden.ready(.5));
        mother.spawned();assertFalse(mother.ready(.6));assertFalse(mother.ready(.49));
        assertTrue(warden.ready(.35));warden.spawned();assertFalse(warden.ready(.1));
    }
    @Test void aLargeHitCanCrossBothThresholdsAndFailedSpawnsRetry() {
        var mother=new ThresholdSummon(.5);var warden=new ThresholdSummon();
        assertTrue(mother.ready(.2));assertTrue(warden.ready(.2));
        assertTrue(mother.ready(.2));mother.spawned();assertFalse(mother.ready(.2));
        assertThrows(IllegalArgumentException.class,()->new ThresholdSummon(Double.NaN));
    }
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
