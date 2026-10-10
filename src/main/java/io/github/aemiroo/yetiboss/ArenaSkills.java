package io.github.aemiroo.yetiboss;
/** Pure timing/geometry shared by the live attacks and their tests. */
final class ArenaSkills {
 static final int ICE_WARNING=35,ICE_FALL=20,WAVE_INTERVAL=60,WHIRL_DURATION=200;
 static double fall(double age){double t=Math.max(0,Math.min(1,age/ICE_FALL));return t*t;}
 static double healing(int age){return Math.max(0,Math.min(1,age/(double)WHIRL_DURATION));}
 static double horizontalSquared(double x,double z){return x*x+z*z;}
 static boolean pulse(int age){return age>0&&age<=WHIRL_DURATION&&age%20==0;}
 static double hitboxWidth(double modelScale){return modelScale*.60;}
 static double hitboxOffset(double modelScale){return modelScale*.18;}
}
