package io.github.aemiroo.yetiboss;

/** Native Warden melee may hit arena participants; other native damage stays blocked. */
final class WardenStrikeGate {
    private WardenStrikeGate() {}
    static boolean allowed(boolean melee,boolean eligible,long tick,long ready) {
        return melee&&eligible&&tick>=ready;
    }
}
