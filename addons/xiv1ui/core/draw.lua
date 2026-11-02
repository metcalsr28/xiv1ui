--[[
* xiv1ui - drawing core.
*
* One ID3DXSprite batch per frame. Modules draw textures (PNG files under assets/) and text (gdifonts objects)
* through the helpers here, in the order they are called, between draw.begin_frame() and draw.end_frame().
*
* Scale: modules lay out in HUD units, designed for a 1080-pixel-high screen, and every helper here multiplies
* positions and sizes by draw.scale on the way to the sprite (D3DX8's sprite has no SetTransform). draw.scale is the
* screen's height / 1080 (so the HUD keeps its proportions at any resolution) times the player's UI scale
* (Configuration » UI scale, draw.user_scale).
--]]

local d3d8 = require('d3d8');
local ffi  = require('ffi');

local draw = {};

draw.scale = 1;              -- HUD units -> screen pixels (screen_k() * user_scale)
draw.user_scale = 1;         -- the player's UI scale
draw.SCALES = { 0.8, 0.9, 1, 1.1, 1.25, 1.4, 1.5 };
draw.DESIGN_H = 1080;        -- the screen height the HUD is laid out for

--- Screen height / 1080: the HUD's size at a UI scale of 100%.
function draw.screen_k()
    local ok, h = pcall(function () return require('scaling').window.h; end);
    h = ok and tonumber(h) or 0;
    if h <= 0 then return 1; end
    return math.max(0.5, math.min(4, h / draw.DESIGN_H));
end

--- Size of one HUD part relative to the rest (Configuration » HUD: action bar, target, party list ...). While a part
-- draws, draw.scale includes its factor; layout.screen() then reports the screen in that part's units, so anchors
-- still land on the same screen edges. draw.part is that factor (1 outside a scaled part).
draw.part = 1;
function draw.push_part(k)
    draw.part = k;
    draw.scale = draw.screen_k() * draw.user_scale * k;
end
function draw.pop_part()
    draw.part = 1;
    draw.scale = draw.screen_k() * draw.user_scale;
end

--- Set the player's UI scale (clamped to the offered range) for the next frame.
function draw.set_scale(s)
    s = tonumber(s) or 1;
    draw.user_scale = math.max(draw.SCALES[1], math.min(draw.SCALES[#draw.SCALES], s));
    draw.scale = draw.screen_k() * draw.user_scale;
end

local device  = d3d8.get_device();
local sprite  = nil;
local cache   = {};      -- texture path -> { tex, w, h } (false = failed to load)
local base    = nil;     -- addon folder, with trailing backslash

local vec_pos   = ffi.new('D3DXVECTOR2', { 0, 0 });
local vec_scale = ffi.new('D3DXVECTOR2', { 1, 1 });
local vec_rot   = ffi.new('D3DXVECTOR2', { 0, 0 });
local rect      = ffi.new('RECT', { 0, 0, 0, 0 });

function draw.init(addon_path)
    base = addon_path;
    local out = ffi.new('ID3DXSprite*[1]');
    if ffi.C.D3DXCreateSprite(device, out) == ffi.C.S_OK then
        sprite = d3d8.gc_safe_release(ffi.cast('ID3DXSprite*', out[0]));
    end
    return sprite ~= nil;
end

function draw.release()
    cache = {};
    sprite = nil;
end

-- Themes: 'gold' (black and gold, the default) swaps these window pieces for their *_gold twins (made by
-- tools/make_art.py); 'classic' keeps the blue and white originals. The choice is store.data.theme.
local THEMED = { win_body = true, win_title = true, row_sel = true, btn_pill = true, btn_pill_focus = true,
                 cmd_panel = true, cmd_panel_sel = true };
function draw.theme()
    local st = package.loaded['core.store'];
    return (st and st.data and st.data.theme) or 'gold';
end

-- The signature icons (sig_*) live in one file, assets/sig_icons.pak (tools/make_signature_icons.py): b'XSIGPAK1',
-- u32 count, count x (u16 name length, name, u32 offset, u32 size), then the PNGs. The index is read once; each icon's
-- bytes when it's first drawn.
local pak = nil;            -- name -> { offset, size }, or false
local function pak_index()
    if pak ~= nil then return pak; end
    pak = false;
    local f = io.open(base .. 'assets\\sig_icons.pak', 'rb');
    if f == nil then return pak; end
    local function u(n)
        local s = f:read(n);
        if s == nil or #s < n then return nil; end
        local v = 0;
        for i = n, 1, -1 do v = v * 256 + s:byte(i); end
        return v;
    end
    if f:read(8) ~= 'XSIGPAK1' then f:close(); return pak; end
    local idx = {};
    for _ = 1, u(4) or 0 do
        local len = u(2);
        local name = len and f:read(len);
        local off, size = u(4), u(4);
        if not (name and off and size) then break; end
        idx[name] = { off, size };
    end
    f:close();
    pak = idx;
    return pak;
end

local function pak_texture(name)
    local idx = pak_index();
    local e = idx and idx[name];
    if e == nil then return nil; end
    local f = io.open(base .. 'assets\\sig_icons.pak', 'rb');
    if f == nil then return nil; end
    f:seek('set', e[1]);
    local bytes = f:read(e[2]);
    f:close();
    if bytes == nil or #bytes ~= e[2] then return nil; end
    local out = ffi.new('IDirect3DTexture8*[1]');
    if ffi.C.D3DXCreateTextureFromFileInMemoryEx(device, bytes, #bytes, 0xFFFFFFFF, 0xFFFFFFFF, 1, 0,
            ffi.C.D3DFMT_A8R8G8B8, ffi.C.D3DPOOL_MANAGED, ffi.C.D3DX_DEFAULT, ffi.C.D3DX_DEFAULT, 0,
            nil, nil, out) ~= ffi.C.S_OK then
        return nil;
    end
    local tex = d3d8.gc_safe_release(ffi.cast('IDirect3DTexture8*', out[0]));
    local ok, desc = tex:GetLevelDesc(0);
    if ok ~= 0 then return nil; end
    return { tex = tex, w = desc.Width, h = desc.Height };
end

--- Load (once) a texture from assets/<name>.png (a signature icon from the pack). Returns the cache entry or nil.
function draw.texture(name)
    if THEMED[name] and draw.theme() == 'gold' then name = name .. '_gold'; end
    local t = cache[name];
    if t ~= nil then return t or nil; end
    if name:sub(1, 4) == 'sig_' then
        t = pak_texture(name);
        cache[name] = t or false;
        return t;
    end
    local path = base .. 'assets\\' .. name .. '.png';
    local out = ffi.new('IDirect3DTexture8*[1]');
    -- D3DX_DEFAULT_NONPOW2-style sizes are not available in d3d8; keep source PNGs power-of-two.
    if ffi.C.D3DXCreateTextureFromFileExA(device, path, 0xFFFFFFFF, 0xFFFFFFFF, 1, 0, ffi.C.D3DFMT_A8R8G8B8,
            ffi.C.D3DPOOL_MANAGED, ffi.C.D3DX_DEFAULT, ffi.C.D3DX_DEFAULT, 0, nil, nil, out) ~= ffi.C.S_OK then
        cache[name] = false;
        return nil;
    end
    local tex = d3d8.gc_safe_release(ffi.cast('IDirect3DTexture8*', out[0]));
    local ok, desc = tex:GetLevelDesc(0);
    if ok ~= 0 then
        cache[name] = false;
        return nil;
    end
    t = { tex = tex, w = desc.Width, h = desc.Height };
    cache[name] = t;
    return t;
end

function draw.begin_frame()
    if sprite == nil then return false; end
    sprite:Begin();
    return true;
end

function draw.end_frame()
    if sprite ~= nil then sprite:End(); end
end

function draw.sprite()
    return sprite;
end

--- Draw a texture (or part of it) at x,y.
-- opts: sx, sy, sw, sh = source rect (default whole texture); scale (number or {x,y}); color (ARGB, default white);
--       rot (radians, around the rect centre).
function draw.image(name, x, y, opts)
    local t = draw.texture(name);
    if t == nil or sprite == nil then return; end
    opts = opts or {};
    local sx, sy = opts.sx or 0, opts.sy or 0;
    -- default to the art's real size (canvases are padded to powers of two; see assets/manifest.lua)
    local cw, ch = require('core.layout').size(name);
    if cw == 0 then cw, ch = t.w, t.h; end
    local sw, sh = opts.sw or cw, opts.sh or ch;
    if sw <= 0 or sh <= 0 then return; end
    rect.left, rect.top, rect.right, rect.bottom = sx, sy, sx + sw, sy + sh;
    local s, k = opts.scale or 1, draw.scale;
    if type(s) == 'table' then vec_scale.x, vec_scale.y = s[1] * k, s[2] * k; else vec_scale.x, vec_scale.y = s * k, s * k; end
    vec_pos.x, vec_pos.y = x * k, y * k;
    if opts.rot then
        vec_rot.x, vec_rot.y = sw * vec_scale.x / 2, sh * vec_scale.y / 2;
        sprite:Draw(t.tex, rect, vec_scale, vec_rot, opts.rot, vec_pos, opts.color or 0xFFFFFFFF);
    else
        sprite:Draw(t.tex, rect, vec_scale, nil, 0.0, vec_pos, opts.color or 0xFFFFFFFF);
    end
end

--- A solid rectangle (x, y, w, h in HUD units) in a colour (ARGB).
function draw.rect(x, y, w, h, color)
    if w <= 0 or h <= 0 then return; end
    draw.image('white', x, y, { scale = { w / 8, h / 8 }, color = color });
end

--- Load (once) a texture from an image held in memory (e.g. FFXI status icons and item icons from the resource
-- manager). key names it in the cache; ptr/size are the bitmap data. Returns the cache entry or nil.
-- mips: build the full mipmap chain (for big pictures drawn much smaller, e.g. area maps in the minimap disc;
-- without it the paper texture of a map aliases into noise).
function draw.texture_mem(key, ptr, size, mips)
    local t = cache[key];
    if t ~= nil then return t or nil; end
    if ptr == nil then cache[key] = false; return nil; end
    local out = ffi.new('IDirect3DTexture8*[1]');
    if ffi.C.D3DXCreateTextureFromFileInMemoryEx(device, ptr, size or -1, 0xFFFFFFFF, 0xFFFFFFFF, mips and 0 or 1, 0,
            ffi.C.D3DFMT_A8R8G8B8, ffi.C.D3DPOOL_MANAGED, ffi.C.D3DX_DEFAULT, ffi.C.D3DX_DEFAULT, 0xFF000000,
            nil, nil, out) ~= ffi.C.S_OK then
        cache[key] = false;
        return nil;
    end
    local tex = d3d8.gc_safe_release(ffi.cast('IDirect3DTexture8*', out[0]));
    local ok, desc = tex:GetLevelDesc(0);
    if ok ~= 0 then cache[key] = false; return nil; end
    t = { tex = tex, w = desc.Width, h = desc.Height };
    cache[key] = t;
    return t;
end

--- FFXI's own icon for a status effect id (from the resource manager), as a cache entry or nil.
function draw.status_icon(id)
    local key = 'status:' .. id;
    if cache[key] ~= nil then return cache[key] or nil; end
    local icon = AshitaCore:GetResourceManager():GetStatusIconByIndex(id);
    if icon == nil then cache[key] = false; return nil; end
    return draw.texture_mem(key, icon.Bitmap, ashita.interface_version == nil and icon.ImageSize or -1);
end

--- FFXI's own icon for an item id.
function draw.item_icon(id)
    local key = 'item:' .. id;
    if cache[key] ~= nil then return cache[key] or nil; end
    local item = AshitaCore:GetResourceManager():GetItemById(id);
    if item == nil then cache[key] = false; return nil; end
    return draw.texture_mem(key, item.Bitmap, ashita.interface_version == nil and item.ImageSize or -1);
end

--- Draw a cache entry (from texture_mem / status_icon / item_icon) at x,y scaled to w x h.
function draw.entry(t, x, y, w, h, color)
    if t == nil or sprite == nil then return; end
    rect.left, rect.top, rect.right, rect.bottom = 0, 0, t.w, t.h;
    local k = draw.scale;
    vec_scale.x, vec_scale.y = (w or t.w) / t.w * k, (h or t.h) / t.h * k;
    vec_pos.x, vec_pos.y = x * k, y * k;
    sprite:Draw(t.tex, rect, vec_scale, nil, 0.0, vec_pos, color or 0xFFFFFFFF);
end

--- Draw part of a cache entry: source rect sx, sy, sw, sh (texture pixels) to x, y, w, h. flip_y mirrors it
-- vertically (for textures stored bottom-up).
function draw.entry_rect(t, sx, sy, sw, sh, x, y, w, h, color, flip_y)
    if t == nil or sprite == nil or sw <= 0 or sh <= 0 then return; end
    if flip_y then sy = t.h - sy - sh; end
    rect.left, rect.top, rect.right, rect.bottom = sx, sy, sx + sw, sy + sh;
    local k = draw.scale;
    vec_scale.x, vec_scale.y = w / sw * k, (flip_y and -h or h) / sh * k;
    vec_pos.x, vec_pos.y = x * k, (flip_y and y + h or y) * k;
    sprite:Draw(t.tex, rect, vec_scale, nil, 0.0, vec_pos, color or 0xFFFFFFFF);
end

--- Nine-slice: draw texture `name` stretched to w x h keeping c-pixel corners crisp (c in content pixels).
-- cw/ch are the texture's content size (from layout.size); corners are drawn 1:1, edges and centre stretched.
function draw.nine(name, x, y, w, h, c, cw, ch, color)
    local t = draw.texture(name);
    if t == nil or sprite == nil then return; end
    color = color or 0xFFFFFFFF;
    w, h = math.max(w, 2 * c), math.max(h, 2 * c);
    local mw, mh = cw - 2 * c, ch - 2 * c;          -- source middle size
    local dw, dh = w - 2 * c, h - 2 * c;            -- destination middle size
    local xs = { { 0, c, 0, c }, { c, mw, c, dw }, { cw - c, c, w - c, c } };
    local ys = { { 0, c, 0, c }, { c, mh, c, dh }, { ch - c, c, h - c, c } };
    local k = draw.scale;
    for _, X in ipairs(xs) do
        for _, Y in ipairs(ys) do
            if X[2] > 0 and Y[2] > 0 and X[4] > 0 and Y[4] > 0 then
                rect.left, rect.top, rect.right, rect.bottom = X[1], Y[1], X[1] + X[2], Y[1] + Y[2];
                vec_scale.x, vec_scale.y = X[4] / X[2] * k, Y[4] / Y[2] * k;
                vec_pos.x, vec_pos.y = (x + X[3]) * k, (y + Y[3]) * k;
                sprite:Draw(t.tex, rect, vec_scale, nil, 0.0, vec_pos, color);
            end
        end
    end
end

--- Size of a texture, or 0,0 if missing.
function draw.size(name)
    local t = draw.texture(name);
    if t == nil then return 0, 0; end
    return t.w, t.h;
end

--- Multiply a colour's alpha by a (0..1).
function draw.alpha(color, a)
    local ca = bit.rshift(color, 24);
    local c = bit.bor(bit.lshift(math.floor(ca * a + 0.5), 24), bit.band(color, 0x00FFFFFF));
    -- LuaJIT bit ops return signed 32-bit numbers; D3D colours must be unsigned
    if c < 0 then c = c + 4294967296; end
    return c;
end

return draw;
