package io.github.aemiroo.yetiboss;
import java.util.*;
import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.enchantment.EnchantItemEvent;
import org.bukkit.event.entity.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.*;
import org.bukkit.inventory.*;
import org.bukkit.inventory.meta.*;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.potion.*;
/** Server-owned item identities, independent loot rolls and guarded frost abilities. */
final class FrostItems implements Listener {
    private final YetiBoss plugin;
    private final NamespacedKey kindKey,levelKey,legacySword;
    private final Random random=new Random();
    private final Map<String,Long> cooldowns=new HashMap<>();
    private final Map<String,Stack> stacks=new HashMap<>();
    private final Map<UUID,Shot> shots=new HashMap<>();
    private final Map<UUID,BlockFace> faces=new HashMap<>();
    private boolean extraDamage,mining;
    private long tick;
    private record Stack(int count,long expires){}
    private record Shot(UUID owner,int level,boolean bomb,long expires){}
    FrostItems(YetiBoss plugin) {
        this.plugin=plugin;kindKey=new NamespacedKey(plugin,"frost_item");levelKey=new NamespacedKey(plugin,"frostbite");legacySword=new NamespacedKey(plugin,"frostfang");
        Bukkit.getPluginManager().registerEvents(this,plugin);
        Bukkit.getScheduler().runTaskTimer(plugin,()->{tick++;if(tick%200==0){cooldowns.values().removeIf(t->t<=tick);stacks.values().removeIf(s->s.expires<=tick);shots.values().removeIf(s->s.expires<=tick);}},1,1);
    }
    private double number(String path,double fallback){return plugin.getConfig().getDouble("items."+path,fallback);}
    private int integer(String path,int fallback){return plugin.getConfig().getInt("items."+path,fallback);}
    String kind(ItemStack item) {
        if(item==null||!item.hasItemMeta())return "";
        var p=item.getItemMeta().getPersistentDataContainer();String kind=p.get(kindKey,PersistentDataType.STRING);
        if(kind!=null)return kind;
        return p.has(legacySword,PersistentDataType.BYTE)?"frostfang":"";
    }
    private int level(ItemStack item){return item==null||!item.hasItemMeta()?0:item.getItemMeta().getPersistentDataContainer().getOrDefault(levelKey,PersistentDataType.INTEGER,0);}
    private boolean valid(ItemStack item) {
        String k=kind(item);if(!FrostRules.SPECIAL.contains(k))return false;
        Material expected=switch(k){case "frostfang"->Material.NETHERITE_SWORD;case "frostbow"->Material.BOW;default->Material.NETHERITE_PICKAXE;};
        Set<String> enchants=new HashSet<>();item.getEnchantments().keySet().forEach(e->enchants.add(e.getKey().getKey()));
        return item.getType()==expected&&level(item)>=0&&level(item)<=3&&FrostRules.compatible(k,enchants);
    }
    private void describe(ItemMeta meta,String k,int level) {
        List<String> lore=new ArrayList<>();
        lore.add(ChatColor.AQUA+switch(k){case "frostfang"->"Every fifth hit unleashes a frost burst.";case "frostbow"->"Fully charged arrows explode with frost.";case "frostpickaxe"->"Sneak-mine for a 3×3 mining burst.";case "frostbomb"->"Right-click to throw. Consumed on use.";default->"Apply to special frost gear in an anvil.";});
        if(level>0)lore.add(ChatColor.BLUE+"Frostbite "+List.of("","I","II","III").get(level));
        meta.setLore(lore);
    }
    ItemStack create(String k) {
        Material material=switch(k){case "frostfang"->Material.NETHERITE_SWORD;case "frostbow"->Material.BOW;case "frostpickaxe"->Material.NETHERITE_PICKAXE;case "frostbomb"->Material.SNOWBALL;case "frostbite_book"->Material.ENCHANTED_BOOK;default->throw new IllegalArgumentException(k);};
        ItemStack item=new ItemStack(material);ItemMeta meta=item.getItemMeta();meta.getPersistentDataContainer().set(kindKey,PersistentDataType.STRING,k);
        meta.setDisplayName(ChatColor.AQUA+switch(k){case "frostfang"->"Frostfang";case "frostbow"->"Frost Bow";case "frostpickaxe"->"Glacier Pickaxe";case "frostbomb"->"Frost Bomb";default->"Frostbite Enchantment Book";});
        if(!k.equals("frostbite_book"))meta.setItemModel(new NamespacedKey("yetiboss",k));
        if(k.equals("frostbite_book"))meta.getPersistentDataContainer().set(levelKey,PersistentDataType.INTEGER,1);
        if(k.equals("frostfang")){meta.getPersistentDataContainer().set(legacySword,PersistentDataType.BYTE,(byte)1);meta.addEnchant(Enchantment.SHARPNESS,5,true);}
        describe(meta,k,k.equals("frostbite_book")?1:0);item.setItemMeta(meta);return item;
    }
    void loot(Location at) {
        var section=plugin.getConfig().getConfigurationSection("loot");if(section==null)return;
        for(String key:section.getKeys(false)) {
            double chance=section.getDouble(key+".chance");if(random.nextDouble()>=chance)continue;
            int count=FrostRules.amount(random,section.getInt(key+".min"),section.getInt(key+".max"));
            ItemStack item=Set.of("frostfang","frostbow","frostpickaxe","frostbomb","frostbite_book").contains(key)?create(key):new ItemStack(Material.valueOf(key.toUpperCase(Locale.ROOT)));
            while(count>0){ItemStack drop=item.clone();int amount=Math.min(count,drop.getMaxStackSize());drop.setAmount(amount);at.getWorld().dropItemNaturally(at,drop);count-=amount;}
        }
    }
    private boolean ready(Player p,String ability,int duration) {
        String key=p.getUniqueId()+":"+ability;if(cooldowns.getOrDefault(key,0L)>tick)return false;
        cooldowns.put(key,tick+duration);return true;
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void swordHit(EntityDamageByEntityEvent event) {
        if(extraDamage||!(event.getDamager() instanceof Player p)||!(event.getEntity() instanceof LivingEntity victim)||event.getFinalDamage()<=0)return;
        ItemStack sword=p.getInventory().getItemInMainHand();if(!kind(sword).equals("frostfang")||!valid(sword)||p.getAttackCooldown()<.9)return;
        String key=p.getUniqueId()+":"+victim.getUniqueId();Stack old=stacks.get(key);int count=old==null||old.expires<=tick?1:old.count+1;
        if(count<integer("sword.stacks",5)){stacks.put(key,new Stack(count,tick+integer("sword.stack-expiry-ticks",100)));return;}
        stacks.remove(key);if(!ready(p,"sword",integer("sword.cooldown-ticks",80)))return;
        int level=level(sword);
        Bukkit.getScheduler().runTask(plugin,()->{
            if(!p.isOnline()||!victim.isValid()||victim.isDead())return;
            burst(victim.getLocation(),p,null,0,number("sword.bonus-damage",4)+level,integer("sword.slow-ticks",40)+level*10,victim);
        });
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void bowShot(EntityShootBowEvent event) {
        if(!(event.getEntity() instanceof Player p)||!kind(event.getBow()).equals("frostbow")||!valid(event.getBow())||event.getForce()<.95||!(event.getProjectile() instanceof AbstractArrow arrow))return;
        if(ready(p,"bow",integer("bow.cooldown-ticks",60)))shots.put(arrow.getUniqueId(),new Shot(p.getUniqueId(),level(event.getBow()),false,tick+1200));
    }
    @EventHandler(priority=EventPriority.HIGHEST,ignoreCancelled=true)
    public void throwBomb(PlayerInteractEvent event) {
        if(event.getHand()==null||!event.getAction().isRightClick()||!kind(event.getItem()).equals("frostbomb"))return;
        event.setCancelled(true);Player p=event.getPlayer();if(!ready(p,"bomb",integer("bomb.cooldown-ticks",60)))return;
        Snowball ball=p.launchProjectile(Snowball.class,p.getEyeLocation().getDirection().multiply(1.4));ball.setItem(create("frostbomb"));
        shots.put(ball.getUniqueId(),new Shot(p.getUniqueId(),0,true,tick+200));
        if(p.getGameMode()!=GameMode.CREATIVE)event.getItem().setAmount(event.getItem().getAmount()-1);
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void impact(ProjectileHitEvent event) {
        Shot shot=shots.remove(event.getEntity().getUniqueId());if(shot==null)return;
        Player owner=Bukkit.getPlayer(shot.owner);if(owner==null||!owner.isOnline())return;
        Location at=event.getEntity().getLocation().clone();Projectile source=event.getEntity();
        Bukkit.getScheduler().runTask(plugin,()->{
            String type=shot.bomb?"bomb":"bow";
            burst(at,owner,source,number(type+".radius",3),number(type+".damage",shot.bomb?5:4),integer(type+".slow-ticks",60)+shot.level*20,null);
            if(shot.bomb&&source.isValid())source.remove();
        });
    }
    private void burst(Location at,Player owner,Projectile source,double radius,double damage,int slow,LivingEntity direct) {
        at.getWorld().spawnParticle(Particle.SNOWFLAKE,at.clone().add(0,.5,0),30,.7,.7,.7,.03);
        at.getWorld().playSound(at,Sound.BLOCK_GLASS_BREAK,1,.7f);
        Collection<LivingEntity> targets=direct==null?at.getWorld().getNearbyLivingEntities(at,radius):List.of(direct);
        for(LivingEntity target:targets) {
            if(target.equals(owner)||target instanceof ArmorStand||target.isDead()||!owner.hasLineOfSight(target))continue;
            if(target instanceof Player p&&(!at.getWorld().getPVP()||p.getGameMode()==GameMode.CREATIVE||p.getGameMode()==GameMode.SPECTATOR))continue;
            double before=target.getHealth()+target.getAbsorptionAmount();
            int invulnerability=target.getNoDamageTicks();
            if(direct!=null)target.setNoDamageTicks(0);
            extraDamage=true;try{target.damage(damage,source==null?owner:source);}finally{extraDamage=false;if(direct!=null)target.setNoDamageTicks(Math.max(invulnerability,target.getNoDamageTicks()));}
            // Protection plugins can cancel damage; only successful damage applies the slow.
            if(target.getHealth()+target.getAbsorptionAmount()<before)target.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS,slow,direct==null?1:3));
        }
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void face(PlayerInteractEvent event) {
        if(event.getClickedBlock()!=null&&event.getAction()==org.bukkit.event.block.Action.LEFT_CLICK_BLOCK)faces.put(event.getPlayer().getUniqueId(),event.getBlockFace());
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true)
    public void mine(BlockBreakEvent event) {
        Player p=event.getPlayer();ItemStack tool=p.getInventory().getItemInMainHand();
        if(mining||!p.isSneaking()||p.getGameMode()!=GameMode.SURVIVAL||!kind(tool).equals("frostpickaxe")||!valid(tool))return;
        Block center=event.getBlock();if(!mineable(center,tool))return;
        int heldSlot=p.getInventory().getHeldItemSlot();
        if(!ready(p,"pickaxe",Math.max(20,integer("pickaxe.cooldown-ticks",200)-level(tool)*integer("pickaxe.level-reduction-ticks",20))))return;
        BlockFace face=faces.getOrDefault(p.getUniqueId(),BlockFace.UP);List<Block> blocks=new ArrayList<>();
        for(int a=-1;a<=1;a++)for(int b=-1;b<=1;b++)if(a!=0||b!=0)blocks.add(center.getRelative(face.getModX()!=0?0:a,face.getModY()!=0?0:face.getModX()!=0?a:b,face.getModZ()!=0?0:b));
        Bukkit.getScheduler().runTask(plugin,()->{
            if(!p.isOnline()||!p.isSneaking()||p.getInventory().getHeldItemSlot()!=heldSlot||!valid(p.getInventory().getItemInMainHand()))return;
            mining=true;try{
                for(Block block:blocks) {
                    ItemStack held=p.getInventory().getItemInMainHand();if(!valid(held)||!kind(held).equals("frostpickaxe"))break;
                    if(!block.getWorld().isChunkLoaded(block.getX()>>4,block.getZ()>>4)||p.getLocation().distanceSquared(block.getLocation())>64||!mineable(block,held))continue;
                    if(p.breakBlock(block))wear(p,integer("pickaxe.extra-durability",1));
                }
            } finally{mining=false;}
        });
    }
    private boolean mineable(Block block,ItemStack tool) {
        return block.getType().isSolid()&&block.getType().getHardness()>=0&&!(block.getState() instanceof org.bukkit.block.TileState)
            &&block.isPreferredTool(tool)&&block.getWorld().getWorldBorder().isInside(block.getLocation());
    }
    private void wear(Player p,int amount) {
        if(amount<=0)return;ItemStack tool=p.getInventory().getItemInMainHand();if(!(tool.getItemMeta() instanceof Damageable meta))return;
        PlayerItemDamageEvent event=new PlayerItemDamageEvent(p,tool,amount);Bukkit.getPluginManager().callEvent(event);if(event.isCancelled())return;
        int damage=meta.getDamage()+event.getDamage();
        if(damage>=tool.getType().getMaxDurability()){p.getInventory().setItemInMainHand(new ItemStack(Material.AIR));p.playSound(p.getLocation(),Sound.ENTITY_ITEM_BREAK,1,1);}
        else {meta.setDamage(damage);tool.setItemMeta(meta);}
    }
    @EventHandler public void anvil(PrepareAnvilEvent event) {
        AnvilInventory inventory=event.getInventory();ItemStack left=inventory.getItem(0),right=inventory.getItem(1);
        String k=kind(left);boolean book=k.equals("frostbite_book");
        if(right!=null&&FrostRules.SPECIAL.contains(kind(right))&&!k.equals(kind(right))){event.setResult(null);return;}
        if(right!=null&&kind(right).equals("frostbite_book")) {
            if(!(FrostRules.SPECIAL.contains(k)||book)||level(right)<1||level(right)>3){event.setResult(null);return;}
            if(!book&&!valid(left)){event.setResult(null);return;}
            ItemStack result=left.clone();result.setAmount(1);ItemMeta meta=result.getItemMeta();int level=FrostRules.combine(level(left),level(right));
            meta.getPersistentDataContainer().set(levelKey,PersistentDataType.INTEGER,level);describe(meta,k,level);
            String rename=inventory.getRenameText();if(rename!=null&&!rename.isBlank())meta.setDisplayName(rename);
            result.setItemMeta(meta);event.setResult(result);inventory.setRepairCost(5+level*2);inventory.setRepairCostAmount(1);return;
        }
        if(book&&right!=null){event.setResult(null);return;}
        if(FrostRules.SPECIAL.contains(k)&&right!=null) {
            if(!kind(right).isEmpty()&&!kind(right).equals(k)){event.setResult(null);return;}
            ItemStack result=event.getResult();if(result==null)return;
            Set<String> enchants=new HashSet<>();result.getEnchantments().keySet().forEach(e->enchants.add(e.getKey().getKey()));
            if(right.getItemMeta() instanceof EnchantmentStorageMeta stored)stored.getStoredEnchants().keySet().forEach(e->enchants.add(e.getKey().getKey()));
            if(!FrostRules.compatible(k,enchants)){event.setResult(null);return;}
            ItemMeta meta=result.getItemMeta();meta.getPersistentDataContainer().set(kindKey,PersistentDataType.STRING,k);
            int level=kind(right).equals(k)?FrostRules.combine(level(left),level(right)):level(left);
            if(level(left)==0&&level(right)==0)level=0;
            meta.getPersistentDataContainer().set(levelKey,PersistentDataType.INTEGER,level);describe(meta,k,level);result.setItemMeta(meta);event.setResult(result);
        }
    }
    @EventHandler(priority=EventPriority.HIGHEST,ignoreCancelled=true)
    public void enchant(EnchantItemEvent event) {
        String k=kind(event.getItem());if(!FrostRules.SPECIAL.contains(k))return;
        if(event.getEnchantsToAdd().keySet().stream().anyMatch(e->!FrostRules.allowed(k,e.getKey().getKey())))event.setCancelled(true);
    }
    @EventHandler(priority=EventPriority.HIGHEST,ignoreCancelled=true)
    public void takeResult(InventoryClickEvent event) {
        if(event.getRawSlot()!=2||event.getView().getTopInventory().getType()!=InventoryType.ANVIL)return;
        ItemStack result=event.getCurrentItem();if(FrostRules.SPECIAL.contains(kind(result))&&!valid(result))event.setCancelled(true);
    }
    @EventHandler public void quit(PlayerQuitEvent event){faces.remove(event.getPlayer().getUniqueId());}
    static void validate(org.bukkit.configuration.file.FileConfiguration config) {
        var loot=config.getConfigurationSection("loot");if(loot==null)throw new IllegalArgumentException("Missing loot table");
        for(String key:loot.getKeys(false)) {
            double chance=loot.getDouble(key+".chance");int min=loot.getInt(key+".min"),max=loot.getInt(key+".max");
            if(!Double.isFinite(chance)||chance<0||chance>1||min<1||max<min||max>64)throw new IllegalArgumentException("Invalid loot entry: "+key);
            if(!Set.of("frostfang","frostbow","frostpickaxe","frostbomb","frostbite_book").contains(key))Material.valueOf(key.toUpperCase(Locale.ROOT));
        }
        for(String path:List.of("sword.stacks","sword.stack-expiry-ticks","sword.cooldown-ticks","sword.slow-ticks","bow.cooldown-ticks","bow.slow-ticks","bomb.cooldown-ticks","bomb.slow-ticks","pickaxe.cooldown-ticks","pickaxe.level-reduction-ticks","pickaxe.extra-durability")) {
            int n=config.getInt("items."+path);if(n<1||n>1200)throw new IllegalArgumentException("Invalid item setting: "+path);
        }
        for(String path:List.of("sword.bonus-damage","bow.radius","bow.damage","bomb.radius","bomb.damage")) {
            double n=config.getDouble("items."+path);if(!Double.isFinite(n)||n<=0||n>16)throw new IllegalArgumentException("Invalid item setting: "+path);
        }
    }
}
