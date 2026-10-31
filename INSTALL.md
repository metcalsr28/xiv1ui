# Installing xiv1ui

xiv1ui is an Ashita v4 addon. It works with any FFXI install that uses Ashita v4, and has been tested on
CatsEyeXI and HorizonXI, on Windows and on Apple Silicon Macs through CrossOver.

## 1. Find your Ashita folder

It's the folder with `Ashita-cli.exe` in it, next to `addons` and `scripts` folders. On CatsEyeXI it's
`catseyexi-client\Ashita` inside the folder you installed the launcher to (for example
`C:\CatsEyeXI\catseyexi-client\Ashita`).

## 2. Install

**Windows:**

1. Copy the `addons\xiv1ui` folder from this download into your Ashita folder's `addons` folder.
2. Copy `scripts\xiv1ui.txt` into your Ashita folder's `scripts` folder.
3. Open `scripts\default.txt` in a text editor and add this line at the very end:
   ```
   /include xiv1ui.txt
   ```

**macOS or Linux (CrossOver / Wine):** open a terminal in this folder and run

```
./install.sh "<path to your Ashita folder>"
```

On a Mac, a CrossOver bottle's drive C: is at
`~/Library/Application Support/CrossOver/Bottles/<bottle name>/drive_c`. The installer does the three steps above
and keeps a backup of `default.txt` (`default.txt.before-xiv1ui`).

The CatsEyeXI launcher keeps the `/include xiv1ui.txt` line when it updates `default.txt`.

## 3. Turn off addons that draw the same things

xiv1ui has its own minimap, party list, chat, action bar, target frame and name plates. Other addons that draw
these will show up on top of it. In the CatsEyeXI launcher's addon settings (or in `default.txt`) turn off:

- the **Minimap** plugin;
- party list and HUD addons such as **tparty**, **distance**, **hxui**, **xivbar**, **fancycompass**,
  **statustimers** and **partybuffs**.

Keep your server's own plugins (on CatsEyeXI: `cexidats` and `cexislots`).

**Recommended:** HD area maps. In the CatsEyeXI launcher, enable the **Combined Maps** mod (HorizonXI ships
Remapster). The minimap uses whichever map pack XI-Pivot has enabled, and FFXI's own maps otherwise.

## 4. Play

Start the game. xiv1ui loads by itself after you log in, and FFXI's own chat log, party list, compass and clock make
way for xiv1ui's.

- **Home** key or `/xiv1ui menu` opens the Main Menu (Configuration, Gear, Inventory, Actions, Party, Exit).
- Drag anything to move it. The padlock in the bottom-right menu locks everything in place;
  `/xiv1ui layout reset` puts it all back.
- `/xiv1ui bind <slot> cmd <label> <command>` puts any command on the action bar, for example
  `/xiv1ui bind 4 cmd Invite /pcmd add <t>`.
- Using a controller? Turn it on in Configuration. The addon's README lists the buttons.

## Updating and removing

- **Update:** install the new version the same way (on macOS/Linux run `install.sh` again), then type
  `/addon reload xiv1ui` in game or restart.
- **Remove:** delete `addons\xiv1ui` and `scripts\xiv1ui.txt`, and take the `/include xiv1ui.txt` line out of
  `default.txt` (on macOS/Linux: `./install.sh --uninstall "<Ashita folder>"`). FFXI's own interface comes back.

## Troubleshooting

- **FFXI's own panels still show:** your client may lay out its windows differently. xiv1ui leaves anything it
  doesn't recognise alone. Open an issue saying which panel.
- **Name plates are FFXI's:** the Nameplate plugin didn't load. Type `/load nameplate`.
- **The minimap disc is empty:** make sure the FFXI folder (with `VTABLE.DAT` and the `ROM` folders) is the one
  your game runs from.
- **Odd characters in chat:** open an issue with the line; some servers add their own text codes.
- `/addon list` in game should show xiv1ui as `State: Ok`. Errors also go to `Ashita\logs`.

## CatsEyeXI on a Mac (CrossOver): known fixes

These aren't about xiv1ui, but they're what it takes to get CatsEyeXI running well on an Apple Silicon Mac.

1. **Where the launcher lives.** The launcher refuses to run from `Program Files`, `Windows` or `ProgramData`
   ("Startup validation failed" in `cexi.log`). Put it in `C:\CatsEyeXI\` or similar.
2. **"Install" looks like it crashed.** On first install the launcher moves itself into its install folder and
   leaves the last step (moving `CatsEyeXI-Launcher.exe` and restarting) to a PowerShell command, which Wine doesn't
   run. Move `CatsEyeXI-Launcher.exe` into the install folder yourself and start it from there.
3. **Saving the 20 GB download.** If you already have another FFXI install (from another server), copying its
   `FINAL FANTASY XI` and `PlayOnlineViewer` folders into `catseyexi-client\Game` first means the launcher only
   downloads the files that differ.
4. **Low frame rate (about 14 fps in towns).** FFXI uses old x87 floating-point maths, which Rosetta runs very
   slowly. A CrossOver-based Wine build with an x87 accelerator (x87sidecar) fixes most of it. With that Wine:
   - the launcher (a .NET 8 app) crashes at start (`Fatal error. 0x80131506`) unless you give it a compatibility
     rule that re-enables .NET and the standard renderer for it:
     ```
     export WINE_COMPATDB=$'v=5\nname=cexi-launcher;exe=CatsEyeXI-Launcher.exe;dll_overrides=mscoree=b;d3d9=wined3d;dxgi=wined3d\nname=cexi-updater;exe=CatsEyeXI-Updater.exe;dll_overrides=mscoree=b;d3d9=wined3d;dxgi=wined3d'
     ```
     (the `v=5` first line is required);
   - or keep the launcher on plain CrossOver for updates, and start the game directly with the faster Wine: run
     `Ashita-cli.exe catseyexi.ini` from the Ashita folder. That's the boot profile the launcher writes when you press
     Start.
   - Don't run two different Wines on the same bottle at the same time.
   - Still short of frames? Lower environment animations (2 → 1) and the maximum number of sounds (20 → 12) in the
     launcher's settings. Texture settings can stay high.
5. **Controller not working in game** (the launcher's log says "GamePad is disabled"). Set the controller up with
   FFXI's gamepad configuration. The launcher only enables it once those settings exist.

**Privacy:** the CatsEyeXI launcher saves your login in plain text, in `cexi_profiles.json` (launcher folder) and
`catseyexi-client\Ashita\config\boot\catseyexi.ini`. Don't share those files or screenshots of them.
