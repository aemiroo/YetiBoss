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
        for(IceShot shot:shots.values()) shot.entity.remove();
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
        for(Attack a:Attack.values()) {
            String path="attacks."+a.key+".";
            for(String key:List.of("weight","cooldown-ticks","windup-ticks")) {
                int n=c.getInt(path+key);
                if(n<(key.equals("weight")?0:1)||n>12000) throw new IllegalArgumentException("Invalid "+path+key);
            }
            double damage=c.getDouble(path+"damage"),kb=c.getDouble(path+"knockback");
            if(!Double.isFinite(damage)||damage<0||damage>100||!Double.isFinite(kb)||kb<0||kb>3)
                throw new IllegalArgumentException("Invalid attack damage or knockback");
        }
        for(String key:List.of("attacks.swipe.range","attacks.slam.radius","attacks.ice-ball.speed","attacks.barrage.speed")) {
            double n=c.getDouble(key);
            if(!Double.isFinite(n)||n<=0||n>16) throw new IllegalArgumentException("Invalid "+key);
        }
        for(String key:List.of("attacks.ice-ball.slow-ticks","attacks.barrage.slow-ticks","rewards.sword.slow-ticks",
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
                &&(encounter==null||(!entity.equals(encounter.body)&&!entity.equals(encounter.model)))
                &&!shots.containsKey(entity.getUniqueId())) entity.remove();
    }
    private void spawn(Location at) {
        double health=getConfig().getDouble("boss.health");
        IronGolem body=at.getWorld().spawn(at,IronGolem.class,golem->{
            tagged(golem);golem.setPlayerCreated(true);golem.setRemoveWhenFarAway(false);
            golem.customName(net.kyori.adventure.text.Component.text(getConfig().getString("boss.name","Giant Yeti")));
            golem.setCustomNameVisible(true);
            Objects.requireNonNull(golem.getAttribute(Attribute.MAX_HEALTH)).setBaseValue(health);
            Objects.requireNonNull(golem.getAttribute(Attribute.SCALE)).setBaseValue(getConfig().getDouble("boss.golem-scale"));
            Objects.requireNonNull(golem.getAttribute(Attribute.MOVEMENT_SPEED)).setBaseValue(getConfig().getDouble("boss.movement-speed"));
            Objects.requireNonNull(golem.getAttribute(Attribute.KNOCKBACK_RESISTANCE)).setBaseValue(1);
            golem.setHealth(health);
            golem.setSilent(true);golem.setInvisible(false);
        });
        getServer().getMobGoals().removeAllGoals(body);
        ItemDisplay model=at.getWorld().spawn(at,ItemDisplay.class,display->{
            tagged(display);display.setVisibleByDefault(false);
            display.setGravity(false);display.setInvulnerable(true);
            display.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.FIXED);
            display.setBillboard(Display.Billboard.FIXED);
            float scale=(float)getConfig().getDouble("boss.model-scale");
            display.setTransformation(new Transformation(new Vector3f(),new Quaternionf(),new Vector3f(scale),new Quaternionf()));
            display.setTeleportDuration(2);display.setInterpolationDuration(2);
            display.setDisplayWidth(scale);display.setDisplayHeight(scale);display.setViewRange(2);
            display.setItemStack(modelItem("giant_yeti"));
        });
        encounter=new Encounter(body,model,at.clone(),tick);
        updateViewers(encounter);
        Bukkit.broadcastMessage(prefix()+ChatColor.RED+"The Giant Yeti has appeared!");
    }
    private ItemStack modelItem(String name) {
        ItemStack item=new ItemStack(Material.PAPER);ItemMeta meta=item.getItemMeta();
        meta.setItemModel(new NamespacedKey("yetiboss",name));item.setItemMeta(meta);return item;
    }
    private void tick() {
        tick++;
        for(Iterator<IceShot> it=shots.values().iterator();it.hasNext();) {
            IceShot shot=it.next();
            if(!shot.entity.isValid()||tick-shot.created>100||encounter==null) {
                shot.entity.remove();it.remove();
            } else if(tick%3==0) shot.entity.getWorld().spawnParticle(Particle.SNOWFLAKE,shot.entity.getLocation(),2,.05,.05,.05,0);
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
        e.bar.setProgress(Math.max(0,Math.min(1,e.body.getHealth()/getConfig().getDouble("boss.health"))));
        e.enraged=e.bar.getProgress()<=.5;
        e.bar.setColor(e.enraged?BarColor.RED:BarColor.BLUE);
        e.bar.setTitle(getConfig().getString("boss.name","Giant Yeti")+(e.enraged?" — Enraged":""));
        if(tick%10==0) {
            e.bar.removeAll();for(Player p:players)e.bar.addPlayer(p);
            updateViewers(e);
        }
        Location at=e.body.getLocation();at.setPitch(0);
        double moved=at.distance(e.last);
        if(e.pending==null&&moved>.002&&moved<2) e.walk=(e.walk+moved)%1.8;
        else if(e.pending==null) e.walk=0;
        int frame=e.pending==null&&moved>.002?(int)(e.walk/1.8*12):-1;
        int attackFrame=e.pending==null?-1:Math.max(0,Math.min(7,
                (int)((tick-e.windupStarted)*8/Math.max(1,e.releaseTick-e.windupStarted))));
        String model=e.pending!=null?"giant_yeti_attack_"+attackFrame:
                frame<0?"giant_yeti":"giant_yeti_walk_"+frame;
        if(!model.equals(e.modelName)) { e.model.setItemStack(modelItem(model));e.modelName=model; }
        e.model.teleport(at);e.last=at;
        if(e.barrageRemaining>0&&tick>=e.nextShot) {
            Player target=chooseTarget(players,e.body);
            if(target!=null) launch(target,Attack.BARRAGE);
            e.barrageRemaining--;e.nextShot=tick+getConfig().getInt("attacks.barrage.interval-ticks");
            return;
        }
        if(e.pending!=null) {
            if(tick%5==0) telegraph(e);
            if(tick>=e.releaseTick) {
                Attack attack=e.pending;e.pending=null;
                execute(e,attack,players);
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
        e.body.setTarget(null);
        if(tick%10==0) e.body.getPathfinder().moveTo(target,1);
        if(tick<e.nextAttack) return;
        double distance=e.body.getLocation().distance(target.getLocation());
        Map<Attack,Integer> weights=new EnumMap<>(Attack.class);
        for(Attack a:Attack.values()) weights.put(a,getConfig().getInt("attacks."+a.key+".weight"));
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
                    "Giant Yeti: "+attack.key.replace('-',' ')+"!",net.kyori.adventure.text.format.NamedTextColor.AQUA));
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
        for(Player player:e.body.getWorld().getPlayers()) {
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
        packStates.put(id,"REQUESTED");
        try { player.addResourcePack(BOSS_PACK_ID,url,bossPackHash,"Giant Yeti boss model",false); }
        catch(IllegalArgumentException ex) { packStates.put(id,"INVALID_URL");getLogger().warning("Invalid boss resource-pack URL"); }
    }
    @EventHandler public void bossPackStatus(PlayerResourcePackStatusEvent event) {
        if(!BOSS_PACK_ID.equals(event.getID()))return;
        UUID id=event.getPlayer().getUniqueId();
        packStates.put(id,event.getStatus().name());
        if(event.getStatus()==PlayerResourcePackStatusEvent.Status.SUCCESSFULLY_LOADED)bossPackReady.add(id);
        else bossPackReady.remove(id);
        if(encounter!=null&&!encounter.defeated)updateViewers(encounter);
    }
    @EventHandler public void leave(PlayerQuitEvent event) {
        UUID id=event.getPlayer().getUniqueId();bossPackReady.remove(id);packStates.remove(id);
    }
    private void telegraph(Encounter e) {
        Location at=e.body.getLocation();World world=at.getWorld();
        world.spawnParticle(Particle.SNOWFLAKE,at.clone().add(0,2,0),12,1,1,1,.02);
        if(e.pending==Attack.SLAM) {
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
            case ICE_BALL -> {
                // Aim is locked at wind-up start so players can dodge.
                Player p=Bukkit.getPlayer(e.target);
                if(p!=null&&eligible(p,e.origin,getConfig().getDouble("boss.arena-radius"))) launchAt(e.aim,attack);
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
                            getConfig().getDouble("attacks."+attack.key+".knockback"),0);
                }
                at.getWorld().spawnParticle(Particle.SNOWFLAKE,at.clone().add(0,.5,0),45,2,.4,2,.04);
                at.getWorld().playSound(at,Sound.ENTITY_IRON_GOLEM_ATTACK,1,.7f);
            }
        }
    }
    private void playGolemAttack(IronGolem body) {
        // The legacy API misspelled GOLEM; resolve both names across server versions.
        for(String name:List.of("IRON_GOLEM_ATTACK","IRON_GOLEN_ATTACK")) {
            try { body.playEffect(EntityEffect.valueOf(name));return; }
            catch(IllegalArgumentException ignored) {}
        }
    }
    private void launch(Player p,Attack attack) { launchAt(p.getEyeLocation(),attack); }
    private void launchAt(Location aim,Attack attack) {
        Encounter e=encounter;if(e==null) return;
        Location start=e.body.getLocation().add(0,2.7,0);
        org.bukkit.util.Vector direction=aim.toVector().subtract(start.toVector());
        if(direction.lengthSquared()<.001) return;
        direction.normalize();
        // Offset beyond the boss hitbox, preventing immediate self-collision.
        start.add(direction.clone().multiply(1.7));
        Snowball ball=start.getWorld().spawn(start,Snowball.class,s->{
            tagged(s);s.setShooter(e.body);s.setGravity(false);
            s.setItem(new ItemStack(Material.BLUE_ICE));
            s.setVelocity(direction.multiply(getConfig().getDouble("attacks."+attack.key+".speed")));
        });
        shots.put(ball.getUniqueId(),new IceShot(ball,tick,attack));
    }
    private void hit(Player player,double damage,org.bukkit.util.Vector direction,double knockback,int slow) {
        if(encounter==null) return;
        scriptedDamage=true;
        try { player.damage(damage,encounter.body); } finally { scriptedDamage=false; }
        // Knockback and slowness are applied only by the accepted damage listener.
    }
    @EventHandler(priority=EventPriority.HIGHEST,ignoreCancelled=true)
    public void damageRules(EntityDamageEvent event) {
        if(encounter!=null&&event.getEntity().equals(encounter.body)&&!(event instanceof EntityDamageByEntityEvent)) event.setCancelled(true);
        if(event instanceof EntityDamageByEntityEvent by) {
            if(by.getDamager().getPersistentDataContainer().has(entityKey,PersistentDataType.BYTE)
                    &&!scriptedDamage) event.setCancelled(true);
            if(encounter!=null&&event.getEntity().equals(encounter.body)) {
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
        if(e!=null&&event.getEntity().equals(e.body)) {
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
            String path="attacks."+shot.attack.key+".";
            hitWithEffects(p,getConfig().getDouble(path+"damage"),shot.entity.getVelocity(),
                    getConfig().getDouble(path+"knockback"),getConfig().getInt(path+"slow-ticks"));
        }
        shot.entity.remove();
    }
    private void hitWithEffects(Player p,double damage,org.bukkit.util.Vector direction,double kb,int slow) {
        // Capture the accepted event's result before applying secondary effects.
        pendingHit=new Hit(p.getUniqueId(),direction.clone(),kb,slow);
        try { hit(p,damage,direction,kb,slow); } finally { pendingHit=null; }
    }
    private Hit pendingHit;
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void knockback(EntityDamageByEntityEvent event) {
        if(!scriptedDamage||encounter==null||!event.getDamager().equals(encounter.body)
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
        if(encounter==null||!event.getEntity().equals(encounter.body)) return;
        event.getDrops().clear();event.setDroppedExp(0);encounter.defeated=true;
        encounter.recipients=encounter.participation.finish();
        encounter.model.remove();encounter.bar.removeAll();
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
            Bukkit.broadcastMessage(prefix()+ChatColor.AQUA+"The Giant Yeti was defeated! Participants earned a Baby Yeti and XP. Frostfang is on the ground!");
        }
        stop(false);
    }
    private ItemStack sword() {
        ItemStack sword=new ItemStack(Material.NETHERITE_SWORD);ItemMeta meta=sword.getItemMeta();
        meta.setDisplayName(ChatColor.translateAlternateColorCodes('&',getConfig().getString("rewards.sword.name","&bFrostfang")));
        meta.setLore(List.of(ChatColor.AQUA+"Frost Strike",ChatColor.GRAY+"Hits can briefly slow your target."));
        meta.getPersistentDataContainer().set(swordKey,PersistentDataType.BYTE,(byte)1);
        int level=getConfig().getInt("rewards.sword.damage-enchantment-level");
        if(level>0)meta.addEnchant(Enchantment.SHARPNESS,level,false);
        sword.setItemMeta(meta);return sword;
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
        if(encounter!=null&&event.getEntity().equals(encounter.body))event.setCancelled(true);
    }
    @EventHandler public void chunkLoad(ChunkLoadEvent event) {
        for(Entity entity:event.getChunk().getEntities())cleanupStale(entity);
    }
    @EventHandler public void chunkUnload(ChunkUnloadEvent event) {
        if(encounter!=null&&encounter.body.getLocation().getChunk().equals(event.getChunk()))stop(true);
    }
    private void stop(boolean announce) {
        Encounter e=encounter;encounter=null;
        if(e==null)return;
        e.body.remove();e.model.remove();e.bar.removeAll();
        for(Player player:Bukkit.getOnlinePlayers()) player.hideEntity(this,e.model);
        for(IceShot shot:shots.values())shot.entity.remove();shots.clear();
        if(announce)Bukkit.broadcastMessage(prefix()+"The Giant Yeti encounter ended without rewards.");
    }
    @Override public boolean onCommand(CommandSender sender,Command command,String label,String[] args) {
        if(!sender.hasPermission("yetiboss.admin"))return true;
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
                for(int x=-1;x<=1;x++)for(int z=-1;z<=1;z++)for(int y=0;y<5;y++)
                    if(!at.getWorld().isChunkLoaded((at.getBlockX()+x)>>4,(at.getBlockZ()+z)>>4)
                            ||!at.clone().add(x,y,z).getBlock().isPassable()) {
                        sender.sendMessage(prefix()+"Choose an open, loaded area with five blocks of headroom.");return true;
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
                    " | Participants: "+encounter.participation.size()+" | Phase: "+(encounter.enraged?"enraged":"normal")+
                    " | Model: "+(encounter.customVisible?"Giant Yeti":"visible golem fallback")));
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
        if(!sender.hasPermission("yetiboss.admin")||args.length!=1)return List.of();
        return List.of("spawn","stop","status","reload").stream().filter(s->s.startsWith(args[0].toLowerCase(Locale.ROOT))).toList();
    }
    private record IceShot(Snowball entity,long created,Attack attack) {}
    private record Hit(UUID player,org.bukkit.util.Vector direction,double knockback,int slow) {}
    private static final class Encounter {
        final UUID id=UUID.randomUUID();final IronGolem body;final ItemDisplay model;
        final Location origin;Location last,aim;org.bukkit.util.Vector direction;
        final long started;long lastPlayers,nextAttack,releaseTick,nextShot,retryReward,nextRetarget,windupStarted;
        final AttackSelector selector=new AttackSelector();final Participation participation=new Participation();
        final BossBar bar=Bukkit.createBossBar("Giant Yeti",BarColor.BLUE,BarStyle.SEGMENTED_10);
        Attack pending;UUID target,chaseTarget;boolean enraged,defeated,customVisible;int barrageRemaining;
        double walk;String modelName="giant_yeti";Set<UUID> recipients=Set.of();
        final Set<UUID> warned=new HashSet<>();
        Encounter(IronGolem body,ItemDisplay model,Location origin,long tick) {
            this.body=body;this.model=model;this.origin=origin;last=origin.clone();started=tick;lastPlayers=tick;
        }
    }
}
