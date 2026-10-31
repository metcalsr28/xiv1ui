--[[
* xiv1ui - Gear window (reference §21): stats on the left, a paper doll of square slot tiles in the centre (no
* character model, as in 1.0), and on the right the candidates for the selected slot from your bags, with the
* equipped item marked. Arrows move around the doll; Enter (or click) moves into the list; Enter equips through the
* game's own /equip; Esc goes back. Changing the main hand changes job only through FFXI's usual rules.
--]]

local ui   = require('core.ui');
local draw = require('core.draw');
local text = require('core.text');

local M = {};

-- FFXI equipment slots, laid out as a 4x4 doll: weapons / head-neck-ears / body-hands-rings / back-waist-legs-feet
local SLOTS = {
    { id = 0,  name = 'main',  label = 'Main Hand' }, { id = 1,  name = 'sub',   label = 'Off Hand' },
    { id = 2,  name = 'range', label = 'Ranged' },    { id = 3,  name = 'ammo',  label = 'Ammo' },
    { id = 4,  name = 'head',  label = 'Head' },      { id = 9,  name = 'neck',  label = 'Neck' },
    { id = 11, name = 'ear1',  label = 'Left Ear' },  { id = 12, name = 'ear2',  label = 'Right Ear' },
    { id = 5,  name = 'body',  label = 'Body' },      { id = 6,  name = 'hands', label = 'Hands' },
    { id = 13, name = 'ring1', label = 'Left Ring' }, { id = 14, name = 'ring2', label = 'Right Ring' },
    { id = 15, name = 'back',  label = 'Back' },      { id = 10, name = 'waist', label = 'Waist' },
    { id = 7,  name = 'legs',  label = 'Legs' },      { id = 8,  name = 'feet',  label = 'Feet' },
};
local BAGS = { 0, 8, 10, 11, 12, 13, 14, 15, 16 };   -- inventory and wardrobes (equippable from)
local STAT_NAMES = { 'STR', 'DEX', 'VIT', 'AGI', 'INT', 'MND', 'CHR' };
local ROWS = 13;

local win = { id = 'gear', title = 'Gear', w = 900, h = 520, slot = 1, focus = 'doll', sel = 1, first = 0, tiles = {}, rows = {} };

local function equipped(slot_id)
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    local e = inv:GetEquippedItem(slot_id);
    if e == nil or e.Index == 0 then return nil; end
    local bag, idx = bit.rshift(bit.band(e.Index, 0xFF00), 8), bit.band(e.Index, 0xFF);
    local it = inv:GetContainerItem(bag, idx);
    if it == nil or it.Id == 0 then return nil; end
    return it.Id;
end

local function candidates(slot)
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    local r = AshitaCore:GetResourceManager();
    local player = AshitaCore:GetMemoryManager():GetPlayer();
    local job, lvl = player:GetMainJob(), player:GetMainJobLevel();
    local out, seen = {}, {};
    local eq = equipped(slot.id);
    for _, bag in ipairs(BAGS) do
        local max = inv:GetContainerCountMax(bag) or 0;
        for i = 1, max do
            local e = inv:GetContainerItem(bag, i);
            if e and e.Id ~= 0 and e.Id ~= 65535 and not seen[e.Id] then
                local it = r:GetItemById(e.Id);
                if it and it.Slots and bit.band(it.Slots, bit.lshift(1, slot.id)) ~= 0 then
                    seen[e.Id] = true;
                    local ok = bit.band(it.Jobs or 0, bit.lshift(1, job)) ~= 0 and (it.Level or 0) <= lvl;
                    out[#out + 1] = { id = e.Id, name = it.Name[1], res = it, usable = ok, equipped = (e.Id == eq) };
                end
            end
        end
    end
    table.sort(out, function (a, b)
        if a.equipped ~= b.equipped then return a.equipped; end
        return a.name < b.name;
    end);
    return out;
end

local function refresh(w)
    w.items = candidates(SLOTS[w.slot]);
    w.sel = 1; w.first = 0;
end

win.on_open = function (w) refresh(w); end

win.draw = function (w, x, y)
    local p = AshitaCore:GetMemoryManager():GetPlayer();
    -- left: stats
    ui.header('gearstats', 'Attributes', x + 24, y + 62, 180);
    local sy = y + 90;
    for i, n in ipairs(STAT_NAMES) do
        local base, mod = p:GetStat(i - 1) or 0, p:GetStatModifier(i - 1) or 0;
        local o = ui.label('gst' .. i, 'small', { font_height = 16 });
        text.draw(o, n, x + 30, sy, 'baseline');
        local v = ui.label('gsv' .. i, 'small', { font_height = 16, font_alignment = text.align.Right });
        text.draw(v, mod ~= 0 and string.format('%d  +%d', base, mod) or tostring(base), x + 190, sy, 'baseline');
        sy = sy + 22;
    end
    for _, pair in ipairs({ { 'Attack', p:GetAttack() }, { 'Defense', p:GetDefense() } }) do
        local o = ui.label('gsa' .. pair[1], 'small', { font_height = 16, font_color = 0xFFF0DCA0 });
        text.draw(o, pair[1], x + 30, sy, 'baseline');
        local v = ui.label('gsav' .. pair[1], 'small', { font_height = 16, font_alignment = text.align.Right });
        text.draw(v, tostring(pair[2] or 0), x + 190, sy, 'baseline');
        sy = sy + 22;
    end

    -- centre: paper doll
    local dx, dy = x + 230, y + 70;
    w.tiles = {};
    for i, s in ipairs(SLOTS) do
        local c, r = (i - 1) % 4, math.floor((i - 1) / 4);
        local tx, ty = dx + c * 54, dy + r * 70;
        w.tiles[i] = { tx, ty, 44, 44 };
        if i == w.slot then
            local rw, rh = require('core.layout').size('row_sel');
            draw.nine('row_sel', tx - 4, ty - 4, 52, 52, 6, rw, rh, w.focus == 'doll' and 0xFFFFFFFF or 0x90FFFFFF);
            if w.focus == 'doll' then draw.image('cursor_gold', tx - 30, ty + 12); end
        end
        draw.image('slot_square', tx, ty);
        local id = equipped(s.id);
        if id then draw.entry(draw.item_icon(id), tx + 6, ty + 6, 32, 32); end
        local o = ui.label('gslot' .. i, 'slotkey', { font_height = 12, font_alignment = text.align.Center });
        text.draw(o, s.label, tx + 22, ty + 60, 'baseline');
    end

    -- right: candidates for the selected slot
    local lx = x + 470;
    ui.header('gearlist', SLOTS[w.slot].label, lx, y + 62, 400);
    local items = {};
    for i, c in ipairs(w.items or {}) do
        items[i] = { label = c.name, indent = 26, right = c.equipped and 'Equipped' or nil,
                     color = c.equipped and 0xFF9BE08C or (c.usable and 0xFFF4F0E6 or 0xFFA07070) };
    end
    if #items == 0 then items[1] = { label = '(nothing for this slot)', disabled = true }; end
    if w.sel > w.first + ROWS then w.first = w.sel - ROWS; end
    if w.sel <= w.first then w.first = w.sel - 1; end
    w.rows = ui.list(w, 'gear', items, w.sel, lx + 10, y + 76, 380, 26, ROWS, w.first, w.focus == 'list' and ui.top() == w);
    for r = 1, math.min(ROWS, #(w.items or {}) - w.first) do
        draw.entry(draw.item_icon(w.items[r + w.first].id), lx + 16, y + 78 + (r - 1) * 26, 20, 20);
    end
    local hint = ui.label('gearhint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
    text.draw(hint, 'Arrows: choose a slot   Enter: choose gear   Enter again: equip   Esc: back', x + 230, y + w.h - 18, 'baseline');
end

local function equip(w)
    local c = (w.items or {})[w.sel];
    if not c then return; end
    AshitaCore:GetChatManager():QueueCommand(1, string.format('/equip %s "%s"', SLOTS[w.slot].name, c.name));
    w.focus = 'doll';
end

win.key = function (w, vk)
    if w.focus == 'doll' then
        local c, r = (w.slot - 1) % 4, math.floor((w.slot - 1) / 4);
        if vk == ui.VK.LEFT then c = (c - 1) % 4; elseif vk == ui.VK.RIGHT then c = (c + 1) % 4;
        elseif vk == ui.VK.UP then r = (r - 1) % 4; elseif vk == ui.VK.DOWN then r = (r + 1) % 4;
        elseif vk == ui.VK.RETURN then w.focus = 'list'; return true;
        elseif vk == ui.VK.ESCAPE then return false; end
        local ns = r * 4 + c + 1;
        if ns ~= w.slot then w.slot = ns; refresh(w); end
    else
        local n = #(w.items or {});
        if vk == ui.VK.UP then w.sel = math.max(1, w.sel - 1);
        elseif vk == ui.VK.DOWN then w.sel = math.min(math.max(1, n), w.sel + 1);
        elseif vk == ui.VK.RETURN then equip(w);
        elseif vk == ui.VK.ESCAPE or vk == ui.VK.LEFT then w.focus = 'doll'; end
    end
    return true;
end

win.click = function (w, mx, my)
    for i, t in ipairs(w.tiles) do
        if ui.hit(t, mx, my) then w.slot = i; w.focus = 'list'; refresh(w); return; end
    end
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then
            if w.sel == r[5] and w.focus == 'list' then equip(w); else w.sel = r[5]; w.focus = 'list'; end
            return;
        end
    end
end

function M.open() ui.open(win); end

return M;
