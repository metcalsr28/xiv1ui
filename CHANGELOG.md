# Changelog

## 0.4.0

- Customized icons for nearly every action a player can put on the action bar: about 1,300 spells, job
  abilities, weapon skills, songs, ninjutsu, Blood Pacts and Blue Magic spells, each its own painting (Savage Blade,
  Knights of Round, Rudra's Storm, Meteor, the summons and their astral flows, Cocoon, Magic Fruit ...). Element
  and stat families (Bar-, En-, Boost-, storms, Etudes, Carols, helixes, Quick Draw, runes, Maneuvers, Geo-/Indi-)
  come in their element's colour. Higher tiers share their painting, with the numeral on the slot.
- The title screen shows Final Fantasy XI's own logo, Yoshitaka Amano's art, over the scenery in xiv1ui's gold,
  read from your game install (nothing of the game's art comes with xiv1ui). On a server whose client replaces
  the logo with its own branding, the title screen keeps xiv1ui's lettering. Configuration » General to turn it
  off.
- Chat tabs on the General log: General, Party, Linkshell and Tells. A tab you aren't looking at shows a dot when
  something new arrives for it (pink for a tell).
- A tell brings up a notice above the logs ("Tell from Aldo   Ctrl+R: reply") for a few seconds.
- The auto-translate list (Tab while typing) in xiv1ui's style: categories, phrases, your items and key items, with
  a scroll bar; phrases show with FFXI's green and red brackets in the logs and on the line you're typing.
  Auto-translate phrases no longer turn into junk characters in the logs and the dialogue box.
- Chat: Ctrl+R replies to the last tell (the chat line opens with "/tell <name> "). Page Up / Page Down scroll the
  General log (with Shift, the Battle log). Unity and Assist chat have their own colours and can be hidden
  (Configuration » Chat). The logs step aside for the auto-translate list (Tab while typing). Lines FFXI indents
  (the moon phase) are no longer cut short. A linkshell's message shows in the linkshell colour.
- The action menu (Enter / A) glides to the other side of your character when the character runs over toward it,
  so it never covers the character (Configuration » Controls to turn it off).
- Names over characters no longer draw on top of FFXI's own menus (the ones xiv1ui leaves to the game).
- Records of Eminence (Commands » Quests) in xiv1ui's style: the objectives you've taken on with progress bars and
  goals, limited-time challenges in pink, the selected one's description, your Sparks in the title. The figures
  are kept across a reload of xiv1ui.
- The Objective List in xiv1ui's style, from the categories down to each objective: progress or "Complete", the
  ones you've taken on marked, and Confirm on an objective opens its page with what it asks, its rewards (Sparks,
  EXP, Unity Accolades) and whether it can be done again.
- Current / Completed Quests: Confirm on a quest opens its page (client and summary) instead of leaving the list
  looking stuck; quests in some areas (Jeuno) showed the names of the quests after them. Mission lists say
  "No current missions." / "No completed missions." as FFXI does.
- Menus: backing out of a sub-menu no longer brings back FFXI's own window behind xiv1ui's, and the quest lists
  no longer flash FFXI's window as they open and close.
- Title screen: hovering a menu row lights that row (the pointer could land on the row under it).
- A possible freeze while zoning (an unbounded walk of a window's rows) is fixed.
- A diagnostics log for bug reports (Configuration » Experimental, off unless you turn it on): it notes, for the
  last few minutes, which game window had focus and where xiv1ui and the game disagreed (a different item lit than
  the game's cursor, a list left to the game). It never records chat, tells or other players' names. Type
  /xiv1ui report to put your setup, errors.log and the log in one file, addons/xiv1ui/report.txt, to attach to
  your report.

## 0.3.7

- If something in xiv1ui fails, it now reloads itself once (and says so in the chat log) instead of leaving parts of
  the interface gone until you restart. The error is saved to addons/xiv1ui/errors.log, which helps a lot if you
  report a problem. It won't reload again within 10 minutes; a part that keeps failing just stays off.
- Items: the highlight could still jump around after sorting (pressing Down sometimes moved up). The game keeps
  several copies of the item list; xiv1ui now follows the one the game is showing.
- Shops: the Sell list follows the game's order (equipped items first), so the highlighted item is the one sold.
- Records of Eminence (Sparks) exchange: the equipment ranges read "Equ." and some item rows had stray text after
  them; they read "Equ. Lv.1 - 9. (Up to 100000)" and "Cesti. (50)" now.
- Character select: hovering a character (or Yes / No on "Log in with ...?") lights the one under the pointer. It
  used to light the character below it.

## 0.3.6

- Fix: in 0.3.5 the chat logs disappeared (until the next reload) the first time one of FFXI's own windows had
  focus.
- Minimap: areas with several floors show the floor you're on (Ru'Avitau, Ru'Hmet, the Adoulin gates and caverns,
  Ra'Kaznar Inner Court ...), as the game's Map screen picks it.
- Augments: an item's augments are listed with its description (Items, Equipment and the gear list), worded as the
  game words them.
- Equipment: the gear list follows the game's own order, so the highlight is on the item the game's cursor is on.

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
  show a blank minimap (fixed in 0.3.6).

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
