package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class BossVisibilityTest {
    @Test void failedOrMissingPackUsesVisibleFallback() {
        assertFalse(BossVisibility.custom(1,0,true));
        assertFalse(BossVisibility.custom(2,1,true));
        assertFalse(BossVisibility.custom(0,0,true));
        assertFalse(BossVisibility.custom(1,1,false));
    }
    @Test void allViewersReadyEnablesCustomModel() {
        assertTrue(BossVisibility.custom(1,1,true));
        assertTrue(BossVisibility.custom(3,3,true));
    }
}
