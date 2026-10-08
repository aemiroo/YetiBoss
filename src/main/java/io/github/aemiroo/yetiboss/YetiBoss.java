package io.github.aemiroo.yetiboss;

import java.io.IOException;
import java.util.*;
import org.bukkit.*;
import org.bukkit.attribute.Attribute;
import org.bukkit.boss.*;
import org.bukkit.command.*;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.block.EntityBlockFormEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.event.player.PlayerResourcePackStatusEvent;
import org.bukkit.event.world.*;
import org.bukkit.inventory.*;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.potion.*;
import org.bukkit.util.*;
import org.joml.Vector3f;
import org.joml.Quaternionf;
import static io.github.aemiroo.yetiboss.AttackSelector.Attack;

public final class YetiBoss extends JavaPlugin implements Listener {
    private NamespacedKey entityKey,swordKey;
    private PetBridge pets;
    private RewardLedger ledger;
    private Encounter encounter;
    private boolean grabTeleport;
    private final Map<UUID,IceShot> shots=new HashMap<>();
    private final Map<UUID,Long> swordCooldown=new HashMap<>();
    private long tick,snowUntil;
    private final Random random=new Random();
    private boolean scriptedDamage;
    private static final UUID BOSS_PACK_ID=UUID.fromString("01fd25be-18dd-4bb4-8974-c7873cd2f902");
    private final Set<UUID> bossPackReady=new HashSet<>();
    private final Map<UUID,String> packStates=new HashMap<>();
    private byte[] bossPackHash;

    @Override public void onEnable() {
        saveDefaultConfig();
        if(!getConfig().contains("schema-version",true)) {
            if(Math.abs(getConfig().getDouble("boss.model-scale")-4.3)<.001)getConfig().set("boss.model-scale",6.4);
            if(Math.abs(getConfig().getDouble("boss.golem-scale")-1.4)<.001)getConfig().set("boss.golem-scale",2.35);
            getConfig().set("schema-version",3);saveConfig();
        }
        if(getConfig().getInt("schema-version")<4) {
            for(String key:List.of("weight","cooldown-ticks","windup-ticks","damage","knockback","radius","slow-ticks"))
                if(!getConfig().contains("attacks.roar."+key,true))getConfig().set("attacks.roar."+key,getConfig().getDefaults().get("attacks.roar."+key));
            getConfig().set("schema-version",4);saveConfig();
        }
        if(getConfig().getInt("schema-version")<5) {
            // The visible model stays giant; the navigation body must fit normal terrain.
            if(Math.abs(getConfig().getDouble("boss.golem-scale")-2.35)<.001)
                getConfig().set("boss.golem-scale",1.0);
            getConfig().set("schema-version",5);saveConfig();
        }
        if(getConfig().getInt("schema-version")<6) {
            if("Giant Yeti".equals(getConfig().getString("boss.name")))getConfig().set("boss.name","Father Yeti");
            for(String key:List.of("enabled","name","health-fraction"))
                if(!getConfig().contains("mother."+key,true))getConfig().set("mother."+key,getConfig().getDefaults().get("mother."+key));
            getConfig().set("schema-version",6);saveConfig();
        }
        if(getConfig().getInt("schema-version")<7) {
            if(!getConfig().contains("mother.size-multiplier",true))getConfig().set("mother.size-multiplier",.75);
            getConfig().set("schema-version",7);saveConfig();
        }
        if(getConfig().getInt("schema-version")<8) {
            String previous=getConfig().getString("boss.name");
            if("Father Yeti".equals(previous)||"Giant Yeti".equals(previous))
                getConfig().set("boss.name","Cyborg Father Yeti");
            getConfig().set("schema-version",8);saveConfig();
        }
        entityKey=new NamespacedKey(this,"encounter_entity");
        swordKey=new NamespacedKey(this,"frostfang");
        try {
            validate(getConfig());
            pets=new PetBridge(Objects.requireNonNull(getServer().getPluginManager().getPlugin("CosmeticPets")));
            ledger=new RewardLedger(getDataFolder().toPath().resolve("rewards.yml"));
        } catch(Exception ex) {
            getLogger().severe("Cannot enable YetiBoss: "+ex.getMessage()+". CosmeticPets 1.5.0 or newer is required.");
            getServer().getPluginManager().disablePlugin(this);return;
        }
        try(var input=getResource("yeti-pack.sha1")) {
            if(input==null)throw new IOException("Missing built boss pack hash");
            bossPackHash=HexFormat.of().parseHex(new String(input.readAllBytes(),java.nio.charset.StandardCharsets.UTF_8).trim());
        } catch(Exception ex) {
            getLogger().warning("Boss pack unavailable: "+ex.getMessage()+". The visible golem fallback will be used.");
        }
        getServer().getPluginManager().registerEvents(this,this);
        for(World world:Bukkit.getWorlds()) for(Entity entity:world.getEntities()) cleanupStale(entity);
        getServer().getScheduler().runTaskTimer(this,this::tick,1,1);
        for(Player player:Bukkit.getOnlinePlayers()) { claim(player);requestBossPack(player); }
    }
    @Override public void onDisable() {
        stop(false);
        for(IceShot shot:shots.values()) { shot.entity.remove();if(shot.visual!=null)shot.visual.remove(); }
        shots.clear();
    }
    private void validate(FileConfiguration c) {
        for(String key:List.of("boss.health","boss.golem-scale","boss.model-scale","boss.movement-speed",
                "boss.arena-radius","boss.leash-radius")) {
            double value=c.getDouble(key);
            if(!Double.isFinite(value)||value<=0) throw new IllegalArgumentException("Invalid "+key);
        }
        if(c.getDouble("boss.health")>1024 || c.getDouble("boss.golem-scale")>4
                ||c.getDouble("boss.model-scale")>12 ||c.getDouble("boss.arena-radius")>128
                ||c.getDouble("boss.leash-radius")<c.getDouble("boss.arena-radius")
                ||c.getDouble("boss.leash-radius")>160 ||c.getDouble("boss.movement-speed")>1)
            throw new IllegalArgumentException("Boss settings exceed supported bounds");
        double fraction=c.getDouble("mother.health-fraction",.25);
        if(!Double.isFinite(fraction)||fraction<=0||fraction>=1||c.getDouble("boss.health")*fraction<1)
            throw new IllegalArgumentException("Mother health must be at least 1 and below Father health");
        double motherSize=c.getDouble("mother.size-multiplier",.75);
        if(!Double.isFinite(motherSize)||motherSize<.5||motherSize>=1)
            throw new IllegalArgumentException("mother.size-multiplier must be at least 0.5 and below 1");
        validateSummons(c);
        for(Attack a:Attack.values()) {
            String path="attacks."+a.key+".";
            for(String key:List.of("weight","cooldown-ticks","windup-ticks")) {
                int n=c.getInt(path+key);
                if(n<(key.equals("weight")?0:1)||n>12000) throw new IllegalArgumentException("Invalid "+path+key);
            }
            if(a==Attack.SNOW_GOLEMS)continue;
            double damage=c.getDouble(path+"damage"),kb=c.getDouble(path+"knockback");
            if(!Double.isFinite(damage)||damage<0||damage>100||!Double.isFinite(kb)||kb<0||kb>3)
                throw new IllegalArgumentException("Invalid attack damage or knockback");
        }
        for(String key:List.of("attacks.grab-slam.range","attacks.swipe.range","attacks.slam.radius","attacks.roar.radius","attacks.ice-ball.speed","attacks.barrage.speed")) {
            double n=c.getDouble(key);
            if(!Double.isFinite(n)||n<=0||n>16) throw new IllegalArgumentException("Invalid "+key);
        }
        for(String key:List.of("attacks.ice-ball.slow-ticks","attacks.barrage.slow-ticks","attacks.roar.slow-ticks","rewards.sword.slow-ticks",
                "rewards.sword.frost-cooldown-ticks","attacks.global-cooldown-ticks","boss.idle-despawn-seconds",
                "boss.maximum-duration-seconds","snowfall.duration-seconds")) {
            if(c.getInt(key)<1||c.getInt(key)>36000) throw new IllegalArgumentException("Invalid "+key);
        }
        if(c.getInt("rewards.experience")<0||c.getInt("rewards.experience")>1000000
                ||c.getInt("attacks.barrage.count")<1||c.getInt("attacks.barrage.count")>8
                ||c.getInt("attacks.barrage.interval-ticks")<5||c.getInt("attacks.barrage.interval-ticks")>100
                ||c.getInt("snowfall.particles-per-player")<0||c.getInt("snowfall.particles-per-player")>40
                ||c.getInt("rewards.sword.damage-enchantment-level")<0||c.getInt("rewards.sword.damage-enchantment-level")>5
                ||!Double.isFinite(c.getDouble("rewards.sword.frost-chance"))
                ||c.getDouble("rewards.sword.frost-chance")<0||c.getDouble("rewards.sword.frost-chance")>1)
            throw new IllegalArgumentException("Invalid rewards, barrage or snowfall settings");
    }
    private void validateSummons(FileConfiguration c) {
        for(String key:List.of("minions.snow-golems.health","minions.ice-warden.health")) {
            double n=c.getDouble(key);
            if(!Double.isFinite(n)||n<=0||n>1024)throw new IllegalArgumentException("Invalid "+key);
        }
        for(String key:List.of("minions.snow-golems.maximum","minions.snow-golems.per-wave","minions.snow-golems.barrage-count")) {
            int n=c.getInt(key);if(n<1||n>8)throw new IllegalArgumentException("Invalid "+key);
        }
        for(String key:List.of("minions.snow-golems.barrage-cooldown-ticks","minions.snow-golems.barrage-interval-ticks",
                "minions.snow-golems.slow-ticks","minions.ice-warden.slow-ticks","minions.ice-warden.attack-cooldown-ticks")) {
            int n=c.getInt(key);if(n<5||n>1200)throw new IllegalArgumentException("Invalid "+key);
        }
        for(String key:List.of("minions.snow-golems.damage","minions.ice-warden.damage")) {
            double n=c.getDouble(key);if(!Double.isFinite(n)||n<0||n>40)throw new IllegalArgumentException("Invalid "+key);
        }
        double speed=c.getDouble("minions.ice-warden.movement-speed");
        if(!Double.isFinite(speed)||speed<=0||speed>.4)throw new IllegalArgumentException("Invalid Ice Warden speed");
    }
    private String prefix() { return ChatColor.translateAlternateColorCodes('&',getConfig().getString("prefix","&b[Yeti] &7")); }
    private boolean eligible(Player p,Location origin,double radius) {
        return p.isOnline()&&!p.isDead()&&(p.getGameMode()==GameMode.SURVIVAL||p.getGameMode()==GameMode.ADVENTURE)
            &&p.getWorld().equals(origin.getWorld())&&p.getLocation().distanceSquared(origin)<=radius*radius;
    }
    private List<Player> arenaPlayers() {
        if(encounter==null) return List.of();
        return encounter.origin.getWorld().getPlayers().stream()
            .filter(p->eligible(p,encounter.origin,getConfig().getDouble("boss.arena-radius"))).toList();
    }
    private void tagged(Entity entity) {
        entity.setPersistent(false);
        entity.getPersistentDataContainer().set(entityKey,PersistentDataType.BYTE,(byte)1);
    }
    private void cleanupStale(Entity entity) {
        if(entity.getPersistentDataContainer().has(entityKey,PersistentDataType.BYTE)
                &&(encounter==null||(!entity.equals(encounter.body)&&!entity.equals(encounter.model)&&!entity.equals(encounter.hitbox)&&!belongsTo(encounter.mother,entity)&&!encounter.minions.containsKey(entity.getUniqueId())))
                &&!shots.containsKey(entity.getUniqueId())
                &&shots.values().stream().noneMatch(shot->entity.equals(shot.visual))) entity.remove();
    }
    private void spawn(Location at) {
        encounter=createYeti(at,getConfig().getDouble("boss.health"),getConfig().getString("boss.name","Cyborg Father Yeti"),false);
        updateViewers(encounter);
        bossEffect(at,"spawn",Sound.ENTITY_ENDER_DRAGON_GROWL);
        encounter.voiceUntil=tick+103;
        Bukkit.broadcastMessage(prefix()+ChatColor.RED+"The Cyborg Father Yeti has appeared!");
    }
    private Encounter createYeti(Location at,double health,String name,boolean mother) {
        double size=mother?getConfig().getDouble("mother.size-multiplier",.75):1;
        double modelScale=getConfig().getDouble("boss.model-scale")*size;
        double bodyScale=getConfig().getDouble("boss.golem-scale")*size;
        String modelPrefix=mother?"mother_yeti":"giant_yeti";
        IronGolem body=at.getWorld().spawn(at,IronGolem.class,golem->{
            tagged(golem);golem.setPlayerCreated(true);golem.setRemoveWhenFarAway(false);
            golem.customName(net.kyori.adventure.text.Component.text(name));
            golem.setCustomNameVisible(true);
            Objects.requireNonNull(golem.getAttribute(Attribute.MAX_HEALTH)).setBaseValue(health);
            Objects.requireNonNull(golem.getAttribute(Attribute.SCALE)).setBaseValue(bodyScale);
            Objects.requireNonNull(golem.getAttribute(Attribute.MOVEMENT_SPEED)).setBaseValue(getConfig().getDouble("boss.movement-speed"));
            Objects.requireNonNull(golem.getAttribute(Attribute.KNOCKBACK_RESISTANCE)).setBaseValue(1);
            golem.setHealth(health);
            golem.setAI(true);golem.setTarget(null);
            golem.setSilent(true);golem.setInvisible(false);
        });
        getServer().getMobGoals().removeAllGoals(body);
        ItemDisplay model=at.getWorld().spawn(at,ItemDisplay.class,display->{
            tagged(display);display.setVisibleByDefault(false);
            display.setGravity(false);display.setInvulnerable(true);
            display.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.FIXED);
            display.setBillboard(Display.Billboard.FIXED);
            float scale=(float)modelScale;
            display.setTransformation(new Transformation(new Vector3f(),new Quaternionf(),new Vector3f(scale),new Quaternionf()));
            display.setTeleportDuration(2);display.setInterpolationDuration(2);
            display.setDisplayWidth(scale);display.setDisplayHeight(scale);display.setViewRange(2);
            display.setItemStack(modelItem(modelPrefix));
        });
        IronGolem hitbox=at.getWorld().spawn(at,IronGolem.class,golem->{
            tagged(golem);golem.setAI(false);golem.setGravity(false);golem.setSilent(true);
            golem.setInvisible(true);golem.setCollidable(false);golem.setPlayerCreated(true);
            golem.setRemoveWhenFarAway(false);
            Objects.requireNonNull(golem.getAttribute(Attribute.MAX_HEALTH)).setBaseValue(1024);
            golem.setHealth(1024);
            // The approved mesh is 13.1 model units high; normal golem height is 2.7 blocks.
            Objects.requireNonNull(golem.getAttribute(Attribute.SCALE)).setBaseValue(
                modelScale*13.1/16/2.7);
        });
        return new Encounter(body,model,hitbox,at.clone(),tick,name,health,modelPrefix,modelScale);
    }
    private boolean belongsTo(Encounter e,Entity entity) {
        return e!=null&&(entity.equals(e.body)||entity.equals(e.model)||entity.equals(e.hitbox));
    }
    private boolean activeYeti(Encounter e) {
        return encounter==e||(encounter!=null&&encounter.mother==e);
    }
    private void removeYeti(Encounter e) {
        if(e!=null) {e.body.remove();e.model.remove();e.hitbox.remove();e.bar.removeAll();e.grabbed=null;}
    }
    private ItemStack modelItem(String name) {
        ItemStack item=new ItemStack(Material.PAPER);ItemMeta meta=item.getItemMeta();
        meta.setItemModel(new NamespacedKey("yetiboss",name));item.setItemMeta(meta);return item;
    }
    private void tick() {
        tick++;
        for(Iterator<IceShot> it=shots.values().iterator();it.hasNext();) {
            IceShot shot=it.next();
            if(!shot.entity.isValid()||tick-shot.created>100||encounter==null||!shot.caster.isValid()||shot.caster.isDead()) {
                shot.entity.remove();if(shot.visual!=null)shot.visual.remove();it.remove();
            } else {
                if(shot.visual!=null)shot.visual.teleport(shot.entity.getLocation().clone().add(-.35,-.35,-.35));
                if(tick%3==0)shot.entity.getWorld().spawnParticle(Particle.SNOWFLAKE,shot.entity.getLocation(),2,.05,.05,.05,0);
            }
        }
        if(tick%1200==0) swordCooldown.entrySet().removeIf(e->e.getValue()<=tick);
        if(tick%200==0) for(Player p:Bukkit.getOnlinePlayers()) claim(p);
        if(tick<snowUntil&&tick%10==0) for(Player p:Bukkit.getOnlinePlayers()) {
            if(p.getGameMode()==GameMode.SPECTATOR) continue;
            p.spawnParticle(Particle.SNOWFLAKE,p.getLocation().add(0,5,0),
                getConfig().getInt("snowfall.particles-per-player"),5,3,5,.02);
        }
        Encounter e=encounter;
        if(e==null) return;
        if(e.defeated) { victory(e);return; }
        if(!e.body.isValid()||e.body.isDead()) { stop(false);return; }
        if(tick-e.started>getConfig().getInt("boss.maximum-duration-seconds")*20L) { stop(true);return; }
        List<Player> players=arenaPlayers();
        if(players.isEmpty()) {
            if(tick-e.lastPlayers>getConfig().getInt("boss.idle-despawn-seconds")*20L) { stop(true);return; }
        } else e.lastPlayers=tick;
        if(e.body.getLocation().distanceSquared(e.origin)>Math.pow(getConfig().getDouble("boss.leash-radius"),2)) {
            stop(true);return;
        }
        Encounter mother=e.mother;
        if(mother!=null) {
            if(!mother.body.isValid()||mother.body.isDead()
                    ||mother.body.getLocation().distanceSquared(e.origin)>Math.pow(getConfig().getDouble("boss.leash-radius"),2)) {
                removeYeti(mother);e.mother=null;
            } else tickYeti(mother,players,false);
        }
        tickYeti(e,players,true);
    }
    private void tickYeti(Encounter e,List<Player> players,boolean father) {
        tickGrab(e);
        e.bar.setProgress(Math.max(0,Math.min(1,e.body.getHealth()/e.maximumHealth)));
        e.enraged=e.bar.getProgress()<=.5;
        if(father) {
            tickMinions(e,players);
            if(getConfig().getBoolean("mother.enabled",true)&&e.motherTrigger.ready(e.bar.getProgress())&&tick>=e.nextMotherAttempt) {
                e.nextMotherAttempt=tick+100;
                double size=getConfig().getDouble("mother.size-multiplier",.75);
                double scale=getConfig().getDouble("boss.model-scale")*size;
                Location at=spawnPoint(e,Math.max(getConfig().getDouble("boss.golem-scale")*size*.7,scale*.4),Math.max(scale,getConfig().getDouble("boss.golem-scale")*size*2.7));
                if(at!=null) {
                    Encounter summoned=createYeti(at,e.maximumHealth*getConfig().getDouble("mother.health-fraction",.25),getConfig().getString("mother.name","Mother Yeti"),true);
                    summoned.origin.setX(e.origin.getX());summoned.origin.setY(e.origin.getY());summoned.origin.setZ(e.origin.getZ());
                    e.mother=summoned;e.motherTrigger.spawned();updateViewers(summoned);
                    bossEffect(at,"spawn",Sound.ENTITY_ENDER_DRAGON_GROWL);summoned.voiceUntil=tick+103;
                    for(Player player:players)player.sendMessage(prefix()+ChatColor.RED+"The Cyborg Father Yeti summoned the Mother Yeti!");
                }
            }
        }
        if(father&&getConfig().getBoolean("minions.ice-warden.enabled",true)&&e.wardenTrigger.ready(e.bar.getProgress())
                &&tick>=e.nextWardenAttempt) {
            e.nextWardenAttempt=tick+100;
            Location summon=spawnPoint(e,1.0,3.0);
            if(summon!=null) {
                spawnMinion(e,summon,true);e.wardenTrigger.spawned();
                for(Player player:players)player.sendMessage(prefix()+ChatColor.AQUA+"The Yeti has summoned an Ice Warden!");
            }
        }
        e.bar.setColor(e.enraged?BarColor.RED:BarColor.BLUE);
        e.bar.setTitle(e.name+(e.enraged?" — Enraged":""));
        if(tick%10==0) {
            e.bar.removeAll();for(Player p:players)e.bar.addPlayer(p);
            updateViewers(e);
        }
        if(tick>=e.nextGrowl&&tick>=e.voiceUntil&&e.pending==null&&e.recovery==null&&!players.isEmpty()) {
            bossSound(e,"angry",Sound.ENTITY_POLAR_BEAR_WARNING,3f);
            e.nextGrowl=tick+240+random.nextInt(240);
        }
        Location at=e.body.getLocation();at.setPitch(0);
        double dx=at.getX()-e.last.getX(),dz=at.getZ()-e.last.getZ();
        double moved=Math.hypot(dx,dz);
        if(e.pending==null&&moved>.002&&moved<2) {
            e.walk=(e.walk+moved)%1.8;e.lastWalkTick=tick;
        } else if(e.pending==null&&tick-e.lastWalkTick>3) {
            // Settle toward the nearest neutral pose instead of snapping to idle.
            double neutral=Math.round(e.walk/.9)*.9;
            double delta=neutral-e.walk;
            e.walk=Math.abs(delta)<.06?0:(e.walk+Math.copySign(.06,delta)+1.8)%1.8;
        }
        int walkFrames=e.modelPrefix.equals("giant_yeti")?24:12;
        int frame=e.pending==null&&(moved>.002||e.walk!=0)?Math.min(walkFrames-1,(int)(e.walk/1.8*walkFrames)):-1;
        int attackFrame=e.pending==null?-1:Math.max(0,Math.min(3,
                (int)((tick-e.windupStarted)*4/Math.max(1,e.releaseTick-e.windupStarted))));
        if(e.recovery!=null&&tick>=e.recoveryUntil)e.recovery=null;
        Attack animated=e.pending!=null?e.pending:e.recovery;
        int poseFrame=e.pending!=null?attackFrame:e.recovery==null?0:
                Math.min(7,4+(int)((tick-e.recoveryStarted)*4/Math.max(1,e.recoveryUntil-e.recoveryStarted)));
        String pose=animated==Attack.SWIPE?"swipe":animated==Attack.ICE_BALL||animated==Attack.BARRAGE?"throw":
                animated==Attack.ROAR||animated==Attack.SNOW_GOLEMS?"roar":"attack";
        String model=e.grabbed!=null?e.modelPrefix+"_attack_3":animated!=null?e.modelPrefix+"_"+pose+"_"+poseFrame:
                frame<0?e.modelPrefix:e.modelPrefix+"_walk_"+frame;
        if(!model.equals(e.modelName)) { e.model.setItemStack(modelItem(model));e.modelName=model; }
        float turn=(float)Math.IEEEremainder(at.getYaw()-e.visualYaw,360);
        e.visualYaw+=Math.max(-12f,Math.min(12f,turn));
        Location visual=at.clone();visual.setYaw(e.visualYaw);
        e.model.teleport(visual);e.hitbox.teleport(at);e.last=at;
        if(e.barrageRemaining>0&&tick>=e.nextShot) {
            Player target=chooseTarget(players,e.body);
            if(target!=null) launchAt(e,target.getEyeLocation(),Attack.BARRAGE);
            e.barrageRemaining--;e.nextShot=tick+getConfig().getInt("attacks.barrage.interval-ticks");
            return;
        }
        if(e.grabbed!=null||e.recovery!=null)return;
        if(e.pending!=null) {
            if(tick%5==0) telegraph(e);
            if(tick>=e.releaseTick) {
                Attack attack=e.pending;e.pending=null;
                execute(e,attack,players);
                e.recovery=attack;e.recoveryStarted=tick;e.recoveryUntil=tick+12;
                e.nextAttack=tick+getConfig().getInt("attacks.global-cooldown-ticks");
            }
            return;
        }
        Player target=e.chaseTarget==null?null:Bukkit.getPlayer(e.chaseTarget);
        if(target==null||!players.contains(target)||tick>=e.nextRetarget) {
            target=chooseTarget(players,e.body);
            e.chaseTarget=target==null?null:target.getUniqueId();e.nextRetarget=tick+60;
        }
        if(target==null) { e.body.getPathfinder().stopPathfinding();return; }
        if(tick%5==0) e.body.getPathfinder().moveTo(target,1);
        if(tick<e.nextAttack) return;
        double distance=e.body.getLocation().distance(target.getLocation());
        Map<Attack,Integer> weights=new EnumMap<>(Attack.class);
        for(Attack a:Attack.values()) weights.put(a,getConfig().getInt("attacks."+a.key+".weight"));
        if(!father||!getConfig().getBoolean("minions.snow-golems.enabled",true)
                ||snowGolemCount(e)>=getConfig().getInt("minions.snow-golems.maximum"))
            weights.put(Attack.SNOW_GOLEMS,0);
        Encounter other=father?e.mother:encounter;
        if(other!=null&&other.grabbed!=null)weights.put(Attack.GRAB_SLAM,0);
        if(distance>getConfig().getDouble("attacks.grab-slam.range"))weights.put(Attack.GRAB_SLAM,0);
        Player attackTarget=target;
        e.selector.choose(tick,e.enraged,distance,getConfig().getDouble("attacks.swipe.range"),
            getConfig().getDouble("attacks.slam.radius"),weights,random).ifPresent(attack->{
                e.pending=attack;e.windupStarted=tick;e.target=attackTarget.getUniqueId();
                e.aim=attackTarget.getEyeLocation().clone();
                e.direction=attackTarget.getLocation().toVector().subtract(e.body.getLocation().toVector()).setY(0);
                if(e.direction.lengthSquared()>0) e.direction.normalize();
                e.releaseTick=tick+getConfig().getInt("attacks."+attack.key+".windup-ticks");
                e.selector.used(attack,tick,getConfig().getInt("attacks."+attack.key+".cooldown-ticks"));
                e.body.getPathfinder().stopPathfinding();
                e.body.setVelocity(new org.bukkit.util.Vector(0,e.body.getVelocity().getY(),0));
                for(Player p:players)p.sendActionBar(net.kyori.adventure.text.Component.text(
                    e.name+": "+attack.key.replace('-',' ')+"!",net.kyori.adventure.text.format.NamedTextColor.AQUA));
                bossSound(e,"angry",Sound.ENTITY_POLAR_BEAR_WARNING,3f);
                telegraph(e);
            });
    }
    private Player chooseTarget(List<Player> players,IronGolem body) {
        // Usually chase the nearest player; sometimes pressure another participant.
        if(players.isEmpty()) return null;
        if(random.nextInt(4)==0) return players.get(random.nextInt(players.size()));
        return players.stream().min(Comparator.comparingDouble(p->p.getLocation().distanceSquared(body.getLocation()))).orElse(null);
    }
    private void updateViewers(Encounter e) {
        List<Player> viewers=e.body.getWorld().getPlayers().stream()
            .filter(p->p.getLocation().distanceSquared(e.body.getLocation())<96*96).toList();
        boolean custom=BossVisibility.custom(viewers.size(),(int)viewers.stream()
            .filter(p->bossPackReady.contains(p.getUniqueId())).count(),e.model.isValid());
        // Keep the living entity tracked for client-side melee selection.
        // Mixed pack readiness uses a visible fallback for everyone.
        e.body.setInvisible(custom);
        e.customVisible=custom;
        Objects.requireNonNull(e.hitbox.getAttribute(Attribute.SCALE)).setBaseValue(custom?
            e.modelScale*13.1/16/2.7:.01);
        for(Player player:e.body.getWorld().getPlayers()) {
            if(custom&&viewers.contains(player))player.showEntity(this,e.hitbox);
            else player.hideEntity(this,e.hitbox);
            boolean visible=custom&&viewers.contains(player);
            if(visible)player.showEntity(this,e.model);
            else player.hideEntity(this,e.model);
            if(viewers.contains(player)&&!bossPackReady.contains(player.getUniqueId())
                    &&e.warned.add(player.getUniqueId()))
                player.sendMessage(prefix()+"Using the visible golem fallback while the YetiBoss pack is unavailable. "+
                    "Pack status: "+packStates.getOrDefault(player.getUniqueId(),"not requested")+".");
        }
    }
    private void requestBossPack(Player player) {
        UUID id=player.getUniqueId();bossPackReady.remove(id);
        if(BedrockPlayers.contains(id)) {
            boolean installed=getConfig().getBoolean("bedrock.enabled",false)&&BedrockPlayers.displayBridgeEnabled();
            if(installed)bossPackReady.add(id);
            packStates.put(id,installed?"BEDROCK_CONFIGURED":"BEDROCK_PACKS_NOT_ENABLED");
            return;
        }
        String url=getConfig().getString("resource-pack.url",
            "https://github.com/aemiroo/YetiBoss/releases/download/yeti-pack/YetiBoss-Pack.zip");
        if(bossPackHash==null||url==null||url.isBlank()) { packStates.put(id,"DISABLED");return; }
        // Match the pack to this JAR, including draft builds; the legacy URL
        // otherwise serves a different ZIP after a model update.
        if(url.equals("https://github.com/aemiroo/YetiBoss/releases/download/yeti-pack/YetiBoss-Pack.zip"))
            url="https://github.com/aemiroo/YetiBoss/releases/download/yeti-pack-assets/YetiBoss-Pack-"
                +HexFormat.of().formatHex(bossPackHash)+".zip";
        packStates.put(id,"REQUESTED");
        try { player.addResourcePack(BOSS_PACK_ID,url,bossPackHash,"Cyborg Father Yeti boss model",false); }
        catch(IllegalArgumentException ex) { packStates.put(id,"INVALID_URL");getLogger().warning("Invalid boss resource-pack URL"); }
    }
    @EventHandler public void bossPackStatus(PlayerResourcePackStatusEvent event) {
        if(!BOSS_PACK_ID.equals(event.getID()))return;
        UUID id=event.getPlayer().getUniqueId();
        packStates.put(id,event.getStatus().name());
        if(event.getStatus()==PlayerResourcePackStatusEvent.Status.SUCCESSFULLY_LOADED)bossPackReady.add(id);
        else bossPackReady.remove(id);
        if(encounter!=null&&!encounter.defeated) {updateViewers(encounter);if(encounter.mother!=null)updateViewers(encounter.mother);}
    }
    @EventHandler public void leave(PlayerQuitEvent event) {
        UUID id=event.getPlayer().getUniqueId();bossPackReady.remove(id);packStates.remove(id);
    }
    private void bossSound(Encounter e,String sound,Sound fallback,float volume) {
        Location at=e.body.getLocation();
        if(tick<e.voiceUntil)return;
        e.voiceUntil=tick+80;
        float pitch=sound.equals("idle")?.65f:.9f;
        // Built-in sound works independently of resource-pack acceptance and custom mappings.
        for(Player player:Bukkit.getOnlinePlayers()) {
            if(!player.getWorld().equals(at.getWorld())||player.getLocation().distanceSquared(at)>48*48)continue;
            player.playSound(at,Sound.ENTITY_ENDER_DRAGON_GROWL,SoundCategory.HOSTILE,volume,pitch);
        }
    }
    private void bossEffect(Location at,String name,Sound fallback) {
        for(Player player:Bukkit.getOnlinePlayers()) {
            if(!player.getWorld().equals(at.getWorld())||player.getLocation().distanceSquared(at)>48*48)continue;
            if(BedrockPlayers.contains(player.getUniqueId()))
                player.playSound(at,"yetiboss."+name,SoundCategory.HOSTILE,3f,1f);
            else if(bossPackReady.contains(player.getUniqueId()))
                player.playSound(at,"yetiboss:"+name,SoundCategory.HOSTILE,3f,1f);
            else player.playSound(at,fallback,SoundCategory.HOSTILE,3f,1f);
        }
    }
    private void telegraph(Encounter e) {
        Location at=e.body.getLocation();World world=at.getWorld();
        world.spawnParticle(Particle.SNOWFLAKE,at.clone().add(0,2,0),12,1,1,1,.02);
        if(e.pending==Attack.SLAM||e.pending==Attack.ROAR) {
            double r=getConfig().getDouble("attacks.slam.radius");
            for(int i=0;i<32;i++) {
                double a=2*Math.PI*i/32;
                world.spawnParticle(Particle.SNOWFLAKE,at.clone().add(Math.cos(a)*r,.15,Math.sin(a)*r),1,0,0,0,0);
            }
        }
        world.playSound(at,Sound.BLOCK_SNOW_BREAK,.6f,.6f);
    }
    private void execute(Encounter e,Attack attack,List<Player> players) {
        Location at=e.body.getLocation();
        switch(attack) {
            case ROAR -> {
                double radius=getConfig().getDouble("attacks.roar.radius");
                for(Player player:players) {
                    org.bukkit.util.Vector delta=player.getLocation().toVector().subtract(at.toVector());
                    if(delta.lengthSquared()<=radius*radius&&e.body.hasLineOfSight(player))
                        hitWithEffects(player,getConfig().getDouble("attacks.roar.damage"),delta,
                            getConfig().getDouble("attacks.roar.knockback"),getConfig().getInt("attacks.roar.slow-ticks"),e.body);
                }
                at.getWorld().spawnParticle(Particle.SNOWFLAKE,at.clone().add(0,2,0),80,radius/2,1,radius/2,.08);
            }
            case GRAB_SLAM -> {
                Encounter other=e==encounter?encounter.mother:encounter;
                if(other!=null&&other.grabbed!=null)return;
                Player victim=Bukkit.getPlayer(e.target);
                if(victim==null||!players.contains(victim)||victim.isInsideVehicle()
                        ||victim.getLocation().distanceSquared(at)>Math.pow(getConfig().getDouble("attacks.grab-slam.range"),2)
                        ||!e.body.hasLineOfSight(victim))return;
                Location landing=victim.getLocation().clone();
                // Only grab over solid ground with clear space for a player-sized lift.
                if(landing.clone().add(0,-.1,0).getBlock().isPassable()||!room(landing,.35,4.5))return;
                e.grabbed=victim.getUniqueId();e.grabLanding=landing;e.grabStarted=tick;
                e.body.getPathfinder().stopPathfinding();
                victim.sendActionBar(net.kyori.adventure.text.Component.text("The Yeti grabbed you!"));
            }
            case SNOW_GOLEMS -> {
                int count=Math.min(getConfig().getInt("minions.snow-golems.per-wave"),
                    getConfig().getInt("minions.snow-golems.maximum")-snowGolemCount(e));
                for(int i=0;i<count;i++) {
                    Location point=spawnPoint(e,.5,2.0);
                    if(point!=null)spawnMinion(e,point,false);
                }
            }
            case ICE_BALL -> {
                // Aim is locked at wind-up start so players can dodge.
                Player p=Bukkit.getPlayer(e.target);
                if(p!=null&&eligible(p,e.origin,getConfig().getDouble("boss.arena-radius"))) launchAt(e,e.aim,attack);
            }
            case BARRAGE -> {
                e.barrageRemaining=getConfig().getInt("attacks.barrage.count");e.nextShot=tick;
            }
            case SWIPE, SLAM -> {
                playGolemAttack(e.body);
                double range=getConfig().getDouble("attacks."+attack.key+(attack==Attack.SLAM?".radius":".range"));
                for(Player p:players) {
                    org.bukkit.util.Vector delta=p.getLocation().toVector().subtract(at.toVector());
                    if(delta.lengthSquared()>range*range||!e.body.hasLineOfSight(p)) continue;
                    org.bukkit.util.Vector horizontal=delta.clone().setY(0);
                    if(attack==Attack.SWIPE&&horizontal.lengthSquared()>0
                            &&horizontal.normalize().dot(e.direction)<.2) continue;
                    hitWithEffects(p,getConfig().getDouble("attacks."+attack.key+".damage"),delta,
                            getConfig().getDouble("attacks."+attack.key+".knockback"),0,e.body);
                }
                at.getWorld().spawnParticle(Particle.SNOWFLAKE,at.clone().add(0,.5,0),45,2,.4,2,.04);
                at.getWorld().playSound(at,Sound.ENTITY_IRON_GOLEM_ATTACK,1,.7f);
            }
        }
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void releaseGrab(org.bukkit.event.player.PlayerTeleportEvent event) {
        if(!grabTeleport&&encounter!=null) {
            UUID id=event.getPlayer().getUniqueId();
            if(id.equals(encounter.grabbed))encounter.grabbed=null;
            if(encounter.mother!=null&&id.equals(encounter.mother.grabbed))encounter.mother.grabbed=null;
        }
    }
    private void tickGrab(Encounter e) {
        if(e.grabbed==null)return;
        Player p=Bukkit.getPlayer(e.grabbed);
        if(p==null||!eligible(p,e.origin,getConfig().getDouble("boss.arena-radius"))
                ||!p.getWorld().equals(e.grabLanding.getWorld())
                ||p.getLocation().distanceSquared(e.grabLanding)>36||p.isInsideVehicle()) {
            e.grabbed=null;return;
        }
        long age=tick-e.grabStarted;
        double lift=age<10?age*.22:age<20?2.2:Math.max(0,2.2-(age-20)*.44);
        Location held=e.grabLanding.clone().add(0,lift,0);
        held.setYaw(p.getLocation().getYaw());held.setPitch(p.getLocation().getPitch());
        if(!room(held,.35,1.9)) {e.grabbed=null;return;}
        // Respect teleport cancellation; never mount players or alter gravity/game mode.
        boolean teleported;
        grabTeleport=true;
        try {teleported=p.teleport(held,org.bukkit.event.player.PlayerTeleportEvent.TeleportCause.PLUGIN);}
        finally {grabTeleport=false;}
        if(!teleported||!activeYeti(e)||e.grabbed==null) {e.grabbed=null;return;}
        p.setVelocity(new org.bukkit.util.Vector());p.setFallDistance(0);
        if(age>=25) {
            e.grabbed=null;
            hitWithEffects(p,getConfig().getDouble("attacks.grab-slam.damage"),
                    p.getLocation().toVector().subtract(e.body.getLocation().toVector()),
                    getConfig().getDouble("attacks.grab-slam.knockback"),40,e.body);
            held.getWorld().spawnParticle(Particle.SNOWFLAKE,held,55,1.2,.25,1.2,.08);
            bossEffect(held,"grab_slam",Sound.ENTITY_IRON_GOLEM_ATTACK);
        }
    }
    private void playGolemAttack(IronGolem body) {
        // The legacy API misspelled GOLEM; resolve both names across server versions.
        for(String name:List.of("IRON_GOLEM_ATTACK","IRON_GOLEN_ATTACK")) {
            try { body.playEffect(EntityEffect.valueOf(name));return; }
            catch(IllegalArgumentException ignored) {}
        }
    }
    private void launchAt(Encounter e,Location aim,Attack attack) {
        String path="attacks."+attack.key+".";
        launchFrom(e.body,aim,attack,getConfig().getDouble(path+"damage"),getConfig().getDouble(path+"speed"),
                getConfig().getDouble(path+"knockback"),getConfig().getInt(path+"slow-ticks"));
    }
    private void launchFrom(LivingEntity caster,Location aim,Attack attack,double damage,double speed,double kb,int slow) {
        if(encounter==null||!caster.isValid()||caster.isDead())return;
        Location start=caster.getEyeLocation();
        org.bukkit.util.Vector direction=aim.toVector().subtract(start.toVector());
        if(direction.lengthSquared()<.001)return;
        direction.normalize();
        Encounter source=caster.equals(encounter.body)?encounter:encounter.mother;
        double launchWidth=source!=null&&caster.equals(source.body)&&source.customVisible?
                source.hitbox.getBoundingBox().getWidthX():caster.getBoundingBox().getWidthX();
        start.add(direction.clone().multiply(Math.max(.8,launchWidth/2+.3)));
        // Do not spawn a projectile through a wall.
        if(!start.getWorld().isChunkLoaded(start.getBlockX()>>4,start.getBlockZ()>>4)||!start.getBlock().isPassable())return;
        Snowball ball=start.getWorld().spawn(start,Snowball.class,s->{
            tagged(s);s.setShooter(caster);s.setGravity(false);
            s.setItem(new ItemStack(Material.BLUE_ICE));s.setVelocity(direction.multiply(speed));
        });
        BlockDisplay visual=null;
        if(attack==Attack.ICE_BALL) {
            visual=start.getWorld().spawn(start.clone().add(-.35,-.35,-.35),BlockDisplay.class,d->{
                tagged(d);d.setBlock(Material.BLUE_ICE.createBlockData());d.setPersistent(false);
                d.setTeleportDuration(1);
                d.setTransformation(new Transformation(new Vector3f(),new Quaternionf(),new Vector3f(.7f),new Quaternionf()));
            });
        }
        shots.put(ball.getUniqueId(),new IceShot(ball,visual,tick,attack,caster,damage,kb,slow));
    }
    private void hit(Player player,double damage,LivingEntity source) {
        if(encounter==null)return;
        scriptedDamage=true;
        try { player.damage(damage,source); } finally { scriptedDamage=false; }
    }
    private boolean allied(Entity entity) {
        return encounter!=null&&(entity.equals(encounter.body)||entity.equals(encounter.hitbox)||belongsTo(encounter.mother,entity)||encounter.minions.containsKey(entity.getUniqueId()));
    }
    private int snowGolemCount(Encounter e) {
        return (int)e.minions.values().stream().filter(m->!m.warden&&m.mob.isValid()&&!m.mob.isDead()).count();
    }
    private boolean room(Location at,double halfWidth,double height) {
        World world=at.getWorld();
        if(at.getY()<world.getMinHeight()||at.getY()+height>=world.getMaxHeight())return false;
        for(int x=(int)Math.floor(at.getX()-halfWidth);x<=(int)Math.floor(at.getX()+halfWidth);x++)
            for(int z=(int)Math.floor(at.getZ()-halfWidth);z<=(int)Math.floor(at.getZ()+halfWidth);z++) {
                if(!world.isChunkLoaded(x>>4,z>>4))return false;
                for(int y=at.getBlockY();y<Math.ceil(at.getY()+height);y++)
                    if(!world.getBlockAt(x,y,z).isPassable())return false;
            }
        return true;
    }
    private Location spawnPoint(Encounter e,double halfWidth,double height) {
        for(int attempt=0;attempt<24;attempt++) {
            double angle=random.nextDouble()*Math.PI*2,distance=5+random.nextDouble()*4;
            Location at=e.body.getLocation().add(Math.cos(angle)*distance,0,Math.sin(angle)*distance);
            if(!at.getWorld().isChunkLoaded(at.getBlockX()>>4,at.getBlockZ()>>4)
                    ||at.distanceSquared(e.origin)>Math.pow(getConfig().getDouble("boss.arena-radius"),2)
                    ||!at.getWorld().getWorldBorder().isInside(at))continue;
            for(int dy:new int[]{0,1,-1,2,-2}) {
                Location test=at.clone().add(0,dy,0);test.setY(test.getBlockY());
                if(room(test,halfWidth,height)&&test.getY()>test.getWorld().getMinHeight()
                        &&!test.clone().add(0,-1,0).getBlock().isPassable()
                        &&test.getWorld().getNearbyEntities(test,halfWidth*2,height,halfWidth*2).stream()
                            .noneMatch(entity->entity instanceof LivingEntity))return test;
            }
        }
        return null;
    }
    private void spawnMinion(Encounter e,Location at,boolean warden) {
        Mob mob=warden?at.getWorld().spawn(at,Warden.class):at.getWorld().spawn(at,Snowman.class);
        tagged(mob);mob.setAI(true);getServer().getMobGoals().removeAllGoals(mob);mob.setRemoveWhenFarAway(false);mob.setSilent(true);
        mob.setCustomNameVisible(true);
        mob.customName(net.kyori.adventure.text.Component.text(warden?"Ice Warden":"Evil Snow Golem",
                warden?net.kyori.adventure.text.format.NamedTextColor.AQUA:net.kyori.adventure.text.format.NamedTextColor.RED));
        double health=getConfig().getDouble(warden?"minions.ice-warden.health":"minions.snow-golems.health");
        Objects.requireNonNull(mob.getAttribute(Attribute.MAX_HEALTH)).setBaseValue(health);mob.setHealth(health);
        Objects.requireNonNull(mob.getAttribute(Attribute.MOVEMENT_SPEED)).setBaseValue(
                warden?getConfig().getDouble("minions.ice-warden.movement-speed"):.22);
        if(mob instanceof Snowman snowman)snowman.setDerp(true);
        e.minions.put(mob.getUniqueId(),new IceMinion(mob,warden,tick+30));
        at.getWorld().spawnParticle(Particle.SNOWFLAKE,at.clone().add(0,1,0),25,.5,1,.5,.03);
    }
    private void tickMinions(Encounter e,List<Player> players) {
        for(IceMinion minion:new ArrayList<>(e.minions.values())) {
            Mob mob=minion.mob;
            if(!mob.isValid()||mob.isDead()) {e.minions.remove(mob.getUniqueId());continue;}
            if(mob.getLocation().distanceSquared(e.origin)>Math.pow(getConfig().getDouble("boss.leash-radius"),2)) {
                mob.remove();e.minions.remove(mob.getUniqueId());continue;
            }
            if(tick%10==0)mob.getWorld().spawnParticle(Particle.SNOWFLAKE,mob.getLocation().add(0,1,0),3,.4,.8,.4,0);
            Player target=players.stream().filter(mob::hasLineOfSight)
                .min(Comparator.comparingDouble(p->p.getLocation().distanceSquared(mob.getLocation()))).orElse(null);
            if(target==null) {mob.getPathfinder().stopPathfinding();continue;}
            org.bukkit.util.Vector delta=target.getLocation().toVector().subtract(mob.getLocation().toVector());
            if(delta.clone().setY(0).lengthSquared()>.001)mob.setRotation(
                    (float)Math.toDegrees(Math.atan2(-delta.getX(),delta.getZ())),0);
            if(minion.warden) {
                // Warden movement/attacks use its native brain, not a second scripted hit.
                if(tick%20==0) {
                    ((Warden)mob).setAnger(target,150);
                    ((Warden)mob).setDisturbanceLocation(target.getLocation());
                    mob.setTarget(target);
                }
                if(delta.lengthSquared()>9&&tick%10==0)mob.getPathfinder().moveTo(target,1);
            } else {
                if(delta.lengthSquared()>36) {
                    if(tick%10==0)mob.getPathfinder().moveTo(target,1);
                } else mob.getPathfinder().stopPathfinding();
                if(minion.remaining==0&&tick>=minion.nextAttack) {
                    minion.remaining=getConfig().getInt("minions.snow-golems.barrage-count");
                    minion.nextShot=tick;
                    minion.nextAttack=tick+getConfig().getInt("minions.snow-golems.barrage-cooldown-ticks");
                }
                if(minion.remaining>0&&tick>=minion.nextShot) {
                    launchFrom(mob,target.getEyeLocation(),Attack.BARRAGE,
                        getConfig().getDouble("minions.snow-golems.damage"),getConfig().getDouble("attacks.barrage.speed"),.4,
                        getConfig().getInt("minions.snow-golems.slow-ticks"));
                    minion.remaining--;minion.nextShot=tick+getConfig().getInt("minions.snow-golems.barrage-interval-ticks");
                }
            }
        }
    }
    @EventHandler(priority=EventPriority.HIGHEST,ignoreCancelled=true)
    public void snowTrail(EntityBlockFormEvent event) {
        if(allied(event.getEntity()))event.setCancelled(true);
    }
    @EventHandler(priority=EventPriority.HIGHEST)
    public void hitboxDamage(EntityDamageEvent event) {
        Encounter root=encounter;
        if(root==null)return;
        Encounter e=event.getEntity().equals(root.hitbox)?root:root.mother;
        if(e==null||!event.getEntity().equals(e.hitbox))return;
        boolean allowed=!event.isCancelled();event.setCancelled(true);
        if(!allowed||!e.customVisible||!(event instanceof EntityDamageByEntityEvent by))return;
        Player player=attacker(by.getDamager());
        if(player==null||!eligible(player,e.origin,getConfig().getDouble("boss.arena-radius")))return;
        double damage=event.getDamage();
        // Re-enter normal damage events on the encounter body, retaining the original source.
        Bukkit.getScheduler().runTask(this,()->{
            if(activeYeti(e)&&!e.defeated&&e.body.isValid()&&player.isOnline())
                e.body.damage(damage,by.getDamager());
        });
    }
    @EventHandler(priority=EventPriority.HIGHEST,ignoreCancelled=true)
    public void damageRules(EntityDamageEvent event) {
        if(encounter!=null&&allied(event.getEntity())&&!(event instanceof EntityDamageByEntityEvent)) event.setCancelled(true);
        if(event instanceof EntityDamageByEntityEvent by) {
            if(by.getDamager().getPersistentDataContainer().has(entityKey,PersistentDataType.BYTE)
                    &&!scriptedDamage) {
                IceMinion minion=encounter==null?null:encounter.minions.get(by.getDamager().getUniqueId());
                if(minion!=null&&minion.warden) {
                    boolean playerEligible=by.getEntity() instanceof Player player
                        &&eligible(player,encounter.origin,getConfig().getDouble("boss.arena-radius"));
                    if(!WardenStrikeGate.allowed(event.getCause()==EntityDamageEvent.DamageCause.ENTITY_ATTACK,
                            playerEligible,tick,minion.nextAttack))event.setCancelled(true);
                    else by.setDamage(getConfig().getDouble("minions.ice-warden.damage"));
                } else event.setCancelled(true);
            }
            if(allied(event.getEntity())) {
                Player p=attacker(by.getDamager());
                if(p==null||!eligible(p,encounter.origin,getConfig().getDouble("boss.arena-radius"))) event.setCancelled(true);
            }
        }
    }
    private Player attacker(Entity entity) {
        if(entity instanceof Player p) return p;
        if(entity instanceof Projectile projectile&&projectile.getShooter() instanceof Player p) return p;
        return null;
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void acceptedDamage(EntityDamageByEntityEvent event) {
        if(event.getFinalDamage()<=0) return;
        Encounter e=encounter;
        IceMinion striking=e==null?null:e.minions.get(event.getDamager().getUniqueId());
        if(striking!=null&&striking.warden&&!scriptedDamage&&event.getEntity() instanceof Player player) {
            striking.nextAttack=tick+getConfig().getInt("minions.ice-warden.attack-cooldown-ticks");
            int duration=getConfig().getInt("minions.ice-warden.slow-ticks");
            Bukkit.getScheduler().runTask(this,()->{
                if(player.isOnline()&&!player.isDead())
                    player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS,duration,0));
            });
        }
        Encounter hurt=e==null?null:event.getEntity().equals(e.body)?e:
            e.mother!=null&&event.getEntity().equals(e.mother.body)?e.mother:null;
        if(hurt!=null&&!hurt.defeated&&event.getFinalDamage()<hurt.body.getHealth()&&tick>=hurt.nextHurtSound) {
            boolean first=random.nextBoolean();
            hurt.nextHurtSound=tick+(first?10:30);
            bossEffect(hurt.body.getLocation(),first?"hurt_1":"hurt_2",Sound.ENTITY_IRON_GOLEM_HURT);
        }
        if(e!=null&&allied(event.getEntity())) {
            Player p=attacker(event.getDamager());if(p!=null)e.participation.damage(p.getUniqueId(),event.getFinalDamage());
        }
        if(event.getDamager() instanceof Player p&&event.getEntity() instanceof LivingEntity victim) {
            ItemStack item=p.getInventory().getItemInMainHand();ItemMeta meta=item.getItemMeta();
            if(meta!=null&&meta.getPersistentDataContainer().has(swordKey,PersistentDataType.BYTE)
                    &&tick>=swordCooldown.getOrDefault(p.getUniqueId(),0L)
                    &&random.nextDouble()<getConfig().getDouble("rewards.sword.frost-chance")) {
                swordCooldown.put(p.getUniqueId(),tick+getConfig().getInt("rewards.sword.frost-cooldown-ticks"));
                // MONITOR does not alter the event. Apply the effect next tick.
                Bukkit.getScheduler().runTask(this,()->{
                    if(victim.isValid()&&!victim.isDead()) {
                        victim.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS,getConfig().getInt("rewards.sword.slow-ticks"),1));
                        victim.getWorld().spawnParticle(Particle.SNOWFLAKE,victim.getLocation().add(0,1,0),8,.3,.5,.3,0);
                    }
                });
            }
        }
    }
    @EventHandler public void projectileHit(ProjectileHitEvent event) {
        IceShot shot=shots.remove(event.getEntity().getUniqueId());if(shot==null) return;
        Location at=shot.entity.getLocation();
        at.getWorld().spawnParticle(Particle.SNOWFLAKE,at,18,.25,.25,.25,.04);
        at.getWorld().playSound(at,Sound.BLOCK_GLASS_BREAK,.7f,1.5f);
        if(event.getHitEntity() instanceof Player p&&encounter!=null
                &&eligible(p,encounter.origin,getConfig().getDouble("boss.arena-radius"))) {
            hitWithEffects(p,shot.damage,shot.entity.getVelocity(),shot.knockback,shot.slow,shot.caster);
        }
        shot.entity.remove();if(shot.visual!=null)shot.visual.remove();
    }
    private void hitWithEffects(Player p,double damage,org.bukkit.util.Vector direction,double kb,int slow) {
        if(encounter!=null)hitWithEffects(p,damage,direction,kb,slow,encounter.body);
    }
    private void hitWithEffects(Player p,double damage,org.bukkit.util.Vector direction,double kb,int slow,LivingEntity source) {
        // Capture the accepted event's result before applying secondary effects.
        pendingHit=new Hit(p.getUniqueId(),direction.clone(),kb,slow);
        try { hit(p,damage,source); } finally { pendingHit=null; }
    }
    private Hit pendingHit;
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void knockback(EntityDamageByEntityEvent event) {
        if(!scriptedDamage||encounter==null||!allied(event.getDamager())
                ||!(event.getEntity() instanceof Player p)||event.getFinalDamage()<=0) return;
        Hit h=pendingHit;
        if(h==null||!h.player.equals(p.getUniqueId())) return;
        org.bukkit.util.Vector vector=h.direction.clone().setY(0);
        if(vector.lengthSquared()>.001) vector.normalize().multiply(h.knockback);
        vector.setY(Math.min(.45,h.knockback*.4));
        Bukkit.getScheduler().runTask(this,()->{
            if(!p.isOnline()||p.isDead()) return;
            p.setVelocity(vector);
            if(h.slow>0)p.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS,h.slow,0));
        });
    }
    @EventHandler public void death(EntityDeathEvent event) {
        if(encounter==null)return;
        if(encounter.mother!=null&&event.getEntity().equals(encounter.mother.body)) {
            event.getDrops().clear();event.setDroppedExp(0);
            bossEffect(event.getEntity().getLocation(),"death",Sound.ENTITY_ENDER_DRAGON_DEATH);
            removeYeti(encounter.mother);encounter.mother=null;return;
        }
        if(encounter.minions.remove(event.getEntity().getUniqueId())!=null) {
            event.getDrops().clear();event.setDroppedExp(0);return;
        }
        if(!event.getEntity().equals(encounter.body))return;
        event.getDrops().clear();event.setDroppedExp(0);encounter.defeated=true;
        bossEffect(event.getEntity().getLocation(),"death",Sound.ENTITY_ENDER_DRAGON_DEATH);
        encounter.recipients=encounter.participation.finish();
        encounter.model.remove();encounter.hitbox.remove();encounter.bar.removeAll();
        removeYeti(encounter.mother);encounter.mother=null;
        victory(encounter);
    }
    private void victory(Encounter e) {
        if(tick<e.retryReward) return;
        try { ledger.queue(e.id,e.recipients,getConfig().getInt("rewards.experience")); }
        catch(IOException ex) {
            e.retryReward=tick+200;getLogger().severe("Reward save failed; encounter rewards will retry: "+ex.getMessage());return;
        }
        if(!e.recipients.isEmpty()) {
            ItemStack sword=sword();
            e.origin.getWorld().dropItemNaturally(e.last,sword);
            for(UUID id:e.recipients) {
                try { pets.unlock(id); } catch(ReflectiveOperationException ex) { getLogger().warning("Yeti unlock queued for "+id); }
                Player p=Bukkit.getPlayer(id);if(p!=null)claim(p);
            }
            if(getConfig().getBoolean("snowfall.enabled"))snowUntil=tick+getConfig().getInt("snowfall.duration-seconds")*20L;
            Bukkit.broadcastMessage(prefix()+ChatColor.AQUA+"The Cyborg Father Yeti was defeated! Participants earned a Baby Yeti and XP. Frostfang is on the ground!");
        }
        stop(false);
    }
    private ItemStack sword() {
        ItemStack sword=new ItemStack(Material.NETHERITE_SWORD);ItemMeta meta=sword.getItemMeta();
        meta.setItemModel(new NamespacedKey("yetiboss","frostfang"));
        meta.setDisplayName(ChatColor.translateAlternateColorCodes('&',getConfig().getString("rewards.sword.name","&bFrostfang")));
        meta.setLore(List.of(ChatColor.AQUA+"Frost Strike",ChatColor.GRAY+"Hits can briefly slow your target."));
        meta.getPersistentDataContainer().set(swordKey,PersistentDataType.BYTE,(byte)1);
        int level=getConfig().getInt("rewards.sword.damage-enchantment-level");
        if(level>0)meta.addEnchant(Enchantment.SHARPNESS,level,false);
        sword.setItemMeta(meta);return sword;
    }
    private ItemStack frostGear(String kind) {
        if(kind.equals("frostfang"))return sword();
        ItemStack item=new ItemStack(kind.equals("frostbow")?Material.BOW:Material.NETHERITE_PICKAXE);
        ItemMeta meta=item.getItemMeta();
        meta.setItemModel(new NamespacedKey("yetiboss",kind));
        meta.setDisplayName(ChatColor.AQUA+(kind.equals("frostbow")?"Frost Bow":"Glacier Pickaxe"));
        item.setItemMeta(meta);return item;
    }
    private void claim(Player player) {
        UUID id=player.getUniqueId();if(!ledger.hasYeti(id))return;
        try {
            pets.unlock(id);
            int xp=ledger.xp(id);
            // Consume before applying XP: a crash cannot replay the same claim.
            ledger.consume(id);
            player.giveExp(xp);
            player.sendMessage(prefix()+"You earned "+xp+" XP and unlocked Baby Yeti! Use /pets yeti.");
        } catch(Exception ex) { getLogger().warning("Reward remains queued for "+id+": "+ex.getMessage()); }
    }
    @EventHandler public void join(PlayerJoinEvent event) {
        Bukkit.getScheduler().runTaskLater(this,()->{if(event.getPlayer().isOnline()) {claim(event.getPlayer());requestBossPack(event.getPlayer());}},40);
    }
    @EventHandler public void target(EntityTargetLivingEntityEvent event) {
        if(!allied(event.getEntity()))return;
        IceMinion minion=encounter.minions.get(event.getEntity().getUniqueId());
        if(minion!=null&&minion.warden&&event.getTarget() instanceof Player player
                &&eligible(player,encounter.origin,getConfig().getDouble("boss.arena-radius")))return;
        event.setCancelled(true);
    }
    @EventHandler public void chunkLoad(ChunkLoadEvent event) {
        for(Entity entity:event.getChunk().getEntities())cleanupStale(entity);
    }
    @EventHandler public void chunkUnload(ChunkUnloadEvent event) {
        if(encounter!=null&&encounter.body.getLocation().getChunk().equals(event.getChunk())) {stop(true);return;}
        if(encounter!=null&&encounter.mother!=null&&encounter.mother.body.getLocation().getChunk().equals(event.getChunk())) {
            removeYeti(encounter.mother);encounter.mother=null;
        }
        if(encounter!=null)for(IceMinion minion:new ArrayList<>(encounter.minions.values()))
            if(minion.mob.getLocation().getChunk().equals(event.getChunk())) {
                minion.mob.remove();encounter.minions.remove(minion.mob.getUniqueId());
            }
    }
    private void stop(boolean announce) {
        Encounter e=encounter;encounter=null;
        if(e==null)return;
        removeYeti(e);removeYeti(e.mother);
        for(IceMinion minion:e.minions.values())minion.mob.remove();
        e.minions.clear();
        for(Player player:Bukkit.getOnlinePlayers()) player.hideEntity(this,e.model);
        for(IceShot shot:shots.values()) { shot.entity.remove();if(shot.visual!=null)shot.visual.remove(); }shots.clear();
        if(announce)Bukkit.broadcastMessage(prefix()+"The Cyborg Father Yeti encounter ended without rewards.");
    }
    @Override public boolean onCommand(CommandSender sender,Command command,String label,String[] args) {
        if(!sender.hasPermission("yetiboss.admin"))return true;
        if(args.length==2&&args[0].equalsIgnoreCase("give")) {
            String kind=args[1].toLowerCase(Locale.ROOT);
            if(!(sender instanceof Player player)) {sender.sendMessage("Use this command in-game.");return true;}
            if(!List.of("frostfang","frostbow","frostpickaxe").contains(kind))return false;
            for(ItemStack leftover:player.getInventory().addItem(frostGear(kind)).values())
                player.getWorld().dropItemNaturally(player.getLocation(),leftover);
            requestBossPack(player);return true;
        }
        if(args.length!=1)return false;
        switch(args[0].toLowerCase(Locale.ROOT)) {
            case "spawn" -> {
                if(encounter!=null) { sender.sendMessage(prefix()+"An encounter is already active.");return true; }
                if(!(sender instanceof Player p)) { sender.sendMessage("Spawn in-game.");return true; }
                org.bukkit.util.Vector forward=p.getLocation().getDirection().setY(0);
                if(forward.lengthSquared()<.001)forward=new org.bukkit.util.Vector(0,0,1);
                Location at=p.getLocation().add(forward.normalize().multiply(6));at.setPitch(0);
                if(!at.getWorld().isChunkLoaded(at.getBlockX()>>4,at.getBlockZ()>>4)) {
                    sender.sendMessage(prefix()+"Choose a loaded area.");return true;
                }
                int floor=at.getBlockY();
                while(floor>at.getWorld().getMinHeight()&&floor>at.getBlockY()-8
                        &&at.getWorld().getBlockAt(at.getBlockX(),floor-1,at.getBlockZ()).isPassable())floor--;
                at.setY(floor);
                double halfWidth=getConfig().getDouble("boss.golem-scale")*.7;
                double height=Math.max(getConfig().getDouble("boss.golem-scale")*2.7,getConfig().getDouble("boss.model-scale"));
                if(!room(at,halfWidth,height)) {
                    sender.sendMessage(prefix()+"Choose open, loaded ground with "+Math.ceil(height)+" blocks of headroom.");return true;
                }
                if(at.clone().add(0,-1,0).getBlock().isPassable()||!at.getWorld().getWorldBorder().isInside(at)) {
                    sender.sendMessage(prefix()+"The Yeti needs solid ground inside the world border.");return true;
                }
                spawn(at);
            }
            case "stop" -> {
                if(encounter!=null&&encounter.defeated){sender.sendMessage(prefix()+"Rewards are pending; fix the save error first.");return true;}
                stop(true);sender.sendMessage(prefix()+"Encounter stopped.");
            }
            case "status" -> {
                sender.sendMessage(prefix()+(encounter==null?"No active Yeti.":"Health: "+Math.ceil(encounter.body.getHealth())+
                    " | Mother: "+(encounter.mother==null?"absent":Math.ceil(encounter.mother.body.getHealth())+" HP")+" | Summons: "+encounter.minions.size()+" | Participants: "+encounter.participation.size()+" | Phase: "+(encounter.enraged?"enraged":"normal")+
                    " | Model: "+(encounter.customVisible?"Cyborg Father Yeti":"visible golem fallback")));
                if(sender instanceof Player player)sender.sendMessage(prefix()+"Your boss pack: "+
                    packStates.getOrDefault(player.getUniqueId(),"not requested"));
            }
            case "reload" -> {
                if(encounter!=null){sender.sendMessage(prefix()+"Stop the encounter before reloading.");return true;}
                FileConfiguration old=getConfig();reloadConfig();
                try { validate(getConfig());for(Player player:Bukkit.getOnlinePlayers())requestBossPack(player);sender.sendMessage(prefix()+"Configuration reloaded; boss pack requested again."); }
                catch(IllegalArgumentException ex) {
                    getConfig().getKeys(false).forEach(key->getConfig().set(key,null));
                    old.getValues(false).forEach((key,value)->getConfig().set(key,value));
                    sender.sendMessage(prefix()+"Reload rejected: "+ex.getMessage());
                }
            }
            default -> {return false;}
        }
        return true;
    }
    @Override public List<String> onTabComplete(CommandSender sender,Command command,String alias,String[] args) {
        if(!sender.hasPermission("yetiboss.admin"))return List.of();
        if(args.length==2&&args[0].equalsIgnoreCase("give"))
            return List.of("frostfang","frostbow","frostpickaxe").stream().filter(s->s.startsWith(args[1].toLowerCase(Locale.ROOT))).toList();
        if(args.length!=1)return List.of();
        return List.of("spawn","stop","status","reload","give").stream().filter(s->s.startsWith(args[0].toLowerCase(Locale.ROOT))).toList();
    }
    private record IceShot(Snowball entity,BlockDisplay visual,long created,Attack attack,LivingEntity caster,double damage,double knockback,int slow) {}
    private record Hit(UUID player,org.bukkit.util.Vector direction,double knockback,int slow) {}
    private static final class IceMinion {
        final Mob mob;final boolean warden;long nextAttack,nextShot;int remaining;
        IceMinion(Mob mob,boolean warden,long nextAttack) {this.mob=mob;this.warden=warden;this.nextAttack=nextAttack;}
    }
    private static final class Encounter {
        final UUID id=UUID.randomUUID();final IronGolem body,hitbox;final ItemDisplay model;
        float visualYaw;long lastWalkTick;
        final Location origin;Location last,aim;org.bukkit.util.Vector direction;
        final long started;long lastPlayers,nextAttack,releaseTick,nextShot,retryReward,nextRetarget,windupStarted;
        final ThresholdSummon wardenTrigger=new ThresholdSummon(),motherTrigger=new ThresholdSummon(.5);
        Encounter mother;long nextMotherAttempt;final String name,modelPrefix;final double maximumHealth,modelScale;
        final Map<UUID,IceMinion> minions=new HashMap<>();
        long nextWardenAttempt,grabStarted;UUID grabbed;Location grabLanding;
        final AttackSelector selector=new AttackSelector();final Participation participation=new Participation();
        final BossBar bar=Bukkit.createBossBar("Cyborg Father Yeti",BarColor.BLUE,BarStyle.SEGMENTED_10);
        Attack pending,recovery;long recoveryStarted,recoveryUntil,nextGrowl,voiceUntil,nextHurtSound;UUID target,chaseTarget;boolean enraged,defeated,customVisible;int barrageRemaining;
        double walk;String modelName="giant_yeti";Set<UUID> recipients=Set.of();
        final Set<UUID> warned=new HashSet<>();
        Encounter(IronGolem body,ItemDisplay model,IronGolem hitbox,Location origin,long tick,String name,double maximumHealth,String modelPrefix,double modelScale) {
            this.modelPrefix=modelPrefix;this.modelName=modelPrefix;this.modelScale=modelScale;this.name=name;this.maximumHealth=maximumHealth;this.body=body;this.model=model;this.hitbox=hitbox;this.origin=origin;last=origin.clone();visualYaw=origin.getYaw();lastWalkTick=tick;started=tick;lastPlayers=tick;
        }
    }
}
