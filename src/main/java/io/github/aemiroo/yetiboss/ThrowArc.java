package io.github.aemiroo.yetiboss;

/** Level-ground ballistic estimate using the player's air drag and gravity. */
final class ThrowArc {
    private ThrowArc() {}
    static double horizontalSpeed(double distance,double height) {
        double y=height,vy=.55,drag=1,travel=0;
        for(int tick=0;tick<100;tick++) {
            y+=vy;travel+=drag;
            if(y<=0)break;
            vy=(vy-.08)*.98;drag*=.91;
        }
        return distance/travel;
    }
}
