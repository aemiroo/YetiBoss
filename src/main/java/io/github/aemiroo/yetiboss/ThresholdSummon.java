package io.github.aemiroo.yetiboss;
final class ThresholdSummon {
    private boolean summoned;
    private final double threshold;
    ThresholdSummon() {this(.35);}
    ThresholdSummon(double threshold) {
        if(!Double.isFinite(threshold)||threshold<=0||threshold>1)throw new IllegalArgumentException("Invalid summon threshold");
        this.threshold=threshold;
    }
    boolean ready(double healthFraction) {
        return !summoned&&Double.isFinite(healthFraction)&&healthFraction>0&&healthFraction<=threshold;
    }
    void spawned() { summoned=true; }
}
