# Changelog

## 0.3.1

- Chat: key words in colour, so the parts that matter stand out: what a /check says (too weak / easy prey ...
  incredibly tough, high or low evasion and defense), critical hits, damage (gold dealt by your party, red taken
  by it), healing, misses, resisted spells, what a monster readies or casts, experience, levels, skill-ups and items
  obtained. Configuration » Chat » "Key words in colour" turns it off.
- The Mog House door gets the target ring and its name in the target frame when you target it.
- The Moogle's menu in your Mog House and its Storage list are restyled; options you can't use yet (Remodel, bags
  not unlocked) are greyed out, in every restyled menu, as in the game.
- The minimap no longer draws over the full-screen map.
- In your Mog House the Commands menu's last entry reads "Mog House" (it opens the Moogle's menu), as the game's does,
  instead of "Map".

**Known issues**
- Map markers are very broken: placing, removing and choosing markers (Commands » Map » Markers, or clicking the
  map) doesn't work properly with xiv1ui. Until it's fixed, turn off Configuration » Controls » "Command menu
  (Enter / A) in the FF style" while you set markers; the game's own menus then work as usual.

## 0.3.0

**Icons for everything**
- Every spell, job ability and weapon skill a player can use now has its own icon on the action bar: all White,
  Black, Summoning, Ninjutsu, Song, Geomancy and Blue Magic spells, every job's abilities (rolls, Quick Draw,
  maneuvers, runes, steps, flourishes, stratagems ...) and every player weapon skill.
- Tiers share their spell's icon and the bar shows the tier (Cure II, Fire IV, Utsusemi: Ni ...), drawn on top of
  the slot's ring.
- Pets' Ready moves, Blood Pacts and some passive traits use a shared icon with their initials for now.

**Putting your spells and abilities on the bar**
- Macros » Abilities & Spells: everything your character has learned, by category (Left / Right), with "New" on
  what isn't on a bar yet. Enter places it on any bar slot.
- Newly learned actions still go onto bar 1 by themselves while it has room; when it's full they wait as "New"
  instead of being lost.

**Fixes**
- Inventory: the highlighted row now always matches the item the game's cursor is on, and the list scrolls all
  the way down (it could stick in the first screenful, especially on a controller).
- Item and ability lists scroll like the game's; the action menu's item list counts crystals.
- The Commands menu closes in one step, without FFXI's own box flashing.
- FFXI's small menus that opened under the minimap (a linkshell's, the Bazaar's ...) are no longer hidden: the
  minimap steps aside for them.
- Minimap: Southern San d'Oria and HD map packs made like FFXI's newer maps now load.
- Character select: no longer blocks mouse movement (it could hide the mouse pointer).

**More of the game's menus restyled**
- Status » Currencies and Currencies 2: a currency window (what you hold first, with amounts).
- Key Items: each category's list, with "New" on unexamined items and the description; the Examine question and
  the examined key item.
- Quests (Current / Completed, every area) and Missions (every storyline), with each quest's client and summary.
- Abilities » Job Traits, Pet Command and Mount.
- Map » Change Map (with each area's map count) and Wide Scan (with distances for what's near).
- Synthesis: choosing a crystal, then ingredients.
- Help Desk, Bazaar, Linkshell options, Friend List, and Search's job, country, race, rank and comment lists.
- Between areas: a small "Now Loading..." in place of the "Downloading data..." bar.
- Region Info's maps and the area map: the HUD and names step aside so they don't cover them.

**Configuration**
- General: Knocked Out screen Full / Minimal; dialogue box font and text size.
- HUD: part sizes in 5% steps (60-160%); the action bar group's position in 10 px steps.

## 0.2.1
- Fix the in-game update check (the update manifest listed a file the download site doesn't serve).

## 0.2.0
- Macros: place a macro on any bar slot from a map of every bar (Green / Red 1-3); 88 icons including every action
  icon; type with the keyboard (the on-screen keyboard is for the controller).
- Edit Action Bars (last row of the Macros list): put your macros on any slot, or clear slots.
- Shift+1 / Shift+2 / Shift+3 switch the action bar page.
- Optional in-game updates (Configuration » Experimental, off by default, at your own risk): /xiv1ui update checks
  for a new release, /xiv1ui update now installs it; a check at launch says when one is available.
- Controller: Start opens the Main Menu, a tap of Back opens the map.

## 0.1.x
- Chat customisation (fonts, sizes, spacing, outline, background, resizable logs, collapsed repeats, timestamps,
  channel filters), per-part HUD sizes, a tabbed Configuration, lobby fixes.
- The HUD scales with the screen height; a Configuration window and button; redesigned bottom-right buttons.
- Fixes for the combat menu with loot in the treasure pool, and for the minimap falling back to FFXI's maps.

## 0.1
- First release: a FINAL FANTASY XIV 1.0 style interface for FINAL FANTASY XI (Ashita v4).
