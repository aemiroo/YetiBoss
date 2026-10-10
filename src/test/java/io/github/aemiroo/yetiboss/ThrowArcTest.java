package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ThrowArcTest {
    @Test void reachesRequestedLevelGroundDistance() {
        for(double distance:new double[]{5,10,15}) {
            double vx=ThrowArc.horizontalSpeed(distance,2.2),vy=.55,y=2.2,x=0;
            for(int tick=0;tick<100;tick++) {
                x+=vx;y+=vy;
                if(y<=0)break;
                vx*=.91;vy=(vy-.08)*.98;
            }
            assertEquals(distance,x,1e-6);
        }
    }
}
