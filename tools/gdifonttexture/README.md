# gdifonttexture-clip.dll

xiv1ui's build of ThornyFFXI's gdifonttexture (MIT, https://github.com/ThornyFFXI/gdifonttexture, commit 2d801e7),
the DLL behind gdifonts. One change in what it draws: text outlines use clipped miter joins (limit 2) instead of
GDI+'s default miter joins (limit 10), which put thin spikes on the sharp points of letters (the "A" of "Azure",
the "u" of "Huge Hornet") with xiv1ui's 2 px outlines. Corners stay as sharp as before; only the spikes are cut.
(Round joins were tried first: they fill small letters in.) The join is set after the outline is measured, as
GDI+ under-measures a clipped-miter pen and the text's top was cut off.

The rest of `clipped-joins.diff` makes it build with mingw-w64 instead of MSVC:
- `d3dx_shim.cpp`: `D3DXCreateTexture` (the one D3DX8 call), as d3dx8.lib is MSVC-only and not in the repo;
- `Defines.h`: `float` for `float_t` (mingw's x87 `float_t` is `long double`, which moved every field after
  FontHeight: no text at all), and atlbase.h only under MSVC;
- `%hs` for `%S` in swprintf; a stray end-of-file byte removed from dxfile.h.

Build (on this Mac, nothing installed outside nix):

    git clone https://github.com/ThornyFFXI/gdifonttexture src && cd src && git checkout 2d801e7
    patch -p1 < ../clipped-joins.diff
    nix-shell -p pkgsCross.mingw32.buildPackages.gcc --run "i686-w64-mingw32-g++ -std=c++17 -O2 -DUNICODE \
      -D_UNICODE -DWIN32 -DNDEBUG -shared -o gdifonttexture-clip.dll Exports.cpp GdiFontManager.cpp d3dx_shim.cpp \
      -static -static-libgcc -static-libstdc++ -Wl,--kill-at -Wl,--enable-stdcall-fixup -lgdiplus -lgdi32 \
      -luser32 -lole32 -s"

It has its own file name so that a running game (which keeps the old DLL loaded) picks it up on an addon reload,
and an update never has to overwrite a DLL in use. Same exports as the original; imports only system DLLs.
