--[[
* xiv1ui - the auto-translate list (Tab while typing), in xiv1ui's style in place of FFXI's box (window "fep").
*
* The game still runs the list: Up / Down / Left / Right move, Enter opens a category or puts the phrase in the
* line, Esc goes back. xiv1ui reads where the game is and draws its own list:
*   class = [slot("fep")]: +0x2202 u16 the selected entry (0-based), +0x2204 u16 how many there are
*   [class + 0x14] (the auto-translate state): +0x1FE u16 the category open, 0-based (0 = the category list), with
*     +0x1FC u16 = 0x202 inside one of the dictionary's categories; 0x207 Items, 0x213 Key Items (lists of what you
*     have, which aren't in the dictionary: built from what you hold, and left to the game's box if the count
*     differs)
* The phrases come from the auto-translate dictionary (DAT 55665, English): per category a 76-byte header (u32 id,
* 32-byte bracketed name, 32-byte name, u32 count, u32 byte size) and its entries (u32 id, u8 length, text). Entries
* that start with "@" name something else: @Y job ability / trait / weapon skill / pet command (ability id), @C a
* spell, @A an area, @J a job (hex). The game lists a category's phrases sorted by name, blanks left out.
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local mem     = require('core.mem');
local store   = require('core.store');
local gamewin = require('core.gamewin');
local xi_now  = require('core.now');

local at = {};

local hider = gamewin.new();
function at.release() hider:restore(); end

-- The dictionary: { { name, phrases = { ... sorted } }, ... } (false if the DAT can't be read).
local dict = nil;
local function load_dict()
    dict = false;
    local path = require('core.maps').dat_file(55665);
    local f = path and io.open(path, 'rb');
    if f == nil then return; end
    local d = f:read('*a');
    f:close();
    local rm = AshitaCore:GetResourceManager();
    local function resolve(t)
        local kind, hex = t:match('^@(%a)(%x+)$');
        if kind == nil then return t; end
        local id = tonumber(hex, 16);
        local r;
        if kind == 'Y' then local a = rm:GetAbilityById(id); r = a and a.Name[1];
        elseif kind == 'C' then local s = rm:GetSpellById(id); r = s and s.Name[1];
        elseif kind == 'A' then r = rm:GetString('zones.names', id);
        elseif kind == 'J' then r = rm:GetString('jobs.names', id); end
        return (r and r ~= '') and r or t;
    end
    local function u32(o) return d:byte(o + 1) + d:byte(o + 2) * 256 + d:byte(o + 3) * 65536 + d:byte(o + 4) * 16777216; end
    local out, i = {}, 0;
    while i + 76 <= #d do
        local name = d:sub(i + 37, i + 68):match('^[^%z]*');
        local count, size = u32(i + 68), u32(i + 72);
        local phrases, seen, j = {}, {}, i + 76;
        for _ = 1, count do
            local len = d:byte(j + 5) or 0;
            local t = d:sub(j + 6, j + 5 + len):match('^[^%z]*');
            t = resolve(t);
            if t:match('%S') and not seen[t] then seen[t] = true; phrases[#phrases + 1] = t; end
            j = j + 5 + len;
        end
        table.sort(phrases, function (a, b) return a:lower() < b:lower(); end);
        out[#out + 1] = { name = name, phrases = phrases };
        i = i + 76 + size;
    end
    dict = out;
end

-- The Items list: the names of what you carry (inventory), each once, by name. Key Items: the ones you hold, by id.
local function carried_items()
    local inv, rm = AshitaCore:GetMemoryManager():GetInventory(), AshitaCore:GetResourceManager();
    local out, seen = {}, {};
    for i = 1, math.min(inv:GetContainerCountMax(0) or 0, 80) do
        local it = inv:GetContainerItem(0, i);
        local r = it and it.Id ~= 0 and it.Id ~= 65535 and rm:GetItemById(it.Id);
        local nm = r and r.Name[1];
        if nm and not seen[nm] then seen[nm] = true; out[#out + 1] = nm; end
    end
    table.sort(out, function (a, b) return a:lower() < b:lower(); end);
    return out;
end
local function key_items()
    local ki, rm = require('ui.keyitems'), AshitaCore:GetResourceManager();
    local out = {};
    for id = 1, 4095 do
        if ki.has(id) then           -- (known from the server's key item packets: after a zone change)
            -- (maps aren't offered; mounts' names start with the game's music-note mark, a glyph of its own font)
            local nm = (rm:GetString('keyitems.names', id) or ''):gsub('^[\128-\255]+', '');
            if nm ~= '' and not nm:find('^[Mm]ap of ') then out[#out + 1] = (nm:gsub('^%l', string.upper)); end
        end
    end
    return out;
end

local W, ROW_H, SHOWN = 400, 26, 10;
local view_first, view_key = 0, nil;
local opened = nil;

function at.render()
    local slot = gamewin.slot('fep');
    local cls = slot and gamewin.window('fep') and mem.u32(slot);
    local st = cls and mem.u32(cls + 0x14);
    if store.data.cmd_menu == false or cls == nil or st == nil or not mem.ok(cls + 0x2200, 8) then
        if hider:active() then hider:restore(); end
        opened = nil;
        return;
    end
    if dict == nil then load_dict(); end
    local cur, n = mem.u16(cls + 0x2202), mem.u16(cls + 0x2204);
    local kind, grp = mem.u16(st + 0x1FC), mem.u16(st + 0x1FE);
    -- which list: the categories, one category's phrases, or your items / key items (anything else, or a count
    -- that doesn't match the game's, stays the game's)
    local title, rows;
    if kind == 0x207 then title, rows = 'Items', carried_items(); end
    if kind == 0x213 then title, rows = 'Key Items', key_items(); end
    if rows and #rows ~= n then rows = nil; end
    if rows then
        -- (set above)
    elseif dict and kind ~= 0x207 and kind ~= 0x213 and grp == 0 and n == #dict + 2 then
        title, rows = 'Auto-Translate', {};
        for i, g in ipairs(dict) do rows[i] = g.name; end
        rows[#rows + 1], rows[#rows + 2] = 'Key Items', 'Items';       -- (the game adds these two)
    elseif dict and kind == 0x202 and grp >= 1 and dict[grp] and #dict[grp].phrases == n then
        title, rows = dict[grp].name, dict[grp].phrases;
    end
    if rows == nil or cur == nil or cur >= #rows then
        if hider:active() then hider:restore(); end
        return;
    end
    hider:hide({ 'fep' });
    if opened == nil then opened = xi_now(); end
    local a = math.min(1, (xi_now() - opened) / 0.12);

    local key = title;
    if view_key ~= key then view_key, view_first = key, 0; end
    if cur < view_first then view_first = cur; end
    if cur >= view_first + SHOWN then view_first = cur - SHOWN + 1; end
    view_first = math.max(0, math.min(view_first, math.max(0, #rows - SHOWN)));
    local shown = math.min(SHOWN, #rows);

    -- above the chat line, at the left like FFXI's
    local chat = layout.widgets.chat;
    local _, sh = layout.screen();
    local H = 48 + shown * ROW_H + 30;
    local x = 22 + select(1, layout.offset('chat'));
    local y = sh - 46 - 34 - H - 6 + select(2, layout.offset('chat'));
    local col = draw.alpha(0xFFFFFFFF, a);
    local bw, bh = layout.size('win_body');
    -- (a solid fill first: the game still draws a faint backdrop where its own list would be)
    draw.rect(x + 6, y + 6, W - 12, H - 12, draw.alpha(0xF0100C0A, a));
    draw.nine('win_body', x, y, W, H, 12, bw, bh, col);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th, col);
    local t = ui.label('at_title', 'name', { font_height = 20 });
    t:set_opacity(a);
    text.draw(t, title, x + 18, y + 26, 'baseline');
    local cnt = ui.label('at_count', 'small', { font_height = 15, font_color = 0xFFB8C0D8, font_alignment = text.align.Right });
    cnt:set_opacity(a);
    text.draw(cnt, string.format('%d / %d', cur + 1, #rows), x + W - 18, y + 25, 'baseline');

    local sw9, sh9 = layout.size('row_sel');
    local cat = (title == 'Auto-Translate');           -- (the category list; Items / Key Items also read 0)
    for r = 1, shown do
        local i = view_first + r;               -- 1-based
        local ry = y + 42 + (r - 1) * ROW_H;
        local sel = (i - 1 == cur);
        if sel then
            draw.nine('row_sel', x + 22, ry, W - 34, ROW_H - 2, 6, sw9, sh9, col);
            draw.image('cursor_gold', x + 4, ry + 1, { color = col });
        end
        local o = ui.label('at_row' .. r, 'small', { font_height = 18 });
        local c = sel and 0xFFFFFFFF or 0xFFE0DCD0;
        if o.settings.font_color ~= c then o:set_font_color(c); end
        o:set_opacity(a);
        -- categories carry FFXI's green / red brackets, as the phrases they hold will in the line
        local label = rows[i];
        if cat then
            local bo = ui.label('at_bo' .. r, 'small', { font_height = 18, font_color = 0xFF6EE06E });
            local bc = ui.label('at_bc' .. r, 'small', { font_height = 18, font_color = 0xFFFF6E6E });
            bo:set_opacity(a); bc:set_opacity(a);
            text.draw(bo, '{', x + 34, ry + ROW_H - 7, 'baseline');
            text.set(o, label);
            local lw = text.size(o);
            text.draw(o, label, x + 44, ry + ROW_H - 7, 'baseline');
            text.draw(bc, '}', x + 46 + lw, ry + ROW_H - 7, 'baseline');
        else
            text.draw(o, label, x + 34, ry + ROW_H - 7, 'baseline');
        end
    end
    if #rows > SHOWN then
        -- a scroll bar: where the shown rows sit in the whole list
        local bx, by, bh = x + W - 12, y + 44, shown * ROW_H - 4;
        draw.rect(bx, by, 3, bh, draw.alpha(0x40FFFFFF, a));
        local th = math.max(12, bh * SHOWN / #rows);
        draw.rect(bx, by + (bh - th) * view_first / math.max(1, #rows - SHOWN), 3, th, draw.alpha(0xFFE8C878, a));
    end
    local hint = ui.label('at_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
    hint:set_opacity(a);
    text.draw(hint, cat and 'Enter: open   Esc: back' or 'Enter: put in the line   Esc: back', x + 18, y + H - 10,
              'baseline');
end

return at;
