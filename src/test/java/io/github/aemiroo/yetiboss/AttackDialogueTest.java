package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static io.github.aemiroo.yetiboss.AttackSelector.Attack;
class AttackDialogueTest {
    @Test void distinguishesOverhauledMovesAndMotherSwipe() {
        assertTrue(AttackDialogue.warning(Attack.GRAB_SLAM,true).contains("throw"));
        assertFalse(AttackDialogue.warning(Attack.GRAB_SLAM,true).contains("slam"));
        assertTrue(AttackDialogue.warning(Attack.SWIPE,true).contains("two swipes"));
        assertFalse(AttackDialogue.warning(Attack.SWIPE,false).contains("combo"));
        for(Attack attack:Attack.values())assertFalse(AttackDialogue.warning(attack,true).isBlank());
    }
}
