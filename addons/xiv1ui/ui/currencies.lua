--[[
* xiv1ui - Status » Currencies and Currencies 2, in place of FFXI's long blue lists (window "menu    evitem", which
* the Key Items menu also uses; here it's opened from Status, statcom2).
*
* The values come from the server's packets (layouts as documented in Windower's packets/fields.lua):
*   0x113 Currencies (sent when the list opens), 0x118 Currencies 2.
* xiv1ui shows a currency window: the ones you have first, bright, with their amounts; the rest dimmed under them.
* The game keeps running its list: its cursor (class +0x30, 0-based) and length (+0x40) scroll xiv1ui's window, and
* Esc / B close it as before.
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local mem     = require('core.mem');
local store   = require('core.store');
local gamewin = require('core.gamewin');
local xi_now  = require('core.now');

local cur = {};

-- { label, offset, type } with type i32 / u16 / u8 (packet offsets include the 4-byte header)
local LIST1 = {
    { 'Conquest Points (San d\'Oria)', 0x04, 'i32' }, { 'Conquest Points (Bastok)', 0x08, 'i32' },
    { 'Conquest Points (Windurst)', 0x0C, 'i32' }, { 'Beastmen\'s Seals', 0x10, 'u16' }, { 'Kindred\'s Seals', 0x12, 'u16' },
    { 'Kindred\'s Crests', 0x14, 'u16' }, { 'High Kindred\'s Crests', 0x16, 'u16' },
    { 'Sacred Kindred\'s Crests', 0x18, 'u16' }, { 'Ancient Beastcoins', 0x1A, 'u16' }, { 'Valor Points', 0x1C, 'u16' },
    { 'Scylds', 0x1E, 'u16' }, { 'Guild Points (Fishing)', 0x20, 'i32' }, { 'Guild Points (Woodworking)', 0x24, 'i32' },
    { 'Guild Points (Smithing)', 0x28, 'i32' }, { 'Guild Points (Goldsmithing)', 0x2C, 'i32' },
    { 'Guild Points (Clothcraft)', 0x30, 'i32' }, { 'Guild Points (Leathercraft)', 0x34, 'i32' },
    { 'Guild Points (Bonecraft)', 0x38, 'i32' }, { 'Guild Points (Alchemy)', 0x3C, 'i32' },
    { 'Guild Points (Cooking)', 0x40, 'i32' }, { 'Cinders', 0x44, 'i32' }, { 'Ballista Points', 0x50, 'i32' },
    { 'Fellow Points', 0x54, 'i32' }, { 'Chocobucks (San d\'Oria)', 0x58, 'u16' }, { 'Chocobucks (Bastok)', 0x5A, 'u16' },
    { 'Chocobucks (Windurst)', 0x5C, 'u16' }, { 'Daily Tally', 0x5E, 'u16' }, { 'Research Marks', 0x60, 'i32' },
    { 'Moblin Marbles', 0x68, 'i32' }, { 'Infamy', 0x6C, 'u16' }, { 'Prestige', 0x6E, 'u16' },
    { 'Legion Points', 0x70, 'i32' }, { 'Sparks of Eminence', 0x74, 'i32' }, { 'Shining Stars', 0x78, 'i32' },
    { 'Imperial Standing', 0x7C, 'i32' }, { 'Assault Points (Leujaoam Sanctum)', 0x80, 'i32' },
    { 'Assault Points (M.J.T.G.)', 0x84, 'i32' }, { 'Assault Points (Lebros Cavern)', 0x88, 'i32' },
    { 'Assault Points (Periqia)', 0x8C, 'i32' }, { 'Assault Points (Ilrusi Atoll)', 0x90, 'i32' },
    { 'Nyzul Tokens', 0x94, 'i32' }, { 'Zeni', 0x98, 'i32' }, { 'Jettons', 0x9C, 'i32' }, { 'Therion Ichor', 0xA0, 'i32' },
    { 'Allied Notes', 0xA4, 'i32' }, { 'A.M.A.N. Vouchers', 0xA8, 'u16' }, { 'Login Points', 0xAA, 'u16' },
    { 'Cruor', 0xAC, 'i32' }, { 'Resistance Credits', 0xB0, 'i32' }, { 'Dominion Notes', 0xB4, 'i32' },
    { 'Traverser Stones', 0xC0, 'i32' }, { 'Voidstones', 0xC4, 'i32' }, { 'Kupofried\'s Corundums', 0xC8, 'i32' },
    { 'Reclamation Marks', 0xE0, 'i32' }, { 'Unity Accolades', 0xE4, 'i32' }, { 'Deeds', 0xF8, 'i32' },
};
local LIST2 = {
    { 'Bayld', 0x04, 'i32' }, { 'Kinetic Units', 0x08, 'u16' }, { 'Coalition Imprimaturs', 0x0A, 'u8' },
    { 'Mystical Canteens', 0x0B, 'u8' }, { 'Obsidian Fragments', 0x0C, 'i32' }, { 'Lebondopt Wings Stored', 0x10, 'u16' },
    { 'Pulchridopt Wings Stored', 0x12, 'u16' }, { 'Mweya Plasm Corpuscles', 0x14, 'i32' },
    { 'Ghastly Stones Stored', 0x18, 'u8' }, { 'Verdigris Stones Stored', 0x1B, 'u8' },
    { 'Wailing Stones Stored', 0x1E, 'u8' }, { 'Mellidopt Wings Stored', 0x48, 'u16' }, { 'Escha Beads', 0x4A, 'u16' },
    { 'Escha Silt', 0x4C, 'i32' }, { 'Potpourri', 0x50, 'i32' }, { 'Hallmarks', 0x54, 'i32' },
    { 'Total Hallmarks', 0x58, 'i32' }, { 'Badges of Gallantry', 0x5C, 'i32' }, { 'Crafter Points', 0x60, 'i32' },
};

local data = { [0x113] = nil, [0x118] = nil };

local function read(d, off, ty)
    if d == nil then return nil; end
    local size = (ty == 'u8' and 1) or (ty == 'u16' and 2) or 4;
    if #d < off + size then return nil; end
    local v = 0;
    for i = size, 1, -1 do v = v * 256 + d:byte(off + i); end
    if ty == 'i32' and v >= 2147483648 then v = v - 4294967296; end
    return v;
end

function cur.packet(e)
    if (e.id == 0x113 or e.id == 0x118) and e.data then data[e.id] = e.data; end
end

local function commas(n)
    local s = tostring(n);
    local k;
    repeat s, k = s:gsub('^(-?%d+)(%d%d%d)', '%1,%2'); until k == 0;
    return s;
end

-- which list is open: the Status menu row chosen before the game's list took focus
local function which()
    local cm = require('ui.cmdmenu');
    if store.data.cmd_menu == false or gamewin.window('evitem') == nil then return nil; end
    if (cm.opener or {}).evitem ~= 'statcom2' then return nil; end
    local _, f = require('core.native').focused();
    if f ~= 'evitem' then return nil; end
    local c = (cm.last_choice or {}).statcom2;
    if c == 'Currencies' then return 0x113, LIST1, 'Currencies'; end
    if c == 'Currencies 2' then return 0x118, LIST2, 'Currencies 2'; end
    return nil;
end

local hider = gamewin.new();
local opened = nil;
function cur.release() hider:restore(); end

local ROW_H, SHOWN = 30, 12;

function cur.render()
    local id, list, title = which();
    if id == nil then
        if hider:active() then hider:restore(); end
        opened = nil;
        return;
    end
    hider:hide({ 'evitem' });
    opened = opened or xi_now();
    local a = math.min(1, (xi_now() - opened) / 0.15);
    local d = data[id];
    -- the ones you have first (in the server's order), then the rest
    local rows = {};
    for _, c in ipairs(list) do
        local v = read(d, c[2], c[3]);
        if v and v ~= 0 then rows[#rows + 1] = { c[1], v }; end
    end
    local have = #rows;
    for _, c in ipairs(list) do
        local v = read(d, c[2], c[3]);
        if not (v and v ~= 0) then rows[#rows + 1] = { c[1], v }; end
    end
    -- scroll with the game's cursor (its list has its own order and length)
    local slot = gamewin.slot('evitem');
    local cls = slot and mem.u32(slot);
    local gc, gn = cls and mem.u32(cls + 0x30) or 0, cls and mem.u32(cls + 0x40) or 1;
    local first = 0;
    if #rows > SHOWN and gn and gn > 1 then first = math.floor((#rows - SHOWN) * math.min(1, gc / (gn - 1)) + 0.5); end

    local W = 460;
    local H = 52 + SHOWN * ROW_H + 40;
    local x, y = layout.anchor('topleft', W, H, 40, 60, 'currencies');
    local col = draw.alpha(0xFFFFFFFF, a);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh, col);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th, col);
    draw.image('title_swash', x + 8, y + 4, { color = col });
    local t = ui.label('cur_title', 'name', { font_height = 22 });
    t:set_opacity(a);
    text.draw(t, title, x + 40, y + 27, 'baseline');
    if d == nil then
        local w = ui.label('cur_wait', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
        w:set_opacity(a);
        text.draw(w, 'Waiting for the server...', x + 28, y + 80, 'baseline');
        return;
    end
    for r = 1, math.min(SHOWN, #rows - first) do
        local i = r + first;
        local row = rows[i];
        local ry = y + 52 + (r - 1) * ROW_H;
        local owned = i <= have;
        if i == have + 1 and have > 0 then draw.rect(x + 24, ry - 3, W - 48, 1, draw.alpha(0x60C8A860, a)); end
        local k = ui.label('cur_k' .. r, 'small', { font_height = 17 });
        local v = ui.label('cur_v' .. r, 'small', { font_height = 17, font_alignment = text.align.Right });
        local c1 = owned and 0xFFF4F0E6 or 0xFF8C887C;
        if k.settings.font_color ~= c1 then k:set_font_color(c1); v:set_font_color(owned and 0xFFF0DCA0 or 0xFF8C887C); end
        k:set_opacity(a); v:set_opacity(a);
        text.draw(k, row[1], x + 28, ry + ROW_H - 9, 'baseline');
        text.draw(v, row[2] and commas(row[2]) or '-', x + W - 28, ry + ROW_H - 9, 'baseline');
    end
    local foot = ui.label('cur_foot', 'small', { font_height = 14, font_color = 0xFFB8A880 });
    foot:set_opacity(a);
    text.draw(foot, string.format('%d of %d held.   Up / Down scroll.', have, #rows), x + 24, y + H - 16, 'baseline');
end

return cur;
