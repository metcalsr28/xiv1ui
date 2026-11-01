--[[
* xiv1ui - the Equipment screen (Commands » Equipment). While the game's equipment window ("menu    equip") is
* open, xiv1ui hides it and draws a larger 1.0-style panel: the sixteen slots as a 4×4 grid of item icons (in the
* game's own arrangement), the selected slot lit with its item's name, and the slot names under each icon. The game
* still runs the screen: moving, choosing a slot and picking gear work as before.
*
* Picking gear for a slot (focus on the game's item list, "menu    inventor"): the grid stays, the game's list, item
* info and gil windows stay hidden, and a picker opens beside the grid: the items that fit the slot (from the bags the
* game lists: inventory and wardrobes), the equipped one in green, the one the game's cursor is on lit, with its
* level, jobs and description below. The game's cursor item is read from its item info window (class object +0x24
* item id, +0x26 bag index), so the lit row always matches what Enter will equip. The game's "Storage Options" row
* (cursor on the list header) is shown as the picker's header; choosing it opens the game's own options window.
--]]

local mem    = require('core.mem');
local native = require('core.native');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local ui     = require('core.ui');
local store  = require('core.store');
local ffi    = require('ffi');

local panel = {};

-- help text (start) -> { equipment slot id, short label }
local SLOTS = {
    { 'Main Weapon', 0, 'Main' }, { 'Sub-weapon', 1, 'Sub' }, { 'Ranged Weapon', 2, 'Ranged' }, { 'Ammunition', 3, 'Ammo' },
    { 'Head', 4, 'Head' }, { 'Neck', 9, 'Neck' }, { 'Left Ear', 11, 'Ear' }, { 'Right Ear', 12, 'Ear' },
    { 'Body', 5, 'Body' }, { 'Hands', 6, 'Hands' }, { 'Left hand ring', 13, 'Ring' }, { 'Right hand ring', 14, 'Ring' },
    { 'Back', 15, 'Back' }, { 'Waist', 10, 'Waist' }, { 'Legs', 7, 'Legs' }, { 'Feet', 8, 'Feet' },
};

local slot_ptr = nil;
local hidden = nil;          -- { obj, b69, b6a, b78 }
local extra = {};            -- other windows hidden while the slot grid has focus: name -> { obj, b69, b6a }
local EXTRAS = { 'inventor', 'iteminfo', 'money', 'helpwind', 'titlewin' };
local FINGER = { inventor = true };     -- windows whose cursor finger (+0x78) is hidden as well
local extra_slots = {};
local function extra_window(name)
    extra_slots[name] = require('core.gamewin').slot(name) or false;
    return extra_slots[name] and mem.chain(extra_slots[name], 0, 8) or nil;
end
local scaled = {};           -- row -> obj

local function window()
    slot_ptr = require('core.gamewin').slot('equip') or false;
    return slot_ptr and mem.chain(slot_ptr, 0, 8) or nil;
end

local function is_row(r, obj) return mem.ok(r, 0x70) and mem.u32(r + 0x58) == r and mem.u32(r + 0x5C) == obj; end

local function rows_of(obj)
    local out, n = {}, mem.u32(obj + 0x14);
    while n and n ~= 0 and #out < 80 and mem.ok(n, 0x14) do
        local r = mem.u32(n + 0x10);
        if r and is_row(r, obj) then out[#out + 1] = r; end
        n = mem.u32(n);
    end
    return out;
end

local help_cache = {};
local function help_of(r)
    local e = mem.u32(r + 0x0C);
    if not e then return ''; end
    local h = help_cache[e];
    if h == nil then
        local p = mem.u32(e + 8);
        h = (p and mem.ok(p, 80)) and (ashita.memory.read_string(p, 80) or ''):match('^[^%z]*') or '';
        help_cache[e] = h;
    end
    return h;
end

local function hide(obj, rows)
    if not hidden or hidden[1] ~= obj then
        local a, b, f = mem.u8(obj + 0x69), mem.u8(obj + 0x6A), mem.u8(obj + 0x78);
        if a == nil or a > 1 or b == nil or b > 1 or f == nil or f > 1 then return false; end
        hidden = { obj, a, b, f };
    end
    mem.w8(obj + 0x69, 0); mem.w8(obj + 0x6A, 0); mem.w8(obj + 0x78, 0);
    for _, r in ipairs(rows) do
        if scaled[r] ~= obj then
            local sc = ffi.cast('float*', r + 0x1C);
            if sc[0] == 1 and sc[1] == 1 then sc[0], sc[1] = 0, 0; scaled[r] = obj; end
        end
    end
    return true;
end

local function hide_extras()
    for _, name in ipairs(EXTRAS) do
        local o = extra_window(name);
        if o then
            local e = extra[name];
            if not e or e[1] ~= o then
                local a, b, f = mem.u8(o + 0x69), mem.u8(o + 0x6A), mem.u8(o + 0x78);
                if a and a <= 1 and b and b <= 1 and f and f <= 1 then e = { o, a, b, f }; extra[name] = e; end
            end
            if e and e[1] == o then
                mem.w8(o + 0x69, 0); mem.w8(o + 0x6A, 0);
                if FINGER[name] then mem.w8(o + 0x78, 0); end
                for _, r in ipairs(rows_of(o)) do
                    if scaled[r] ~= o then
                        local sc = ffi.cast('float*', r + 0x1C);
                        if sc[0] == 1 and sc[1] == 1 then sc[0], sc[1] = 0, 0; scaled[r] = o; end
                    end
                end
            end
        end
    end
end

local function restore()
    for name, e in pairs(extra) do
        if extra_window(name) == e[1] then
            if mem.u8(e[1] + 0x69) == 0 then mem.w8(e[1] + 0x69, e[2]); end
            if mem.u8(e[1] + 0x6A) == 0 then mem.w8(e[1] + 0x6A, e[3]); end
            if FINGER[name] and mem.u8(e[1] + 0x78) == 0 then mem.w8(e[1] + 0x78, e[4]); end
        end
    end
    extra = {};
    for r, obj in pairs(scaled) do
        if is_row(r, obj) then
            local sc = ffi.cast('float*', r + 0x1C);
            if sc[0] == 0 and sc[1] == 0 then sc[0], sc[1] = 1, 1; end
        end
    end
    scaled = {};
    if hidden and window() == hidden[1] then
        local o = hidden[1];
        if mem.u8(o + 0x69) == 0 then mem.w8(o + 0x69, hidden[2]); end
        if mem.u8(o + 0x6A) == 0 then mem.w8(o + 0x6A, hidden[3]); end
        if mem.u8(o + 0x78) == 0 then mem.w8(o + 0x78, hidden[4]); end
    end
    hidden = nil;
end

function panel.release() restore(); end

local function equipped(slot_id)
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    local e = inv:GetEquippedItem(slot_id);
    if e == nil or e.Index == 0 then return nil; end
    local bag, idx = bit.rshift(bit.band(e.Index, 0xFF00), 8), bit.band(e.Index, 0xFF);
    local it = inv:GetContainerItem(bag, idx);
    if it == nil or it.Id == 0 then return nil; end
    return it.Id, it;
end

-- The item the game's list cursor is on: its item info window's class object holds the item id (+0x24) and the
-- item's index in its bag (+0x26); 0 when the cursor is on the list header ("Storage Options").
local info_slot = nil;
local function cursor_item()
    info_slot = require('core.gamewin').slot('iteminfo') or false;
    if not info_slot then return nil; end
    local cls = mem.u32(info_slot);
    if cls == nil or not mem.ok(cls + 0x24, 4) then return nil; end
    local id = mem.u16(cls + 0x24);
    if id == nil or id == 0 then return nil; end
    return id, mem.u8(cls + 0x26);
end

-- Bags the game's equipment list can show, in the order of its Storage Options window (the game's own table, read
-- next to the inventor menu's strings, is the same list): inventory and the eight wardrobes. It shows one at a time.
local BAGS = { 0, 8, 10, 11, 12, 13, 14, 15, 16 };
local BAG_NAMES = { [0] = 'Inventory', [8] = 'Mog Wardrobe', [10] = 'Mog Wardrobe 2', [11] = 'Mog Wardrobe 3', [12] = 'Mog Wardrobe 4',
                    [13] = 'Mog Wardrobe 5', [14] = 'Mog Wardrobe 6', [15] = 'Mog Wardrobe 7', [16] = 'Mog Wardrobe 8' };
local shown_bag = 0;         -- the bag the game's list shows
local pending_bag = nil;     -- the bag under the Storage Options cursor when that window was last focused

--- The items in `bag` that fit equipment slot `slot_id`, in bag order: the game lists them all, greying out the
-- ones the current job can't use (nojob), so the rows match its cursor.
local function candidates(slot_id, bag)
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    local rm = AshitaCore:GetResourceManager();
    local pl = AshitaCore:GetMemoryManager():GetPlayer();
    local job, lvl = pl:GetMainJob(), pl:GetMainJobLevel();
    local out = {};
    do
        local n = inv:GetContainerCountMax(bag) or 0;
        for i = 1, math.min(n, 80) do
            local it = inv:GetContainerItem(bag, i);
            if it and it.Id ~= 0 and it.Id ~= 65535 then
                local r = rm:GetItemById(it.Id);
                if r and bit.band(r.Slots or 0, bit.lshift(1, slot_id)) ~= 0 then
                    out[#out + 1] = { id = it.Id, bag = bag, index = i, res = r, equipped = (it.Flags == 5),
                                      low = (r.Level or 0) > lvl,
                                      nojob = bit.band(r.Jobs or 0, bit.lshift(1, job)) == 0 };
                end
            end
        end
    end
    return out;
end

local inventor_slot = nil;

local SLOT_NAMES = { [0] = 'Main Weapon', 'Sub-weapon', 'Ranged Weapon', 'Ammunition', 'Head', 'Body', 'Hands',
    'Legs', 'Feet', 'Neck', 'Waist', 'Left Ear', 'Right Ear', 'Left Ring', 'Right Ring', 'Back' };
local PICK_ROWS, PICK_ROW_H = 8, 40;
local desc_obj = nil;

local picker_dh = 0;          -- the description's height last frame (the window grows to hold it)
local function render_picker(x, y, h, slot_id)
    local W = 440;
    h = math.max(h, 44 + 32 + PICK_ROWS * PICK_ROW_H + 6 + 10 + picker_dh + 18);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, h, 12, bw, bh);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th);
    local title = ui.label('eqp_title', 'name', { font_height = 22 });
    text.draw(title, SLOT_NAMES[slot_id] or 'Equipment', x + 20, y + 27, 'baseline');
    local bagl = ui.label('eqp_bag', 'small', { font_height = 16, font_color = 0xFFC8C4B8, font_alignment = text.align.Right });
    text.draw(bagl, BAG_NAMES[shown_bag] or '', x + W - 20, y + 26, 'baseline');

    local cid, cidx = cursor_item();
    -- which bag is shown: the one holding the item under the game's cursor; on the header, the last one chosen in
    -- Storage Options if the game's item count agrees (the inventor class keeps rows incl. the header at +0x20)
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    if cid then
        for _, b in ipairs(BAGS) do
            local it = inv:GetContainerItem(b, cidx or 0);
            if it and it.Id == cid then shown_bag = b; break; end
        end
        pending_bag = nil;
    elseif pending_bag then
        local cls = inventor_slot and mem.u32(inventor_slot);
        local rows = cls and mem.u16(cls + 0x20);
        if rows and rows - 1 == #candidates(slot_id, pending_bag) then shown_bag = pending_bag; end
        pending_bag = nil;
    end
    local list = candidates(slot_id, shown_bag);
    -- (no item under the cursor to tell: a bag whose count is the game's)
    local lcls = inventor_slot and mem.u32(inventor_slot);
    local lcount = lcls and mem.u16(lcls + 0x20);
    if cid == nil and lcount and lcount - 1 ~= #list then
        for _, b in ipairs(BAGS) do
            local l = candidates(slot_id, b);
            if #l == lcount - 1 then shown_bag, list = b, l; break; end
        end
    end
    -- in the game's order, which isn't the bag's (ui/itempanel.lua in_game_order)
    list = require('ui.itempanel').in_game_order(lcls, list);
    local at = nil;
    for i, c in ipairs(list) do
        if c.id == cid and (cidx == nil or c.index == cidx) then at = i; end
    end
    -- The list's own cursor wins when its row count agrees with ours: the row on screen (+0x24, 1-based, the header
    -- is row 1) plus the scroll (+0x1A); the count, header included, is at +0x20. It doesn't depend on the item info
    -- window, which isn't there on every client (the lit row stuck on the header).
    local lrow, ltop = lcls and mem.u16(lcls + 0x24), lcls and mem.u16(lcls + 0x1A);
    if lrow and ltop and lcount and lcount - 1 == #list and lrow >= 1 then
        local n = lrow + ltop - 1;          -- 0: the header
        if cid == nil or (list[n] and list[n].id == cid) or at == nil then
            at = (n >= 1 and n <= #list) and n or nil;
        end
    elseif cid and at == nil then     -- not one we listed (another bag): show it anyway, so the lit row is right
        local r = AshitaCore:GetResourceManager():GetItemById(cid);
        if r then list[#list + 1] = { id = cid, res = r, equipped = false }; at = #list; end
    end
    panel.lit = { list = list, at = at };     -- (for dev probes)
    -- the header row: "Storage Options" (the game's cursor is on it when no item is under it)
    local hy = y + 44;
    local sw, sh = layout.size('row_sel');
    local opt = ui.label('eqp_opt', 'small', { font_height = 16 });
    if at == nil then
        draw.nine('row_sel', x + 22, hy, W - 34, 26, 6, sw, sh);
        draw.image('cursor_gold', x + 2, hy + 2);
    end
    local oc = at == nil and 0xFFFFFFFF or 0xFFB8C0D8;
    if opt.settings.font_color ~= oc then opt:set_font_color(oc); end
    text.draw(opt, 'Storage Options  ›', x + 34, hy + 19, 'baseline');

    if #list == 0 then
        local none = ui.label('eqp_none', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
        text.draw(none, 'Nothing you can wear here.', x + 34, hy + 64, 'baseline');
    end
    local first = 0;
    if at and at > PICK_ROWS then first = at - PICK_ROWS; end
    for r = 1, math.min(PICK_ROWS, #list - first) do
        local i = r + first;
        local c = list[i];
        local ry = hy + 32 + (r - 1) * PICK_ROW_H;
        local sel = (i == at);
        if sel then
            draw.nine('row_sel', x + 22, ry, W - 34, PICK_ROW_H - 4, 6, sw, sh);
            draw.image('cursor_gold', x + 2, ry + (PICK_ROW_H - 26) / 2);
        end
        draw.entry(draw.item_icon(c.id), x + 30, ry + 2, 32, 32, c.nojob and 0x90FFFFFF or nil);
        local o = ui.label('eqp_r' .. r, 'small', { font_height = 18 });
        local col = c.equipped and 0xFF9BE08C or ((c.low or c.nojob) and 0xFF7C786E or (sel and 0xFFFFFFFF or 0xFFE8E4D8));
        if o.settings.font_color ~= col then o:set_font_color(col); end
        text.draw(o, c.res.Name[1] or '?', x + 72, ry + 25, 'baseline');
        local lv = ui.label('eqp_l' .. r, 'small', { font_height = 15, font_alignment = text.align.Right });
        local lc = c.low and 0xFFFF9080 or 0xFFC8C4B8;
        if lv.settings.font_color ~= lc then lv:set_font_color(lc); end
        text.draw(lv, (c.res.Level or 0) > 0 and ('Lv ' .. c.res.Level) or '', x + W - 20, ry + 25, 'baseline');
    end
    if #list > PICK_ROWS then
        local more = ui.label('eqp_more', 'small', { font_height = 14, font_color = 0xFFB8C0D8, font_alignment = text.align.Right });
        text.draw(more, string.format('%d / %d', at or 0, #list), x + W - 20, hy + 19, 'baseline');
    end

    -- the lit item's description
    local c = at and list[at];
    local dy = hy + 32 + PICK_ROWS * PICK_ROW_H + 6;
    draw.image('name_rule', x + 16, dy, { scale = { (W - 32) / 300, 1 } });
    if c then
        -- level and jobs, as the game's item info shows them, the description and the item's augments
        local d = require('ui.itempanel').describe(c.res,
            AshitaCore:GetMemoryManager():GetInventory():GetContainerItem(c.bag, c.index));
        desc_obj = desc_obj or text.new('small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = W - 44 });
        if desc_obj.settings.text ~= d then text.set(desc_obj, d); end
        picker_dh = select(2, text.size(desc_obj));
        text.render(desc_obj, x + 22, dy + 10);
    end
end

local CELL, GAP = 74, 10;

function panel.render()
    if store.data.cmd_menu == false then if hidden then restore(); end return; end
    local obj = window();
    if obj == nil then if hidden or next(scaled) then restore(); end return; end
    local rows = rows_of(obj);
    -- cells: the rows that carry a slot help text, in the game's grid order (y, then x)
    local cells = {};
    local cur = mem.u32(obj + 0x08);
    for _, r in ipairs(rows) do
        local h = help_of(r);
        for _, sdef in ipairs(SLOTS) do
            if h:sub(1, #sdef[1]) == sdef[1] then
                cells[#cells + 1] = { x = mem.u16(r + 0x2A) or 0, y = mem.u16(r + 0x2C) or 0, slot = sdef[2],
                                      label = sdef[3], sel = (r == cur) };
                break;
            end
        end
    end
    if #cells ~= 16 then if hidden then restore(); end return; end     -- not the layout we know: leave it alone
    -- choosing gear for a slot (focus on the game's item list): the picker opens beside the grid. Anything else
    -- (e.g. the Storage Options window): the game's screens are needed, step aside.
    local fobj, fname = native.focused();
    inventor_slot = require('core.gamewin').slot('inventor') or false;
    -- the Storage Options window (which bag the list shows) is drawn by xiv1ui's menus (ui/cmdmenu.lua)
    if fname == 'mnstorag' then
        local n = mem.u32(fobj + 0x08);
        n = n and mem.ok(n, 0x40) and mem.u16(n + 0x3A);
        if n and BAGS[n] then pending_bag = BAGS[n]; end
    end
    local picking = (fname == 'inventor' or fname == 'mnstorag');
    if fobj ~= obj and not picking then if hidden or next(scaled) then restore(); end return; end
    if not hide(obj, rows) then return; end
    hide_extras();
    table.sort(cells, function (a, b) if a.y ~= b.y then return a.y < b.y; end return a.x < b.x; end);

    local W = 4 * CELL + 3 * GAP + 48;
    -- the selected slot's item: its name, and under it what FFXI's item box would say (level, jobs, stats)
    local sel_item, sel_bag_item = nil, nil;
    for _, c in ipairs(cells) do
        if c.sel then
            local id, it = equipped(c.slot);
            sel_item = id and AshitaCore:GetResourceManager():GetItemById(id) or false;
            sel_bag_item = it;
        end
    end
    local desc = ui.label('eq_desc', 'small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = W - 52 });
    local d = (sel_item and not picking) and require('ui.itempanel').describe(sel_item, sel_bag_item) or '';
    if desc.settings.text ~= d then text.set(desc, d); end
    local dh = d ~= '' and select(2, text.size(desc)) + 10 or 0;
    local H = 46 + 4 * (CELL + 22) + 70 + dh;
    local x, y = layout.anchor('topleft', W, H, 24, 40, 'equippanel');
    layout.bounds('equippanel', x, y, W, H);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th);
    draw.image('title_swash', x + 8, y + 4);
    local title = ui.label('eq_title', 'name', { font_height = 22 });
    text.draw(title, 'Equipment', x + 40, y + 27, 'baseline');

    local sel_name, sel_slot = nil, nil;
    local sw, sh = layout.size('slot_square');
    for i, c in ipairs(cells) do
        local col, rr = (i - 1) % 4, math.floor((i - 1) / 4);
        local cx = x + 24 + col * (CELL + GAP);
        local cy = y + 50 + rr * (CELL + 22);
        draw.image('slot_shadow', cx + (CELL - 60) / 2, cy + (CELL - 60) / 2);
        draw.image('slot_well', cx + (CELL - 44) / 2, cy + (CELL - 44) / 2);
        local id = equipped(c.slot);
        if id then draw.entry(draw.item_icon(id), cx + (CELL - 40) / 2, cy + (CELL - 40) / 2, 40, 40); end
        draw.image(c.sel and 'slot_ring_gold' or 'slot_ring', cx + (CELL - 60) / 2, cy + (CELL - 60) / 2);
        local lb = ui.label('eq_l' .. i, 'small', { font_height = 15, font_alignment = text.align.Center });
        local lc = c.sel and 0xFFF4E070 or 0xFFC8C4B8;
        if lb.settings.font_color ~= lc then lb:set_font_color(lc); end
        text.draw(lb, c.label, cx + CELL / 2, cy + CELL + 14, 'baseline');
        if c.sel then
            sel_slot = c.slot;
            local it = id and AshitaCore:GetResourceManager():GetItemById(id);
            sel_name = it and it.Name[1] or '(nothing equipped)';
        end
    end
    if sel_name then
        local n = ui.label('eq_sel', 'name', { font_height = 21 });
        text.draw(n, sel_name, x + 26, y + H - 26 - dh, 'baseline');
    end
    if dh > 0 then text.draw(desc, desc.settings.text, x + 26, y + H - 14 - dh); end
    if picking and sel_slot then render_picker(x + W + 8, y, H, sel_slot); end
end

return panel;
