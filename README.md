# YetiBoss
A Giant Yeti encounter for LARP SMP, targeting Paper/Purpur 26.3 using the compatible 1.21.4 Bukkit API. Java 21 or newer is required; the server's Java 25 is suitable. Version 0.2.1 is an initial server-test build.

## Install
1. Install CosmeticPets **1.5.0 or newer**, its required PacketEvents dependency, and the current CosmeticPets resource packs/mappings.
2. Download the **YetiBoss** artifact from this repository's successful GitHub Actions build. Place its JAR in plugins.
3. Restart the server. Accept **both** the CosmeticPets pack (pets) and the dedicated YetiBoss pack (boss) on Java.
   The boss ZIP is automatically requested from https://github.com/aemiroo/YetiBoss/releases/download/yeti-pack/YetiBoss-Pack.zip.
   Existing configs without resource-pack.url use that default.
   Bedrock needs the existing GeyserDisplayEntity extension/pack plus YetiBoss-Bedrock.mcpack and both boss mappings.
   Keep the CosmeticPets pack/mappings installed for the reward pet. After installing the boss files, set bedrock.enabled: true in YetiBoss config and restart Geyser/server.
4. As an operator, run /yetiboss spawn in an open arena. It spawns about six blocks ahead, requiring solid ground and five blocks of headroom.

The boss uses the **same model and colors as the CosmeticPets Baby Yeti**, enlarged with boss.model-scale (4.3 by default). Its twelve walking poses are copied from the pet's golem-style gait, with eight additional raised-arm attack poses. The pet itself is unchanged. A pinned MIT-licensed copy of the pet model helpers is included so pack builds are reproducible and do not fetch changing upstream code.

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
Any survival/adventure player dealing positive, uncanceled direct or projectile damage participates. Merely standing nearby does not count. Rewards are not restricted to the killing blow or remaining online.
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
