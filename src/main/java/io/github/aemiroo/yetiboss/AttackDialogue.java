package io.github.aemiroo.yetiboss;
import static io.github.aemiroo.yetiboss.AttackSelector.Attack;
final class AttackDialogue {
    private AttackDialogue() {}
    static String warning(Attack attack,boolean father) {
        return switch(attack) {
            case SWIPE -> father?"Heavy combo — two swipes, then a frost slam!":"Claw swipe — dodge the reach!";
            case SLAM -> father?"Frost shockwave — jump or retreat!":"Ground slam — get clear!";
            case GRAB_SLAM -> "Grab and throw — dodge the reaching hand!";
            case SONIC_BOOM -> "Reactor sonic boom — move out of the beam!";
            case CHARGE -> "Mechanical charge — move out of the marked lane!";
            case ICE_BALL -> "Ice ball — move away from the aimed spot!";
            case BARRAGE -> "Frost barrage — keep moving!";
            case ROAR -> "Freezing roar — back away!";
            case SNOW_GOLEMS -> "Snow reinforcements incoming!";
        };
    }
}
