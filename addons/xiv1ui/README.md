# xiv1ui

An interface for FINAL FANTASY XI (Ashita v4) modelled on the FINAL FANTASY XIV 1.0 HUD, in its final form
(patches 1.18a–1.23b). It only *displays* information and acts through the game's own text commands
(`/ma`, `/ja`, `/ws`, `/item`, `/equip`, `/pcmd` ...). It never sends packets of its own.

## What's in it

| 1.0 element | Where | How to use |
|---|---|---|
| Action bar, 3 bars × 10 slots | bottom centre | Click a slot, or press 1–0 (`/xiv1ui keys on`). Shift+1/2/3 shows bar 1/2/3 (also Shift+↑/↓ with keys on, or click the crest). Hover for pop-up help. |
| HP / MP / TP gauges, EXP bar | under the bar | – |
| Cast bar | above the bar | Shown while casting. |
| Target frame | top centre | Claim colours, aggression orb, enmity capsule, lock-on mark. |
| Target cursor, pop-up numbers | in the world | Gold ring over your target; damage, heal and miss numbers. |
| Status effects + skillchain ("combo") indicator | under the target frame | Hover for the name; right-click to cancel a buff. |
| Party list | bottom right | Click a member to target them. |
| Buttons | bottom right | Trade and Invite (targeted player) above; Commands (FFXI's Commands menu), Inventory (FFXI's Items menu), Map, Emotes, UI Lock, Configuration below (`/xiv1ui configbutton off` hides it). |
| Chat logs (General / Battle) | bottom left | Mouse wheel scrolls. They fade after 60 s of quiet. |
| Minimap and clock | top right | Vana'diel day, moon and time. |
| NPC dialogue | lower centre | 1.0's talk window: the speaker on a grey name plate, the line in a soft black box, a gold arrow while the game waits for you. Closes when you continue (Enter/Esc, A/B), choose an option, or the conversation ends. Lines still go to the chat log, as in 1.0. |
| Main Menu | right edge | **Home** key or `/xiv1ui menu`. ↑/↓, Enter, Esc. |

Main Menu windows:
- **Attributes**: stats, jobs, skills.
- **Gear**: paper doll plus equip.
- **Actions & Traits**: put anything on the bar.
- **Inventory**: use and equip.
- **Party**
- **Configuration**
- **Exit Game**

## Moving things

Drag any widget to move it. UI Lock (the padlock in the micro menu) freezes them.
Configuration » Reset UI positions (or `/xiv1ui layout reset`) puts them back.

**Chat** (Configuration » Chat): font (XIV1UI Serif, PT Sans, PT Serif, Arial), text size 12–28 px, line spacing,
outline, background opacity, timestamps, repeated lines collapsed with a count, and battle text in its own log or in
General. Drag the grip at a log's top-right corner to resize the logs.

**HUD sizes** (Configuration » HUD): the action bar group, target frame, party list, minimap and buttons can each be
made smaller or larger (70–150%), e.g. a smaller action bar to make room for a bigger chat.

**UI scale** (Configuration, or `/xiv1ui scale 125`): 80–150%. Text is re-rendered at the new size, so it stays sharp.
At larger sizes the chat log may reach under the action bar; drag it aside.

## Controller

Turn it on in Configuration.
- **With a window open:** the D-pad moves the cursor, A confirms, B cancels, LB/RB switch tabs.
- **Hold Back + X:** Main Menu.
- **Hold Back + A:** action-bar cursor. D-pad ←/→ picks a slot, ↑/↓ changes bar, A fires, B leaves.
- **Hold LT or RT:** the action bar switches to its LT (red crest) or RT (green crest) layer, in place of FFXI's
  macro palette. D-pad Up/Right/Down/Left fire slots 1–4, Y/B/A/X 5–8, LB/RB 9 and 10. Hold LT and RT together and
  press Up/Down to flip the page. This follows the "Action bar layers" switch, not the controller one.

## Commands

```
/xiv1ui menu                         open/close the Main Menu
/xiv1ui bind <slot> <ma|ja|ws|item> <name>    e.g. /xiv1ui bind 3 ma Cure
/xiv1ui bind <slot> cmd <label> <command>     e.g. /xiv1ui bind 1 cmd Attack /attack <t>
/xiv1ui unbind <slot> | page <n|next|prev> | use <slot> | keys <on|off> | defaults
/xiv1ui layout reset
/xiv1ui config                       open/close the Configuration window
/xiv1ui configbutton on|off          show/hide its button in the bottom-right row
/xiv1ui scale <80..150>
/xiv1ui import <book> <set>          copy an FFXI macro set onto this page's LT (Ctrl row) / RT (Alt row) layers
```

## Thanks

The NPC dialogue window is xiv1ui's own, but the chat modes and prompt codes it relies on were worked out by the
**Balloon** addon (Hando, Yuki, Ghosty, onimitch).

## FFXI's own panels, and the optional extras

xiv1ui hides the game's own panels it replaces by itself: chat log, party list, target box, cast bar, compass,
clock, connection info and the engaged HP/MP/TP box. Everything comes back when xiv1ui is unloaded.

Optional extras that make it better:
- **Nameplate plugin** (ships with most Ashita installs, `/load nameplate`): lets xiv1ui switch off FFXI's own name
  plates and draw its own. Without it, the game's name plates stay.
- **HD area maps** through XI-Pivot (Remapster on HorizonXI): the minimap uses an enabled overlay's map when it can
  read it, and FFXI's own maps otherwise. (CatsEyeXI's Combined Maps pack uses a format it can't read yet.)
- **HXIUIBegone** (HorizonXI): also hides the second chat window and the alliance lists, which xiv1ui doesn't yet.

## Credits and licences

xiv1ui itself is released under the GNU General Public License v3.0 or later (`LICENSE`).

- Fonts: built from **Alegreya** by Huerta Tipográfica / Juan Pablo del Peral (SIL Open Font License 1.1, `fonts/OFL.txt`).
  Renamed "XIV1UI Serif", as the OFL requires for modified versions.
- Japanese font: built from **Noto Serif JP** by Google (SIL Open Font License 1.1, `fonts/OFL-NotoSerifJP.txt`),
  cut down to the Shift-JIS character set and renamed "XIV1UI Serif JP".
- Chat font choices: **PT Sans** and **PT Serif** by ParaType (SIL Open Font License 1.1, `fonts/OFL-PTSans.txt`,
  `fonts/OFL-PTSerif.txt`), unmodified.
- Text rendering: **gdifonts** by Thorny (MIT, `gdifonts/LICENSE`).
- All artwork is original, drawn by `tools/make_art.py` in the style of the 1.0 interface. No Square Enix assets are
  included.
- FINAL FANTASY is a registered trademark of Square Enix. This project is not affiliated with Square Enix.
