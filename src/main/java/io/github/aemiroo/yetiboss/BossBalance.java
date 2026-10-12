package io.github.aemiroo.yetiboss;
import java.util.*;
final class BossBalance {
 record Tune(String path,double previous,double current){}
 static final List<Tune> DAMAGE_TUNES=List.of(
  new Tune("attacks.sonic-boom.damage",20,26),new Tune("attacks.charge.damage",14,19),
  new Tune("attacks.roar.damage",6,9),new Tune("attacks.grab-slam.damage",18,24),
  new Tune("attacks.ice-ball.damage",8,11),new Tune("attacks.swipe.damage",12,16),
  new Tune("attacks.slam.damage",16,22),new Tune("attacks.barrage.damage",7,10),
  new Tune("attacks.grab-slam.range",5,7.5));
 static final List<Tune> TUNES=List.of(
  new Tune("boss.health",700,1000),
  new Tune("boss.movement-speed",0.24,0.28),
  new Tune("mother.health-fraction",0.25,0.35),
  new Tune("attacks.sonic-boom.damage",12,20),
  new Tune("attacks.sonic-boom.cooldown-ticks",280,220),
  new Tune("attacks.charge.damage",10,14),
  new Tune("attacks.charge.cooldown-ticks",200,160),
  new Tune("attacks.roar.damage",4,6),
  new Tune("attacks.roar.cooldown-ticks",260,220),
  new Tune("attacks.grab-slam.damage",14,18),
  new Tune("attacks.grab-slam.cooldown-ticks",240,200),
  new Tune("attacks.global-cooldown-ticks",25,20),
  new Tune("attacks.ice-ball.damage",6,8),
  new Tune("attacks.ice-ball.cooldown-ticks",90,70),
  new Tune("attacks.ice-ball.speed",1.3,1.5),
  new Tune("attacks.swipe.damage",9,12),
  new Tune("attacks.swipe.cooldown-ticks",60,50),
  new Tune("attacks.slam.damage",12,16),
  new Tune("attacks.slam.cooldown-ticks",150,120),
  new Tune("attacks.barrage.damage",5,7),
  new Tune("attacks.barrage.cooldown-ticks",220,180),
  new Tune("attacks.barrage.count",4,5),
  new Tune("attacks.snow-golems.cooldown-ticks",320,240),
  new Tune("minions.snow-golems.maximum",4,6),
  new Tune("minions.snow-golems.per-wave",2,3),
  new Tune("minions.snow-golems.health",25,40),
  new Tune("minions.snow-golems.damage",3,4.5),
  new Tune("minions.snow-golems.barrage-count",4,5),
  new Tune("minions.snow-golems.barrage-cooldown-ticks",120,90),
  new Tune("minions.ice-warden.health",200,280),
  new Tune("minions.ice-warden.damage",12,16),
  new Tune("minions.ice-warden.movement-speed",0.18,0.22),
  new Tune("minions.ice-warden.attack-cooldown-ticks",60,45));
 static double upgrade(double current,Tune tune){return Math.abs(current-tune.previous)<1e-9?tune.current:current;}
 static int cooldown(int base,boolean enraged,double multiplier){return Math.max(1,(int)Math.ceil(base*(enraged?multiplier:1)));}
}
