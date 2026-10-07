package io.github.aemiroo.yetiboss;
final class ThresholdSummon {
    private boolean summoned;
    boolean ready(double healthFraction) {
        return !summoned&&Double.isFinite(healthFraction)&&healthFraction>0&&healthFraction<=0.35;
    }
    void spawned() { summoned=true; }
}
