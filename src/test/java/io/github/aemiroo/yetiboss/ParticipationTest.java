package io.github.aemiroo.yetiboss;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
class ParticipationTest {
    @Test void positiveDamageCountsOnceAndFinishCannotRepeat() {
        var p=new Participation();UUID a=UUID.randomUUID(),b=UUID.randomUUID();
        p.damage(a,1);p.damage(a,2);p.damage(b,0);p.damage(b,-1);p.damage(b,Double.NaN);
        assertEquals(Set.of(a),p.finish());assertEquals(Set.of(),p.finish());
        p.damage(b,2);assertEquals(1,p.size());
    }
}
