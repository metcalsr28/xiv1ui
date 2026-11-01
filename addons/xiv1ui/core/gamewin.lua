--[[
* xiv1ui - hiding the game's own windows while xiv1ui draws a screen in their place.
*
* A game window ("menu    <name>") is hidden with its two visibility bytes (+0x69, +0x6A), its cursor finger
* (+0x78) and the scale floats of its row objects (+0x1C/+0x20, 1.0 -> 0). These are the only writes known to be
* safe (docs/MODDING-NOTES.md §3); everything is put back when the owner stops asking for it. The game re-animates a
* row (scale back to 1) when its cursor moves onto or off it, so rows are checked and hidden again every frame.
*
*   local hider = gamewin.new()
*   hider:hide({ 'inventor', 'iteminfo' })   -- every frame while xiv1ui's screen is up
*   hider:restore()                           -- when it goes away
--]]

local ffi    = require('ffi');
local mem    = require('core.mem');
local native = require('core.native');

local gamewin = {};

local slots = {};            -- name -> slot address
local missed = {};           -- name -> when a lookup last failed (retried every few seconds, not every frame)
local clock = require('core.now');

local function slot(name)
    local s = slots[name];
    if s then return s; end
    local t = clock();
    if missed[name] and t - missed[name] < 3 then return nil; end
    s = native.find_slot(name);
    if s then slots[name], missed[name] = s, nil; else missed[name] = t; end
    return s;
end

gamewin.slot = slot;     -- a game window's slot by name (looked up once; a miss is retried every few seconds)

--- The window object of a game menu by name (nil if it isn't open).
function gamewin.window(name)
    local s = slot(name);
    return s and mem.chain(s, 0, 8) or nil;
end

local function is_row(r, obj) return mem.ok(r, 0x70) and mem.u32(r + 0x58) == r and mem.u32(r + 0x5C) == obj; end

--- A window's row objects (linked list at obj+0x14: node +0 next, +0x10 row).
function gamewin.rows(obj)
    local out, n = {}, mem.u32(obj + 0x14);
    while n and n ~= 0 and #out < 200 and mem.ok(n, 0x14) do
        local r = mem.u32(n + 0x10);
        if r and is_row(r, obj) then out[#out + 1] = r; end
        n = mem.u32(n);
    end
    return out;
end

local Hider = {};
Hider.__index = Hider;

local hiders = setmetatable({}, { __mode = 'k' });
function gamewin.new()
    local h = setmetatable({ wins = {}, rows = {} }, Hider);
    hiders[h] = true;
    return h;
end

--- At the start of each scene (before the game draws): rows the game re-animated since the last frame are hidden
-- again at once, so they never show for a frame.
function gamewin.early()
    for h in pairs(hiders) do
        for r, o in pairs(h.rows) do
            local sc = ffi.cast('float*', r + 0x1C);     -- (read only once it's known to be a live row)
            if is_row(r, o) and (sc[0] ~= 0 or sc[1] ~= 0) then sc[0], sc[1] = 0, 0; end
        end
    end
end

function Hider:hide(names)
    for _, name in ipairs(names) do
        local o = gamewin.window(name);
        if o then
            local w = self.wins[name];
            if not w or w.obj ~= o then
                local a, b, f = mem.u8(o + 0x69), mem.u8(o + 0x6A), mem.u8(o + 0x78);
                if a and a <= 1 and b and b <= 1 and f and f <= 1 then
                    w = { obj = o, a = a, b = b, f = f };
                    self.wins[name] = w;
                else
                    w = nil;
                end
            end
            if w then
                if mem.u8(o + 0x69) ~= 0 then mem.w8(o + 0x69, 0); end
                if mem.u8(o + 0x6A) ~= 0 then mem.w8(o + 0x6A, 0); end
                if mem.u8(o + 0x78) ~= 0 then mem.w8(o + 0x78, 0); end
                for _, r in ipairs(gamewin.rows(o)) do
                    local sc = ffi.cast('float*', r + 0x1C);
                    if self.rows[r] ~= o then
                        if sc[0] == 1 and sc[1] == 1 then sc[0], sc[1] = 0, 0; self.rows[r] = o; end
                    elseif sc[0] ~= 0 or sc[1] ~= 0 then
                        -- the game animates a row when its cursor moves and leaves its scale at 1 again: hide it again
                        sc[0], sc[1] = 0, 0;
                    end
                end
            end
        end
    end
end

function Hider:active() return next(self.wins) ~= nil or next(self.rows) ~= nil; end

--- Let go, except for windows in `linger` that are still open: those stay hidden until the game has closed them
-- (a list backed out of stays on screen for a few frames while it closes). Call every frame while letting go.
function Hider:release_except(linger)
    local keep = {};
    for _, name in ipairs(linger) do
        local w = self.wins[name];
        if w and gamewin.window(name) == w.obj then keep[#keep + 1] = name; end
    end
    if #keep == 0 then self:restore(); return; end
    local held = {};
    for _, name in ipairs(keep) do held[name] = self.wins[name]; end
    -- put back everything else
    local rows = {};
    for r, o in pairs(self.rows) do
        local keepme = false;
        for _, w in pairs(held) do if w.obj == o then keepme = true; end end
        if keepme then rows[r] = o; end
    end
    for r in pairs(rows) do self.rows[r] = nil; end
    for name in pairs(held) do self.wins[name] = nil; end
    self:restore();
    self.wins, self.rows = held, rows;
    self:hide(keep);
end

function Hider:restore()
    for r, o in pairs(self.rows) do
        if is_row(r, o) then
            local sc = ffi.cast('float*', r + 0x1C);
            if sc[0] == 0 and sc[1] == 0 then sc[0], sc[1] = 1, 1; end
        end
    end
    self.rows = {};
    for name, w in pairs(self.wins) do
        if gamewin.window(name) == w.obj then
            local o = w.obj;
            if mem.u8(o + 0x69) == 0 then mem.w8(o + 0x69, w.a); end
            if mem.u8(o + 0x6A) == 0 then mem.w8(o + 0x6A, w.b); end
            if mem.u8(o + 0x78) == 0 then mem.w8(o + 0x78, w.f); end
        end
    end
    self.wins = {};
end

-- Every game window descriptor ("menu    <name>"), found once: name -> slot. (About 900 descriptors exist; the scan
-- takes a moment, so it runs the first time it's needed and is kept.)
local all = nil;
local function all_slots()
    if all then return all; end
    all = {};
    for n = 0, 1200 do
        local a = ashita.memory.find('FFXiMain.dll', 0, '6D656E7520202020', 0, n);
        if not a or a == 0 then break; end
        if mem.u32(a + 0x10) == 0 and mem.u32(a + 0x1C) == 0 then
            local nm = (ashita.memory.read_string(a + 8, 8) or ''):gsub('[%z ]+$', '');
            local s = mem.u32(a + 0x20);
            -- (a name can appear more than once; only an entry whose slot is readable counts. This list is for
            -- looking around only; gamewin.slot() keeps its own, checked lookups. 0x756E656D is the next descriptor's "menu"
            -- text, see native.find_slot)
            if nm ~= '' and s and s > 0x10000 and s ~= 0x756E656D and mem.ok(s, 4) and all[nm] == nil then all[nm] = s; end
        end
    end
    return all;
end

-- Windows that are always about (HUD) and never in the way of a menu panel.
local HUD = { netstat = true, buff = true, logwindo = true, log2 = true, partywin = true, partyw2 = true,
              partyw3 = true, pname = true, helpwind = true, titlewin = true, targetwi = true, compass = true,
              clock = true, menuwind = true, socialme = true, statcom2 = true, persona = true, level = true };

-- The game's menu coordinates (its UI resolution) -> xiv1ui HUD units.
local ui_k = nil;
local function to_hud(v)
    if ui_k == nil then
        local c = AshitaCore:GetConfigurationManager();
        local mw = tonumber(c:GetString('boot', 'ffxi.registry', '0037') or '') or 0;
        local sw = tonumber(c:GetString('boot', 'ffxi.registry', '0001') or '') or 0;
        ui_k = (mw > 0 and sw > 0) and sw / mw or 1;
    end
    return v * ui_k / require('core.draw').scale;
end

--- Rectangles (HUD units: x, y, w, h, name) of visible game windows other than the HUD and `except` (a set).
function gamewin.occupied(except)
    local out = {};
    for nm, s in pairs(all_slots()) do
        if not HUD[nm] and not (except and except[nm]) then
            local o = mem.chain(s, 0, 8);
            if o and mem.u8(o + 0x69) == 1 and mem.u8(o + 0x6A) == 1 then
                local x1, y1, x2, y2 = mem.u16(o + 0x3A), mem.u16(o + 0x3C), mem.u16(o + 0x3E), mem.u16(o + 0x40);
                if x1 and x2 and y2 and x2 > x1 and y2 > y1 and x2 < 4000 and y2 < 4000 then
                    out[#out + 1] = { to_hud(x1), to_hud(y1), to_hud(x2 - x1), to_hud(y2 - y1), nm };
                end
            end
        end
    end
    return out;
end

--- A game window's rectangle in HUD units (x, y, w, h), or nil while it's closed or hidden (by the game or xiv1ui).
function gamewin.rect(name)
    local o = gamewin.window(name);
    if o == nil or mem.u8(o + 0x69) ~= 1 or mem.u8(o + 0x6A) ~= 1 then return nil; end
    local x1, y1, x2, y2 = mem.u16(o + 0x3A), mem.u16(o + 0x3C), mem.u16(o + 0x3E), mem.u16(o + 0x40);
    if not (x1 and y1 and x2 and y2) or x2 <= x1 or y2 <= y1 or x2 >= 4000 or y2 >= 4000 then return nil; end
    return to_hud(x1), to_hud(y1), to_hud(x2 - x1), to_hud(y2 - y1);
end

--- HUD units -> the game's menu coordinates (the inverse of to_hud).
function gamewin.from_hud(v)
    to_hud(0);
    return v * require('core.draw').scale / ui_k;
end

--- A window's rectangle in HUD units even while it's hidden (x, y, w, h), or nil.
function gamewin.raw_rect(name)
    local o = gamewin.window(name);
    if o == nil then return nil; end
    local x1, y1, x2, y2 = mem.u16(o + 0x3A), mem.u16(o + 0x3C), mem.u16(o + 0x3E), mem.u16(o + 0x40);
    if not (x1 and y1 and x2 and y2) or x2 <= x1 or y2 <= y1 or x2 >= 4000 or y2 >= 4000 then return nil; end
    return to_hud(x1), to_hud(y1), to_hud(x2 - x1), to_hud(y2 - y1);
end

--- Move a panel at x, y (w x h) right of any game window it would cover. Returns the new x.
function gamewin.clear_x(x, y, w, h, except)
    for _ = 1, 4 do
        local moved = false;
        for _, r in ipairs(gamewin.occupied(except)) do
            if x < r[1] + r[3] and r[1] < x + w and y < r[2] + r[4] and r[2] < y + h then
                x = r[1] + r[3] + 12;
                moved = true;
            end
        end
        if not moved then break; end
    end
    return x;
end

-- The item under the game's cursor in any item list: the item info window's class object keeps the item id
-- (+0x24) and its index in its bag (+0x26); 0 when no item is under the cursor.
function gamewin.cursor_item()
    local s = slot('iteminfo');
    if not s then return nil; end
    local cls = mem.u32(s);
    if cls == nil or not mem.ok(cls + 0x24, 4) then return nil; end
    local id = mem.u16(cls + 0x24);
    if id == nil or id == 0 then return nil; end
    return id, mem.u8(cls + 0x26);
end

return gamewin;
