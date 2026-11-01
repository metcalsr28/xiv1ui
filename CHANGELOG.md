# Changelog

## 0.3.5

Fixes from the second GitHub issue report (thanks again, hechina1777) and from Reddit:
- Damage numbers: each hit showed twice. Now once.
- Items: the highlight jumped around after paging (Left / Right). The game doesn't always list items in bag order
  (an item that arrived in a freed slot is listed last until you sort); xiv1ui now follows the game's own order.
- Missions: Chains of Promathia, Seekers of Adoulin, Rhapsodies of Vana'diel and The Voracious Resurgence showed
  "?" for every mission. Their names show now.
- Exchange menus (Records of Eminence, Domain Invasion, high-tier battlefields ...): options naming an item or key
  item came out blank or as "Equ.". Such menus are now shown in FFXI's own box, which has the full names.
- Equipment: the selected slot's item level, jobs and stats under the grid; the item card no longer appears late,
  after closing Equipment.
- Mog House: the job change and area lists are no longer covered by the chat logs (the logs step aside while a
  game window you're using overlaps them).
- Chat: auto-translate phrases read {Phrase} (they showed "{Phrase}(" ); a message holding two lines no longer
  draws its second line over the next one.
- Action bar: each action's name above its slot (Configuration » HUD » "Action names on the bar": above the slot,
  on the icon, or off).
- Text: no more thin spikes on the sharp points of letters. The font library's outline is drawn with clipped
  corners (gdifonts/gdifonttexture-clip.dll, built from gdifonttexture's source; see tools/gdifonttexture).
- The clock and moon text a little larger.

**Known issues**
- Areas with several floors (Ru'Avitau, Ru'Hmet, the Adoulin gates and caverns, Ra'Kaznar Inner Court ...) still
  show a blank minimap.

## 0.3.4

Fixes from the first GitHub issue report (thanks, hechina1777):
- Windows: some of FFXI's windows could be mistaken for a stray copy of their name in memory on Windows (the item
  info box, Profile, Job Levels, skills, Merits, Missions, party windows ...). It made the Equipment list's highlight
  stick on "Storage Options", left FFXI's item card showing faintly under xiv1ui's windows, and could light the wrong
  item in item lists.
- Equipment: the list follows the game's own cursor, and finds which bag (inventory or a Mog Wardrobe) it shows by
  itself.
- Magic from the action menu (Enter / A on yourself or a target): the list is the game's: what your jobs can cast,
  Blue Magic only when set (plus Unbridled Learning's spells), in the game's order. It used to show one magic type
  and guess which from the help text, so the highlight could jump several spells, flicker or land on another spell
  (Metallic Body and Stoneskin share their description).
- Blue Magic: spells that aren't set are greyed out, as in the game.
- Items from the action menu: shown in xiv1ui's style again with more than 10 usable items (FFXI's own list showed
  instead).
- Item lists: if the game's cursor and the item info box ever disagree, the item itself wins.
- Damage numbers: several at once on one target (multiple attacks in a round, multi-hit weapon skills, a party
  hitting together) come one after another and stack upward, instead of appearing together in one spot.

## 0.3.3

- Magic lists follow FFXI's own sort order. If you sorted a list (numpad + in the list: Sort » Auto / Manual), the
  highlighted entry could name a different spell than the one cast, most visibly with Trust (choosing one Trust
  summoned another). Sorting by hand also shows the game's "Select a spell or song to move" prompts.

## 0.3.2

- Equipment: the item list for a slot now matches the game's (items your job can't use are listed, greyed out), so
  the highlight follows the cursor and the item you choose is the one equipped.
- Magic and ability lists: the highlight follows the cursor through higher tiers you can't cast yet (Diaga II,
  Protect IV ...). It used to stick on the first spell of a family, since tiers share their description.
- Items: the first opening in a session no longer pauses for a moment (item icons are now loaded ahead of time).

**Known issues**
- Map markers are still very broken with xiv1ui. Until it's fixed, turn off Configuration » Controls » "Command
  menu (Enter / A) in the FF style" while you set markers.

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
