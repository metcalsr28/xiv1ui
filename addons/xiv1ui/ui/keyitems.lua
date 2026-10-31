--[[
* xiv1ui - Commands » Key Items, a category's list, in place of FFXI's blue list (window "menu    evitem" in its list
* mode, class +0x90 = 2; the categories before it are ui/cmdmenu.lua's).
*
* Which key items a category holds comes from FFXI's own key item table (the DAT with file id 0xD993, a "d_msg"
* table: entries 0x2BC bytes from 0x40, every byte XOR 0xFF; u32 key item id at +0x3C). Headings sit in it as
* entries with id 0 and a name like "-Permanent Key Items", each one after the entries of its category; the game
* lists a category's key items in table order. Names and descriptions come from Ashita's resources. What she has
* comes from the server's key item packets (0x55: one per block of 512 ids, block number at 0x84, "held" bits from
* 0x04, "seen" bits from 0x44; sent at login and on zoning, so after a reload of xiv1ui the game's list shows until
* the next zone).
* The game keeps running its list: its cursor (class +0x30, 0-based) moves xiv1ui's, Confirm / Esc work as before.
* While xiv1ui's count of a category differs from the game's (+0x40), the game's own list shows instead.
--]]

local bit     = require('bit');
local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local mem     = require('core.mem');
local store   = require('core.store');
local gamewin = require('core.gamewin');
local xi_now  = require('core.now');

local ki = {};

local DAT_ID = 0xD993;

-- { [heading name] = { ids in table order } }, or false when the table can't be read
local cats = nil;
local function load()
    if cats ~= nil then return cats; end
    cats = false;
    local path = require('core.maps').dat_file(DAT_ID);
    local f = path and io.open(path, 'rb');
    if not f then return cats; end
    local d = f:read('*a');
    f:close();
    local function raw32(at)               -- (0-based offset)
        local a, b, c, e = d:byte(at + 1, at + 4);
        return a + b * 256 + c * 65536 + e * 16777216;
    end
    -- (the entries are stored XOR 0xFF; the header isn't)
    local function u32(at) return bit.bxor(raw32(at), 0xFFFFFFFF) % 4294967296; end
    if #d < 0x40 or d:sub(1, 5) ~= 'd_msg' then return cats; end
    local size, count = raw32(0x20), raw32(0x28);
    if size < 0x48 or count < 1 or 0x40 + size * count > #d then return cats; end
    local out, pending = {}, {};
    for k = 0, count - 1 do
        local e = 0x40 + k * size;
        local id = u32(e + 0x3C);
        if id ~= 0 then
            pending[#pending + 1] = id;
        else
            -- a heading: its name is the first text in the entry after the two numbers
            local raw = d:sub(e + 0x45, e + 0x45 + 0x80);
            local name = {};
            for i = 1, #raw do
                local c = bit.bxor(raw:byte(i), 0xFF);
                if c == 0 and #name > 0 then break; end
                if c >= 0x20 and c < 0x7F then name[#name + 1] = string.char(c); end
            end
            local n = table.concat(name):match('^%-(.+)$');
            if n then out[n] = pending; end
            pending = {};
        end
    end
    cats = out;
    return cats;
end

-- key item flags by block (0x55): block -> { held = string of 64 bytes, seen = string of 64 bytes }
local flags = {};
function ki.packet(e)
    if e.id ~= 0x55 or e.data == nil or #e.data < 0x85 then return; end
    flags[e.data:byte(0x85)] = { held = e.data:sub(0x05, 0x44), seen = e.data:sub(0x45, 0x84) };
end

local function bit_of(s, id)
    local i = id % 512;
    local b = s:byte(math.floor(i / 8) + 1) or 0;
    return bit.band(b, bit.lshift(1, i % 8)) ~= 0;
end
local function has(id)
    local f = flags[math.floor(id / 512)];
    return f ~= nil and bit_of(f.held, id);
end
--- Does she have key item `id`? nil while the server hasn't said (no 0x55 for its block since xiv1ui loaded).
function ki.has(id)
    if flags[math.floor(id / 512)] == nil then return nil; end
    return has(id);
end
local function seen(id)
    local f = flags[math.floor(id / 512)];
    return f ~= nil and bit_of(f.seen, id);
end
-- examined just now (the server's flags catch up at the next zone)
local function mark_seen(id)
    local f = flags[math.floor(id / 512)];
    if f == nil or bit_of(f.seen, id) then return; end
    local i = id % 512;
    local at = math.floor(i / 8) + 1;
    f.seen = f.seen:sub(1, at - 1) .. string.char(bit.bor(f.seen:byte(at), bit.lshift(1, i % 8))) .. f.seen:sub(at + 1);
end

-- the open category's name (the row chosen on the category list), or nil when not a Key Items list
local function which()
    local cm = require('ui.cmdmenu');
    if store.data.cmd_menu == false or gamewin.window('evitem') == nil then return nil; end
    local _, f = require('core.native').focused();
    -- (and while its "Examine?" question is up)
    if f ~= 'evitem' and f ~= 'evitem01' then return nil; end
    if (cm.opener or {}).evitem == 'statcom2' then return nil; end
    local slot = gamewin.slot('evitem');
    local cls = slot and mem.u32(slot);
    local mode = cls and mem.u32(cls + 0x90);
    if mode ~= 2 and mode ~= 3 then return nil; end
    return (cm.last_choice or {}).evitem, cls, mode == 3;
end

local selected = nil;
--- The key item under the cursor while the list is up (or its "Examine?" question), or nil.
function ki.selected() return selected; end

local hider = gamewin.new();
local opened = nil;
function ki.release() hider:restore(); end

local ROW_H, SHOWN = 28, 12;
local view_first = 0;

function ki.render()
    local cat, cls, detail = which();
    local t = cat and load();
    local ids = t and t[cat];
    local held = {};
    if ids then
        for _, id in ipairs(ids) do
            if has(id) then held[#held + 1] = id; end
        end
    end
    local n = cls and mem.u32(cls + 0x40);
    local cur = cls and mem.u32(cls + 0x30);
    if ids == nil or n ~= #held or #held == 0 or cur == nil or cur >= #held then
        if hider:active() then hider:restore(); end
        opened, selected = nil, nil;
        return;
    end
    selected = held[cur + 1];
    hider:hide({ 'evitem' });
    if opened == nil then opened, view_first = xi_now(), 0; end
    local a = math.min(1, (xi_now() - opened) / 0.15);
    -- the view follows the cursor, scrolling only when it reaches an edge
    if cur < view_first then view_first = cur; end
    if cur >= view_first + SHOWN then view_first = cur - SHOWN + 1; end

    local rm = AshitaCore:GetResourceManager();
    if detail then
        -- an examined key item: its name and description (Esc: back to the list)
        mark_seen(selected);
        local W = 460;
        local d = ui.label('ki_detail', 'small', { font_height = 18, font_color = 0xFFE8E4D8, box_width = W - 56 });
        local dt = (rm:GetString('keyitems.descriptions', selected) or ''):gsub('\r', '')
            :gsub('([^\n])\n([^\n])', '%1 %2');
        if d.settings.text ~= dt then text.set(d, dt); end
        local _, dh = text.size(d);
        local H = 60 + dh + 40;
        local x, y = layout.anchor('topleft', W, H, 40, 60, 'keyitems');
        local col = draw.alpha(0xFFFFFFFF, a);
        local bw, bh = layout.size('win_body');
        draw.nine('win_body', x, y, W, H, 12, bw, bh, col);
        local tw, th = layout.size('win_title');
        draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th, col);
        draw.image('title_swash', x + 8, y + 4, { color = col });
        local title = ui.label('ki_title', 'name', { font_height = 22 });
        title:set_opacity(a);
        local nm = rm:GetString('keyitems.names', selected) or '?';
        text.draw(title, nm:sub(1, 1):upper() .. nm:sub(2), x + 40, y + 27, 'baseline');
        d:set_opacity(a);
        text.draw(d, dt, x + 28, y + 52);
        local hint = ui.label('ki_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
        hint:set_opacity(a);
        text.draw(hint, 'Esc / Back: return to the list', x + 24, y + H - 14, 'baseline');
        return;
    end
    local W = 460;
    local rows = math.min(SHOWN, #held);
    -- the selected key item's description, under the list
    local desc = ui.label('ki_desc', 'small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = W - 48 });
    -- (FFXI breaks its descriptions for its own narrow box: single breaks become spaces)
    local dtext = (rm:GetString('keyitems.descriptions', held[cur + 1]) or ''):gsub('\r', '')
        :gsub('([^\n])\n([^\n])', '%1 %2');
    if desc.settings.text ~= dtext then text.set(desc, dtext); end
    local _, dh = text.size(desc);
    local H = 52 + rows * ROW_H + math.max(60, dh + 30);
    local x, y = layout.anchor('topleft', W, H, 40, 60, 'keyitems');
    local col = draw.alpha(0xFFFFFFFF, a);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh, col);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th, col);
    draw.image('title_swash', x + 8, y + 4, { color = col });
    local title = ui.label('ki_title', 'name', { font_height = 22 });
    title:set_opacity(a);
    text.draw(title, cat, x + 40, y + 27, 'baseline');
    local cnt = ui.label('ki_count', 'small', { font_height = 16, font_color = 0xFFC8C4B8, font_alignment = text.align.Right });
    cnt:set_opacity(a);
    text.draw(cnt, string.format('%d-%d / %d', view_first + 1, view_first + rows, #held), x + W - 20, y + 25, 'baseline');

    local sw, sh = layout.size('row_sel');
    for r = 1, rows do
        local i = view_first + r;
        local id = held[i];
        local ry = y + 44 + (r - 1) * ROW_H;
        local sel = (i - 1 == cur);
        if sel then
            draw.nine('row_sel', x + 22, ry, W - 44, ROW_H - 2, 6, sw, sh, col);
            draw.image('cursor_gold', x + 2, ry + 1, { color = col });
        end
        local o = ui.label('ki_row' .. r, 'small', { font_height = 18 });
        local c = sel and 0xFFFFFFFF or 0xFFD8D4C8;
        if o.settings.font_color ~= c then o:set_font_color(c); end
        o:set_opacity(a);
        local name = rm:GetString('keyitems.names', id) or '?';
        text.draw(o, name:sub(1, 1):upper() .. name:sub(2), x + 34, ry + ROW_H - 8, 'baseline');
        -- not looked at yet
        if not seen(id) then
            local nw = ui.label('ki_new' .. r, 'small', { font_height = 14, font_color = 0xFFF0C060,
                                                          font_alignment = text.align.Right });
            nw:set_opacity(a);
            text.draw(nw, 'New', x + W - 30, ry + ROW_H - 9, 'baseline');
        end
    end
    local dy = y + 52 + rows * ROW_H;
    draw.rect(x + 20, dy - 2, W - 40, 1, draw.alpha(0x60C8A860, a));
    desc:set_opacity(a);
    text.draw(desc, dtext, x + 24, dy + 10);
end

return ki;
