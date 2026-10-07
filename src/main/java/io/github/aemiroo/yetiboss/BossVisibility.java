package io.github.aemiroo.yetiboss;
final class BossVisibility {
    private BossVisibility() {}
    static boolean custom(int viewers,int ready,boolean displayValid) {
        return displayValid&&viewers>0&&ready==viewers;
    }
}
