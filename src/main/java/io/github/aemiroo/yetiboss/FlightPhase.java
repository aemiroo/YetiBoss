package io.github.aemiroo.yetiboss;
/** One short, bounded retreat: ascend, regenerate, telegraph descent, land. */
final class FlightPhase {
 static final int ASCEND=40,HEAL=100,DESCEND=40,DURATION=180;
 static double height(long age,double peak) {
  double t=age<ASCEND?Math.max(0,age)/(double)ASCEND:age<ASCEND+HEAL?1:Math.max(0,1-(age-ASCEND-HEAL)/(double)DESCEND);
  return peak*(.5-.5*Math.cos(Math.PI*t));
 }
 static double healProgress(long age){return Math.max(0,Math.min(1,(age-ASCEND)/(double)HEAL));}
}
