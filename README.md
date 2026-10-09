# YetiBoss
A Giant Yeti encounter for LARP SMP, targeting Paper/Purpur 26.3 using the compatible 1.21.4 Bukkit API. Java 21 or newer is required; the server's Java 25 is suitable. Version 0.4.0 is an initial server-test build.

## Install
1. Install CosmeticPets **1.5.0 or newer**, its required PacketEvents dependency, and the current CosmeticPets resource packs/mappings.
2. Download the **YetiBoss** artifact from this repository's successful GitHub Actions build. Place its JAR in plugins.
3. Restart the server. Accept **both** the CosmeticPets pack (pets) and the dedicated YetiBoss pack (boss) on Java.
   The boss ZIP is automatically requested from https://github.com/aemiroo/YetiBoss/releases/download/yeti-pack/YetiBoss-Pack.zip.
   Existing configs without resource-pack.url use that default.
   Bedrock needs the existing GeyserDisplayEntity extension/pack plus YetiBoss-Bedrock.mcpack and both boss mappings.
   Keep the CosmeticPets pack/mappings installed for the reward pet. After installing the boss files, set bedrock.enabled: true in YetiBoss config and restart Geyser/server.
4. As an operator, run /yetiboss spawn in an open arena. It spawns about six blocks ahead, requiring solid ground and five blocks of headroom.

The boss has an original white-and-grey mountain Yeti model inspired by the supplied reference: heavy shoulders, long arms, individual fingers/claws, a broad head with red eyes and a deep fang-lined mouth. The default model scale is **6.4**, approximately 6.4 blocks tall, with a matching larger golem hitbox. The baby pet is unchanged. Walking arms swing together like a golem; eight attack poses remain included.

On upgrade, only the previous default model scale (4.3) and hitbox scale (1.4) migrate to 6.4 and 2.35 respectively. Custom size settings are preserved. Use an open arena with at least seven blocks of headroom.

The model is drawn over a damageable iron golem whose client-side hitbox stays tracked. **If any nearby viewer has not loaded the boss pack, everyone sees a visible golem fallback** instead of an invisible fight. Once all viewers within 96 blocks have the pack, the custom model appears. Pack failure/decline does not kick players. /yetiboss status reports the active model and the caller's boss-pack loading status. This independent pack status no longer relies on CosmeticPets reporting its pack loaded.

Bedrock readiness is an explicit server configuration assertion: the plugin can detect the display extension, but cannot verify the contents of a Bedrock client's packs. Keep bedrock.enabled false until the boss pack and mappings have been installed. Verify Java and Bedrock rendering before a public event.

## Commands
All commands require yetiboss.admin (operators by default).
- /yetiboss spawn: start one encounter.
- /yetiboss stop: abort without rewards.
- /yetiboss status: health, phase and participant count.
- /yetiboss reload: validate and reload config when no encounter is running.

Only one boss runs at a time. Restart, disable, timeout, leaving the arena empty, unloading its chunk, or leaving its leash radius aborts the fight without rewards. This build does not resume an active fight after restart. Boss entities are nonpersistent and stale tagged entities are removed when encountered.

## Combat
700 HP by default, configurable. The Yeti pursues survival/adventure players in its arena using native pathfinding. It does not break blocks or place ice/snow.

The weighted attack selector checks distance, phase and per-attack cooldowns. No attack repeats immediately; if alternatives are unavailable, it waits while pursuing a player.
- Ice ball: locks aim when the wind-up starts; dodging is possible.
- Swipe: a forward close-range arc.
- Ground slam: a visible ring followed by a nearby area hit.
- Barrage: four ice projectiles, enabled at half health.

Damage, knockback, cooldowns, weights and wind-ups are configurable. The 26.3 ice projectile is a snowball rendered as blue ice, with custom hit damage/slowness and a shatter effect. It does **not** depend on 26.4's experimental native Ice Ball. Native 26.4 integration can follow once its server API is stable.

## Rewards
Any survival/adventure player dealing positive, uncanceled direct or projectile damage to the Yeti or its summoned enemies participates. Merely standing nearby does not count. Rewards are not restricted to the killing blow or remaining online.
- Every participant receives a permanent **Baby Yeti unlock** in CosmeticPets and 3,000 **XP points**, configurable.
- **One Frostfang sword** drops on the ground at the boss's death. Normal vanilla pickup applies: first pickup gets it, regardless of participation. No personal copies are issued.
- Frostfang has one custom effect, **Frost Strike**: by default a 20% chance on accepted melee damage to apply Slowness II for three seconds, with a four-second per-player cooldown. It is an item tag/effect, not a registered vanilla enchantment. Vanilla Sharpness V is configurable.
- After victory, all online players receive a configurable five-minute snowfall particle effect across worlds. It places no snow layers and changes no weather.

Offline XP/unlocks are queued in plugins/YetiBoss/rewards.yml; online players claim immediately, offline players on join. CosmeticPets stores earned unlocks independently in yeti-unlocks.yml. Existing preview permission remains available to administrators.

Reward files use atomic replacement; repeated processing of the same encounter cannot queue duplicate XP. XP claims are consumed before applying XP to prevent replay after a crash. An abrupt crash between that save and the player's persisted XP can lose XP; this is not an atomic transaction with Minecraft player data. Keep backups and reconcile manually if this rare case occurs. The Yeti unlock is idempotent and persisted before consuming the reward.

## Validation
GitHub Actions runs attack-selection, participation and reward-persistence tests, compiles against Paper, and uploads the JAR. Live validation must cover:
- Java/Bedrock model visibility, hitbox clicks, movement around terrain.
- Dodging, armor/shield behavior, canceled damage with protection plugins.
- Two or more participants, someone disconnecting, and exactly one sword.
- XP and /pets yeti surviving restart.
- Stop/unload/restart cleanup and no block/snow-layer changes.

Existing repository GPL-3.0 license applies.

## Boss pack troubleshooting
- Use /yetiboss status. SUCCESSFULLY_LOADED is required on Java; merely ACCEPTED or DOWNLOADED is not enough.
- FAILED_DOWNLOAD: verify the repository/release are public, and that resource-pack.url serves the exact YetiBoss-Pack.zip from this build.
- DECLINED: enable server resource packs in the client's server settings and reconnect.
- SUCCESSFULLY_LOADED with fallback: another viewer within 96 blocks has not loaded the boss pack.
- Bedrock: install the dedicated boss mcpack alongside the display extension's own pack. Put the boss JSON beside the working CosmeticPets Geyser JSON, and the boss display YAML beside the working CosmeticPets display YAML. Keep each plugin's mappings as separate files. Restart before reconnecting.
- Stop the boss and run /yetiboss reload to request the pack again, or reconnect.
- The release is published only after all build checks pass. If using a custom host, update its ZIP together with the plugin JAR.

For local builds, generate both packs with the resource-pack Python scripts before running mvn verify. GitHub Actions does this automatically.


## Summoned enemies (0.3.0)
- **Evil Snow Golems** are a weighted random summon attack: two per wave, capped at four living golems by default. They approach players until within six blocks and fire four-shot ice barrages at visible survival/adventure players inside the arena. Hits apply Slowness I for three seconds by default. Barrage speed follows the Yeti barrage setting; minion damage, timing, count, health, cap and slowness are configurable.
- **Ice Warden** summons once per encounter at **35% HP or below**, after finding clear loaded ground. If the area is blocked it retries every five seconds until it can spawn. It is a native Warden themed with snow particles and slowing melee attacks, not a new custom Warden texture/model. Its movement AI is enabled; vanilla damage is blocked and plugin-controlled melee applies Slowness. It navigates toward players. Use an arena with traversable paths.
- Summons have no item/XP drops, no natural environmental death, no friendly fire, and no snow trails. Accepted player damage can kill them normally.
- All summons and their projectiles are removed on victory, stop, timeout, disable, or encounter abort. A summon entering an unloading chunk is removed. Killing the Warden does not cause it to respawn.
- Set minions.snow-golems.enabled or minions.ice-warden.enabled to false to disable the respective summon.
- Live checks should include the four-golem cap, slowing barrages, crossing 35% health in one hit, Warden movement, and cleanup after death/stop/restart.

### 0.3.1 movement and model fixes
Summons now keep AI movement enabled with vanilla goals removed. Snow golems approach players until within six blocks and fire the existing slowing ice barrage. The Ice Warden uses navigation to chase players and the plugin controls its melee damage. Vanilla summon damage remains blocked.

The Yeti has longer, distinct legs and red eyes and a recessed fang-lined mouth. Pose models use valid vanilla element rotation steps.

`attacks.grab-slam` adds a weighted close-range attack: a 35-tick warning, range/line-of-sight check, a short lift and downward slam for 14 damage by default. Players can dodge during the warning. The grab requires clear space and solid ground, respects canceled teleports, and ends on other teleports, death, leaving the arena, disconnect, or encounter cleanup. It changes no game mode, gravity, or mount state.

Live verification: test both summons navigating around obstacles, grab dodging/cancellation/disconnect, and Java/Bedrock visual poses on the target server.

The latest boss model uses the second supplied mountain-Yeti reference: white/grey fur, heavy shoulders, long arms, distinct fingers and claws, red eyes and a deep mouth. It is an original block-built interpretation, not an imported mesh from the image.

### 0.3.2 Warden damage
Ice Warden targeting now permits eligible arena participants and refreshes native anger. Its native melee event is allowed, uses the configured damage, and applies Slowness only after accepted positive damage. Sonic-boom damage, friendly fire and hits outside the arena remain blocked; shields, armor and protection plugins still affect damage. The attack cooldown starts only after an accepted hit.

The reference-based model now has broader shoulders, tapered and outward-stepped limbs, shaggy silhouette details and a taller fang-lined cavity. A single image does not contain the original mesh/textures or unseen sides: this is a closer reconstruction, not an exact imported model.

### 0.4.0 model rebuild
Replaced the voxel-cell model with a compact articulated cuboid model: a smaller head placed ahead of the torso, a fully visible mouth cavity, long angled arms, sloping shoulders, planted legs, segmented fingers, tapered fangs, and layered fur pieces. Fur uses textured surfaces, and the Bedrock atlas preserves all texture pixels. Both walk and raised-arm attack variants remain available. This is a reconstruction from the supplied image; exact original geometry, unseen sides, textures and lighting cannot be recovered from that image alone.

## 0.5.0 boss rework

The approved snow-white horned Yeti replaces the earlier gorilla model. Flat hands,
red eyes, and tapered 3D scream fangs are retained. Separate one-arm swipe/throw,
two-arm slam, and open-mouth roar poses play through a short recovery after impact.
A frost roar deals nearby damage, knockback, and Slowness after a visible windup.
Existing randomized cooldowns, minions, grab/slam, and rewards remain in place.

The supplied idle and angry growls are converted to mono Ogg and bundled in both
packs. Idle growls occur at randomized 12–24 second intervals; attack windups use
the angry growl. Java players without the boss pack hear a vanilla fallback.
Replace the Bedrock pack and BOTH mapping files because new animation IDs were added.
Restart with the new JAR; existing configs receive the new roar defaults automatically.
The attacks use snow particles without changing terrain or placing snow layers.

## 0.5.1 movement and growl fixes

Walk poses rotate arms at the shoulders and alternate leg rotations. The default
collision body is normal golem size so paths fit ordinary terrain; the visible
Yeti remains giant. Old default scale 2.35 migrates to 1.0 automatically. Chase
paths refresh every five ticks without repeatedly clearing the mob target.
Attack selection no longer resets the idle sound timer. Growls finish playing
before another starts and are audible up to 48 blocks with hostile sounds enabled.
Install the new JAR and packs together; reconnect to load the new pack hash.

## 0.5.2 vanilla growls

Idle and angry growls now use Minecraft's built-in Ender Dragon growl, with lower
pitch for idle and higher pitch for anger. Playback no longer depends on the
resource pack or custom Bedrock sound mappings. Only the JAR needs updating for
this fix. The client's Hostile Creatures volume must be enabled.

## 0.5.3 combat growls

The encounter's arena players are active combat targets, so periodic growls now
use the angry pitch throughout the fight. Idle-pitch growls no longer play during
chasing, attacks, or the enraged phase.

## 0.5.4 combat hitbox

An invisible, stationary-AI golem follows the visual model as a separate combat
hitbox. Its height scales to the 13.1-unit mesh height (5.24 blocks at scale 6.4);
the normal-size body continues pathfinding. The hitbox approximates the central
torso and head, rather than every animated arm or horn. Melee and projectile
damage relay to the original body through normal damage events and participation
tracking. The proxy cannot take environmental damage, drop items, or split rewards.
It is removed on death/stop and disabled with the vanilla model fallback.

### 0.5.5 — boss event sounds

Adds the five supplied clips: spawn once per encounter, death once, two randomly selected hurt clips, and grab-slam landing. Hurt clips have a short overlap cooldown and skip lethal hits. Combat retains the Ender Dragon growl. Custom audio requires the updated resource pack and enabled Hostile Creatures volume; Java players without the pack hear vanilla fallback sounds. Replace the Bedrock pack for Geyser clients as well.

### 0.5.6 — eye texture correction

The eyes now appear only on the front of the face. Top, back, sides and underside use a plain dark face texture in every animation pose, in both resource packs.

### 0.5.7 — overlapping surfaces

Separates coplanar overlapping surfaces at the hip/legs, feet and curled horn segments. Small geometry offsets preserve the silhouette and prevent surface flicker across all 45 poses. Includes the front-only eye fix from 0.5.6.


## Father and Mother Yeti (0.6.0)

The main boss is named Father Yeti. Once at or below 50% health he summons Mother Yeti, using the same model, walking/attack animations and randomized combat. Mother has 25% of Father's maximum HP (175 HP with the default 700 HP), her own health bar and attack cooldowns. Only Father summons snow golems and the Ice Warden; the 35% Warden trigger stays independent. Summoning retries every five seconds until safe loaded ground is available, then never repeats even if Mother dies.

Damage to either Yeti counts toward participation. Mother drops no separate rewards. Father's defeat completes the event and removes Mother and other summons; stopping, unloading or disabling cleans them up too. Set `mother.enabled`, `mother.name`, and `mother.health-fraction` in config.yml, then `/yetiboss reload` while no encounter is active. Existing default boss name migrates to Father Yeti; custom names remain. No resource-pack changes are required.


## Distinct Mother model (0.6.1)

Mother is now 25% smaller than Father by default, with a narrower silhouette, pale glacier fur, cyan eyes and outward swept ice horns. She has separate idle, walking, slam, swipe, throw and roar models in both Java and Bedrock packs. Animations never switch back to Father's model. Display size, navigation body, collision clearance and combat hitbox scale together. Health and summon thresholds remain unchanged. `mother.size-multiplier` controls size relative to Father (0.5 to below 1.0). Update the JAR and Java/Bedrock resource packs, plus both Geyser mapping files for Bedrock players, then restart and reconnect.


## Frost gear models (0.6.2)

Frostfang now uses an original jagged ice blade with a dark hilt. Frost Bow uses curved ice limbs and three Java draw stages. Glacier Pickaxe uses a broad two-sided frozen head. All have first/third person, inventory, frame and ground transforms, with Bedrock held-item geometries and mappings on their real sword/bow/pickaxe base items. Father drops the new Frostfang model automatically. Admins can inspect each with `/yetiboss give frostfang`, `/yetiboss give frostbow`, and `/yetiboss give frostpickaxe`.

This release implements appearance; Frost Bow and Glacier Pickaxe currently retain their vanilla abilities. Slowing/homing arrows, 3×3 mining, throwable boss ice and configurable additional loot are still pending. Update both packs and the Geyser item mappings, replace the plugin, then restart and reconnect.


## Gear hand pose corrections (0.6.3)

Frostfang and Glacier Pickaxe use third-person transforms aligned with their upright geometry, so their blades/heads extend upward from the hand. Their first-person transforms no longer apply the diagonal tilt intended for generated vanilla sprites. Frost Bow has separate bow holding transforms for both hands, shared by all drawing stages. Update the plugin (contains the pack hash) and resource pack, then restart and reconnect.


## Grip anchoring and frost textures (0.6.4)

The sword, pickaxe and all bow draw stages now anchor their actual grip point to the palm, instead of placing the item by its overall bounding-box center. Java first/third-person left and right poses account for Minecraft's hand mirroring. Bedrock hand-bound geometries use the same physical grip as their origin.

All three items have new darker forged metal, stitched leather wraps, pale rime edges, branching ice cracks, and restrained cyan runic inlays. Bedrock inventory icons now sample the same patterned materials rather than flat color swatches. Replace the JAR and Java/Bedrock packs, then restart and reconnect to load the new pack hash.


## Approved frost-forged gear remodel (0.7.0)

Rebuilds all three items from the approved concept sheet: Frostfang has a long dark fuller, cyan rune panels, jagged ice edges, hooked guard and faceted jewels; Glacier Pickaxe has a downward-curved two-sided head, socket jewel, decorated wrapped haft and silver collars; Frost Bow has stepped recurve limbs, crystal clusters, metallic reinforcement, a jewel-trimmed central grip, connected string and three nocked-arrow draw stages.

The models use native cuboids and legal 45-degree diamond accents, with matching textures and 64px geometry-derived Bedrock icons. First/third-person grip anchors remain shared across Java and Bedrock. All gear IDs and commands remain compatible. Update both packs and the plugin for the new pack hash, then restart and reconnect. This release remodels the visuals; the previously planned bow/mining/loot mechanics are still pending.


## 0.8.0 — Yeti combat overhaul

Cyborg Father Yeti now uses a distance-driven knuckle gait and a bounding gallop during his telegraphed charge. His melee sequence performs two swipes 14 ticks apart, then a slam 18 ticks later. Slams send an expanding, jumpable frost ring out to 12 blocks; each ring and charge hits each player at most once. At half health, reactor sparks, faster attack cadence, longer/faster charges and stronger frost rings intensify the fight.

Both Yetis now lift and throw a grabbed player instead of slamming them downward. The randomized 5–15 block distance is estimated for level ground; walls, elevation, water and player movement affect actual travel. Existing grab cancellation and cleanup rules remain. Mother Yeti retains her exact model, textures and animation assets.

The idle bow carry pose has been retuned from the in-game screenshot. Actions run titles include version 0.8.0 and the commit description. Schema 9 adds charge settings and updates only the previous default global cooldown. Validate bow carrying/shooting in both hands, terrain collision during charge, throw distances and fight balance on the actual server before using this draft for an event.

### Ice Warden appearance (0.8.7)
The summoned Ice Warden uses an original ice-armored sentinel model with crystal horns, a luminous chest core, and a 24-frame distance-driven walk. Its native Warden combat is retained. Mixed resource-pack readiness uses the vanilla Warden fallback. Father and Mother assets are unchanged.

### Sculpted Yeti silhouettes (0.8.8)
Father and Mother now have faceted shoulders, heads, hands and limbs, tapered torsos, and layered fur edges. Existing palettes, connected horns, Father machinery and all animation rigs are retained. Ice Warden assets and combat are unchanged.

### Cyborg body repair (0.8.9)
Closed the Father torso seam, joined the hips and shoulders with a continuous inner torso, removed loose Father fur tufts, and gave the mechanical half a solid steel shell. Model displays stay upright regardless of their underlying mob look pitch. Mother geometry is unchanged.

### Ice Warden animations (0.8.10)
Added idle breathing, an emerge entrance, two-arm melee follow-through, hit recoil, and native roar/sniff pose animations. Melee animation triggers on accepted damage; hit recoil triggers when the minion takes damage. These poses replace walking temporarily and settle back to the movement cycle. Native damage and attack cadence are retained.
