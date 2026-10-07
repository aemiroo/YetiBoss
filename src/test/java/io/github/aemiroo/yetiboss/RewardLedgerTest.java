package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.*;
import java.util.*;
class RewardLedgerTest {
    @TempDir Path directory;
    @Test void offlineRewardsSurviveRestartAndEncounterCannotQueueTwice() throws Exception {
        Path file=directory.resolve("rewards.yml");UUID encounter=UUID.randomUUID(),player=UUID.randomUUID();
        var ledger=new RewardLedger(file);
        ledger.queue(encounter,Set.of(player),3000);
        ledger.queue(encounter,Set.of(player),3000);
        var restarted=new RewardLedger(file);
        assertTrue(restarted.hasYeti(player));assertEquals(3000,restarted.xp(player));
        restarted.consume(player);
        var afterClaim=new RewardLedger(file);assertFalse(afterClaim.hasYeti(player));assertEquals(0,afterClaim.xp(player));
        afterClaim.queue(encounter,Set.of(player),3000);assertFalse(afterClaim.hasYeti(player));
    }
    @Test void separateVictoriesAccumulateOfflineXp() throws Exception {
        var ledger=new RewardLedger(directory.resolve("rewards.yml"));UUID player=UUID.randomUUID();
        ledger.queue(UUID.randomUUID(),Set.of(player),3000);
        ledger.queue(UUID.randomUUID(),Set.of(player),3000);
        assertEquals(6000,ledger.xp(player));
    }
}
