# xiv1ui

An interface for **FINAL FANTASY XI** (Ashita v4) modelled on the **FINAL FANTASY XIV 1.0** HUD, in its final form
(patches 1.18a–1.23b): action bar, gauges, party list, target frame, chat logs, minimap, NPC dialogue window, Main
Menu, and a restyled title screen and character creation. It only *displays* information and acts through the
game's own text commands when you click or press something. It never sends packets of its own.

Built and tested on **CatsEyeXI** and **HorizonXI**.

## Install

See [`INSTALL.md`](INSTALL.md). In short, for any Ashita v4 install:

1. Copy `addons/xiv1ui` into your Ashita folder's `addons` folder.
2. Copy `scripts/xiv1ui.txt` into your Ashita folder's `scripts` folder.
3. Add this line at the end of `scripts/default.txt`:
   ```
   /include xiv1ui.txt
   ```
4. Start the game.

On macOS or Linux (CrossOver / Wine), `./install.sh "<Ashita folder>"` does steps 1–3. Turn off other HUD addons
that draw the same things (a minimap plugin, party list or action bar addons), or you'll see both. `INSTALL.md`
also has known fixes for running CatsEyeXI on Apple Silicon Macs.

## Using it

The addon's [README](addons/xiv1ui/README.md) lists every element, the commands, controller support and the
optional extras (the Nameplate plugin for name plates, HD area maps through XI-Pivot).

## Licence

GNU General Public License v3.0 or later (`LICENSE`). Fonts: Alegreya and Noto Serif JP (SIL Open Font License 1.1).
Text rendering: gdifonts (MIT). All artwork is original, drawn by `tools/make_art.py`; no Square Enix assets are
included. FINAL FANTASY is a registered trademark of Square Enix; this project is not affiliated with Square Enix.
