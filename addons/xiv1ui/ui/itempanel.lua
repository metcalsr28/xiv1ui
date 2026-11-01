--[[
* xiv1ui - the Items screen (Commands » Items) in xiv1ui's style. The game keeps running its item list
* ("menu    inventor"): moving, using, sorting and dropping work exactly as before. xiv1ui hides the list, the item
* info box and the sort hint, and draws a larger window: the bag's items with their icons and counts in bag order,
* the one under the game's cursor lit (read from the game's item info, so it always matches), and its description.
* Equipment's gear picker uses the same list window; that case belongs to ui/equippanel.lua.
* A shop's Sell list ("menu    shop", with the gil box "money") is the same bag in the same order: drawn here too,
* titled with the shopkeeper's name and the gil she has.
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local store   = require('core.store');
local native  = require('core.native');
local gamewin = require('core.gamewin');
local mem     = require('core.mem');

local panel = {};

local hider = gamewin.new();
local HIDE = { 'inventor', 'iteminfo', 'itmsort2', 'helpwind', 'titlewin' };
local HIDE_SET = {};
for _, n in ipairs(HIDE) do HIDE_SET[n] = true; end
HIDE_SET.iuse = true;
local SELL_HIDE = { 'shop', 'money', 'iteminfo', 'itemctrl', 'helpwind', 'titlewin' };
-- the shopkeeper's offers (packet 0x3D, the answer to an appraisal: u32 price at 0x04, bag slot at 0x08), by slot
local offers = {};
-- the shopkeeper's wares (packet 0x3C: u16 first slot at 0x04, then 12-byte entries from 0x08: u32 price,
-- u16 item id, u8 shop slot), by shop slot; a new shop's first packet starts the list again
local goods = {};
local function u32(d, o) return d:byte(o + 1) + d:byte(o + 2) * 256 + d:byte(o + 3) * 65536 + d:byte(o + 4) * 16777216; end
function panel.packet(e)
    if e.id == 0x3C and e.data and #e.data >= 0x14 then
        local d = e.data;
        if d:byte(5) + d:byte(6) * 256 == 0 then goods = {}; end
        for o = 0x08, #d - 12, 12 do
            local id = d:byte(o + 5) + d:byte(o + 6) * 256;
            if id ~= 0 then goods[#goods + 1] = { price = u32(d, o), id = id, slot = d:byte(o + 7) }; end
        end
        return;
    end
    if e.id ~= 0x3D or e.data == nil or #e.data < 0x0A then return; end
    local d = e.data;
    local price = d:byte(5) + d:byte(6) * 256 + d:byte(7) * 65536 + d:byte(8) * 16777216;
    offers = { [d:byte(9)] = price };      -- (only the latest appraisal: an old one for this slot is stale)
end

-- the shop's list is showing her own bag (Shop » Sell), not the shopkeeper's goods
-- (Sell was the choice, or, e.g. after a reload, the item under the cursor is the one in her bag at that slot)
-- Shop » Buy: the shop window listing the shopkeeper's wares (the item under the cursor is one of them)
-- Bazaar » Set Prices opens the same shop window over her own bag: not a shop visit
local function bazaar() return require('ui.cmdmenu').opener.shop == 'bazaar'; end

local function buying(fname)
    if (fname ~= 'shop' and fname ~= 'itemctrl' and fname ~= 'shopbuy') or gamewin.window('shop') == nil then return false; end
    if bazaar() then return false; end
    if #goods == 0 then return false; end
    if require('ui.cmdmenu').last_choice.shopmain == 'Buy' then return true; end
    local id = gamewin.cursor_item();
    for _, g in ipairs(goods) do if g.id == id then return true; end end
    return false;
end

-- the shopkeeper: the nearest NPC (the one she's talking to stands within a few yalms), looked up once per visit
local shopkeeper = nil;
local last_gil, gain = nil, nil;   -- (the sale flash)
local function nearest_npc()
    local ent = AshitaCore:GetMemoryManager():GetEntity();
    local me = AshitaCore:GetMemoryManager():GetParty():GetMemberTargetIndex(0);
    local best, bd = nil, 7;
    local mz = ent:GetLocalPositionZ(me) or 0;
    for i = 1, 1023 do
        -- (on her floor: a shop can have a house right above it)
        if i ~= me and bit.band(ent:GetRenderFlags0(i) or 0, 0x200) ~= 0 and (ent:GetSpawnFlags(i) or 0) == 2
                and math.abs((ent:GetLocalPositionZ(i) or 1e9) - mz) < 3 then
            local d = math.sqrt(ent:GetDistance(i) or 1e9);
            local n = ent:GetName(i);
            if d < bd and n and n ~= '' then best, bd = n, d; end
        end
    end
    return best;
end

local function selling(fname)
    -- (the quantity box, itemctrl, and the Sell / Cancel question, shopsell, belong to the list while it's up)
    if (fname ~= 'shop' and fname ~= 'itemctrl' and fname ~= 'shopsell') or gamewin.window('shop') == nil then
        return false;
    end
    if bazaar() then return false; end
    local last = require('ui.cmdmenu').last_choice.shopmain;
    if last == 'Sell' then return true; end
    if last == 'Buy' then return false; end
    -- (not seen which was chosen, e.g. after a reload: the cursor is on something that isn't among the wares)
    local id = gamewin.cursor_item();
    if id == nil then return false; end
    for _, g in ipairs(goods) do if g.id == id then return false; end end
    return true;
end

local BAGS = { 0, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 1, 2, 4, 9 };
local BAG_NAMES = { [0] = 'Inventory', [1] = 'Mog Safe', [2] = 'Storage', [4] = 'Mog Locker', [5] = 'Mog Satchel',
    [6] = 'Mog Sack', [7] = 'Mog Case', [8] = 'Mog Wardrobe', [9] = 'Mog Safe 2', [10] = 'Mog Wardrobe 2',
    [11] = 'Mog Wardrobe 3', [12] = 'Mog Wardrobe 4', [13] = 'Mog Wardrobe 5', [14] = 'Mog Wardrobe 6',
    [15] = 'Mog Wardrobe 7', [16] = 'Mog Wardrobe 8' };
local shown_bag = 0;
local inv_slot = nil;

local W, ROWS, ROW_H = 480, 12, 36;
local desc_obj = nil;
local ring_since = nil;     -- when the ring form appeared (slide-in)
local last_ring = nil;      -- the ring last drawn { key, items, cursor, since }

function panel.release() hider:restore(); end

-- the action menu's Items lists only what can be used (the item's flags have 0x400: potions, food, enchanted gear)
local USABLE = 0x400;
local function from_action_menu()
    local o = require('ui.cmdmenu').opener.inventor;
    return o == 'playermo' or o == 'battlemo';
end
-- Synthesis » Crystal Synthesis: the game's list holds only her crystals, to choose one
local function choosing_crystal()
    return require('ui.cmdmenu').opener.inventor == 'cmbmenu';
end
-- then an ingredient for a slot of the synthesis grid (window "tskill<n>", one per crystal)
local function choosing_ingredient()
    return (require('ui.cmdmenu').opener.inventor or ''):match('^tskill') ~= nil;
end

local view_first = nil;      -- the first row shown (kept between frames so the view scrolls like the game's)

local function items_of(bag, usable_only)        -- usable_only: true, or 'crystal' (crystals only)
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    local rm = AshitaCore:GetResourceManager();
    local out = {};
    local n = math.min(inv:GetContainerCountMax(bag) or 0, 80);
    for i = 1, n do
        local it = inv:GetContainerItem(bag, i);
        if it and it.Id ~= 0 and it.Id ~= 65535 then
            local r = rm:GetItemById(it.Id);
            -- (the game's usable list: items flagged usable, and crystals, type 8, which it lists too)
            local usable = bit.band(r and r.Flags or 0, USABLE) ~= 0 or (r and r.Type == 8);
            if usable_only == 'crystal' then usable = r and r.Type == 8; end
            if r and (not usable_only or usable) then out[#out + 1] = { id = it.Id, index = i, count = it.Count, res = r, equipped = (it.Flags == 5) }; end
        end
    end
    return out, n;
end

-- The game's own order for the list it shows. It isn't always the bag's slot order: an item that arrived in a freed
-- slot is listed at the end, until the bag is sorted. The list class's +0x60 points at a block of item lists, each
-- 81 8-byte records from +0x70 (k * 0x288): a 0xFFFF header, then { u16 item id, u8 slot } per row. The one in use
-- holds exactly our items; returns `list` in its order, or unchanged when none does.
local function in_game_order(cls, list)
    local base = cls and mem.u32(cls + 0x60);
    if base == nil or #list == 0 or not mem.ok(base + 0x70, 24 * 0x288) then return list; end
    local by_slot = {};
    for _, c in ipairs(list) do by_slot[c.index] = c; end
    for k = 0, 23 do
        local s = base + 0x70 + k * 0x288;
        if mem.u16(s) == 0xFFFF and mem.u16(s + #list * 8) ~= 0 and (#list == 80 or mem.u16(s + (#list + 1) * 8) == 0) then
            local out = {};
            for i = 1, #list do
                local c = by_slot[mem.u8(s + i * 8 + 2)];
                if c == nil or c.id ~= mem.u16(s + i * 8) then out = nil; break; end
                out[i] = c;
            end
            if out then return out; end
        end
    end
    return list;
end

local function describe(r)
    local d = (r.Description and r.Description[1] or ''):gsub('\n', '  ');
    if (r.Level or 0) > 0 or (r.Jobs or 0) ~= 0 then
        local jobs, n = {}, 0;
        for j = 1, 22 do
            if bit.band(r.Jobs or 0, bit.lshift(1, j)) ~= 0 then
                n = n + 1;
                jobs[#jobs + 1] = AshitaCore:GetResourceManager():GetString('jobs.names_abbr', j) or '';
            end
        end
        if n > 0 then d = string.format('Lv.%d  %s\n%s', r.Level or 0, n >= 22 and 'All Jobs' or table.concat(jobs, ' '), d); end
    end
    return d;
end

-- Item icons become textures the first time they're drawn, and opening a bag draws them all at once: the first
-- opening in a session stalled for a moment. They're loaded ahead instead, two per frame, while no menu is open
-- (the inventory first, then the other bags; new items as they arrive).
local disagree_since = nil;     -- since when the list's cursor and the item info box name different items
local warm = { bag = 1, slot = 1, done = {} };
local WARM_BAGS = { 0, 8, 10, 11, 12, 13, 14, 15, 16, 5, 6, 7, 1, 2, 4, 9 };
local function warm_icons()
    local _, focus = native.focused();
    if focus ~= nil then return; end
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    local made = 0;
    for _ = 1, 40 do                      -- (at most 40 slots looked at a frame)
        local bag = WARM_BAGS[warm.bag];
        if bag == nil then warm.bag, warm.slot = 1, 1; return; end
        local n = math.min(inv:GetContainerCountMax(bag) or 0, 80);
        if warm.slot > n then
            warm.bag, warm.slot = warm.bag + 1, 1;
        else
            local it = inv:GetContainerItem(bag, warm.slot);
            warm.slot = warm.slot + 1;
            if it and it.Id ~= 0 and it.Id ~= 65535 and not warm.done[it.Id] then
                warm.done[it.Id] = true;
                draw.item_icon(it.Id);
                made = made + 1;
                if made >= 2 then return; end
            end
        end
    end
end

function panel.render()
    pcall(warm_icons);
    if store.data.cmd_menu == false then if hider:active() then hider:restore(); end return; end
    local _, fname = native.focused();
    -- the list itself, or a menu opened from it (Use / Drop, Sort): the list stays up underneath
    local sell = selling(fname);
    local buy = not sell and buying(fname);
    local shopping = sell or buy;
    local own = shopping or (fname == 'inventor' or fname == 'iuse' or fname == 'itmsort2') and gamewin.window('inventor') ~= nil;
    if fname == nil and last_ring and require('ui.cmdmenu').choosing() then
        -- an item chosen from the ring: the game hides its list while you choose the target
        require('ui.cmdmenu').ring(last_ring[1], last_ring[2], last_ring[3], last_ring[4], true);
        return;
    end
    if last_ring and require('ui.cmdmenu').grace() then
        -- just confirmed: the game may reopen the list in a moment; keep things as they are
        require('ui.cmdmenu').ring(last_ring[1], last_ring[2], last_ring[3], last_ring[4], false);
        return;
    end
    if not own then last_ring = nil; end
    if not own or gamewin.window('equip') ~= nil then
        -- (the list stays hidden while the game closes it)
        if hider:active() then
            if gamewin.window('equip') ~= nil then hider:restore(); else hider:release_except({ 'inventor', 'iteminfo' }); end
        end
        return;
    end
    inv_slot = gamewin.slot(shopping and 'shop' or 'inventor');
    local crystal = not shopping and choosing_crystal();
    local usable = not shopping and (from_action_menu() or crystal);
    local filter = crystal and 'crystal' or usable;
    if usable then
        -- only while the game's row count agrees with ours (else the game draws its own list)
        local cls = inv_slot and mem.u32(inv_slot);
        -- (this list keeps its item count at the class's +0x20; +0x1C is the last row on screen, scroll + 10)
        local rows = cls and mem.u16(cls + 0x20);
        local n = #items_of(0, filter);
        if rows == nil or rows ~= n then
            if hider:active() then hider:restore(); end
            return;
        end
    end
    local fresh = not hider:active();       -- the screen just opened
    hider:hide(shopping and SELL_HIDE or HIDE);

    local cid, cidx = gamewin.cursor_item();
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    -- opened from Mog House: the bag chosen there; otherwise the inventory (until the cursor item says otherwise)
    local cmdm = require('ui.cmdmenu');
    if fresh or sell then
        shown_bag = 0;
        if cmdm.last_menu == 'mogcont' then
            for b, n in pairs(BAG_NAMES) do if n == cmdm.last_choice.mogcont then shown_bag = b; end end
        end
    end
    if cid and not sell then
        for _, b in ipairs(BAGS) do
            local it = inv:GetContainerItem(b, cidx or 0);
            if it and it.Id == cid then shown_bag = b; break; end
        end
    end
    if usable then shown_bag = 0; end
    local list, cap = items_of(shown_bag, filter);
    if not buy then list = in_game_order(inv_slot and mem.u32(inv_slot), list); end
    local at = nil;
    if buy then
        list = {};
        local rm = AshitaCore:GetResourceManager();
        for _, g in ipairs(goods) do
            local r = rm:GetItemById(g.id);
            if r then list[#list + 1] = { id = g.id, index = g.slot, count = 1, res = r, price = g.price }; end
        end
        for i, c in ipairs(list) do if c.id == cid then at = i; end end
    end
    for i, c in ipairs(list) do if not buy and c.id == cid and c.index == cidx then at = i; end end
    if sell and at == nil and cid then
        -- (the shop's list numbers its rows its own way: the item itself is what counts)
        for i, c in ipairs(list) do if c.id == cid then at = i; break; end end
    end
    -- The list window's own cursor: the row on screen (class +0x24, 1-based) plus how far the list has scrolled
    -- (+0x1A). It is the game's own answer, so it wins over the item info box (which lags behind, and isn't shown at
    -- all in some lists); not in a shop, whose list numbers its rows its own way.
    if not shopping then
        local cls = inv_slot and mem.u32(inv_slot);
        local row, top = cls and mem.u16(cls + 0x24), cls and mem.u16(cls + 0x1A);
        local n = row and top and row + top;
        if n and row >= 1 and n <= #list then
            -- (unless the item info box has named another item for a while: then our list isn't in the game's
            -- order, and the item itself is what counts)
            local by_id = at;
            if cid == nil or list[n].id == cid or by_id == nil then
                disagree_since = nil;
                at = n;
            else
                disagree_since = disagree_since or require('core.now')();
                if require('core.now')() - disagree_since < 0.4 then at = n; end
            end
        end
    end

    panel.lit = { list = list, at = at };     -- (for dev probes)

    -- opened from the action menu: the same ring as the menu, in its place
    if usable and not crystal and require('ui.cmdmenu').action_spot() then
        if fresh or not ring_since then ring_since = require('core.now')(); end
        local items = {};
        for i, c in ipairs(list) do
            items[i] = { label = c.res.Name[1] or '?', icon = c.id, sub = c.count > 1 and tostring(c.count) or nil };
        end
        if #items == 0 then items[1] = { label = 'No usable items', dim = true }; end
        local c = at and list[at];
        last_ring = { 'items', items, at, ring_since };
        require('ui.cmdmenu').ring('items', items, at, ring_since, require('ui.cmdmenu').choosing(), c and describe(c.res) or nil);
        return;
    end
    ring_since, last_ring = nil, nil;
    local H = 50 + ROWS * ROW_H + 140 + (shopping and 34 or 0);
    local x, y = layout.anchor('topleft', W, H, 24, 40, 'itempanel');
    -- opened from the action menu: in the menu's place, beside the character
    local ax, ay = require('ui.cmdmenu').action_spot();
    if ax then
        local sw, sh = layout.screen();
        x, y = math.min(ax, sw - W - 10), math.max(10, math.min(ay, sh - H - 10));
    end
    -- a window the list works with (an NPC's trade box, a shop's price list ...) stays visible: step right of it
    x = gamewin.clear_x(x, y, W, H, HIDE_SET);
    layout.bounds('itempanel', x, y, W, H);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th);
    draw.image('title_swash', x + 8, y + 4);
    local title = ui.label('itp_title', 'name', { font_height = 22 });
    local ingredient = not shopping and not usable and choosing_ingredient();
    local heading = crystal and 'Choose a Crystal' or ingredient and 'Choose an Ingredient' or usable and 'Items'
                    or BAG_NAMES[shown_bag] or 'Items';
    if shopping then
        if fresh or shopkeeper == nil then shopkeeper = nearest_npc() or false; end
        if sell then heading = shopkeeper and ('Sell to ' .. shopkeeper) or 'Sell';
        else heading = shopkeeper and (shopkeeper .. "'s Wares") or 'Wares'; end
    end
    text.draw(title, heading, x + 40, y + 27, 'baseline');
    local cnt = ui.label('itp_count', 'small', { font_height = 16, font_color = 0xFFC8C4B8, font_alignment = text.align.Right });
    local gil = (inv:GetContainerItem(0, 0) or {}).Count or 0;
    if shopping then
        -- her purse, with a coin; a sale shows as a gold "+N gil" rising from it
        local now = require('core.now')();
        if last_gil and gil > last_gil and not fresh then gain = { gil - last_gil, now }; end
        last_gil = gil;
        text.draw(cnt, string.format('%s gil', tostring(gil):reverse():gsub('(%d%d%d)', '%1,'):reverse():gsub('^,', '')),
            x + W - 20, y + 26, 'baseline');
        draw.image('mi_gil', x + W - 112, y + 8, { scale = { 22 / 44, 22 / 44 } });
        if gain and now - gain[2] < 1.6 then
            local k = (now - gain[2]) / 1.6;
            local g = ui.label('itp_gain', 'name', { font_height = 22, font_color = 0xFFFFE08A, font_alignment = text.align.Right });
            g:set_opacity(1 - k * k);
            text.draw(g, string.format('+%d gil', gain[1]), x + W - 20, y + 26 - 30 * k, 'baseline');
        end
    else
        text.draw(cnt, string.format('%d / %d', #list, cap), x + W - 20, y + 26, 'baseline');
    end

    local sw, sh = layout.size('row_sel');
    -- the view only scrolls when the cursor leaves it (as the game's lists do), not with every move
    local first = view_first or 0;
    if at then
        if at <= first then first = at - 1; elseif at > first + ROWS then first = at - ROWS; end
    end
    first = math.max(0, math.min(first, math.max(0, #list - ROWS)));
    view_first = first;
    if #list == 0 then
        local none = ui.label('itp_none', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
        text.draw(none, crystal and 'No crystals.' or usable and 'No usable items.' or 'Empty.', x + 34, y + 76, 'baseline');
    end
    for r = 1, math.min(ROWS, #list - first) do
        local i = r + first;
        local c = list[i];
        local ry = y + 46 + (r - 1) * ROW_H;
        local sel = (i == at);
        if sel then
            draw.nine('row_sel', x + 22, ry, W - 34, ROW_H - 4, 6, sw, sh);
            draw.image('cursor_gold', x + 2, ry + (ROW_H - 26) / 2);
        end
        draw.entry(draw.item_icon(c.id), x + 30, ry + 2, 28, 28);
        local o = ui.label('itp_r' .. r, 'small', { font_height = 18 });
        local col = c.equipped and 0xFF9BE08C or (sel and 0xFFFFFFFF or 0xFFE8E4D8);
        if o.settings.font_color ~= col then o:set_font_color(col); end
        text.draw(o, c.res.Name[1] or '?', x + 68, ry + 22, 'baseline');
        if buy then
            -- the price: gold if her purse covers it, dim red if not
            local q = ui.label('itp_q' .. r, 'small', { font_height = 17, font_alignment = text.align.Right });
            local pc = c.price <= gil and 0xFFF0D890 or 0xFFB06A60;
            if q.settings.font_color ~= pc then q:set_font_color(pc); end
            text.draw(q, tostring(c.price):reverse():gsub('(%d%d%d)', '%1,'):reverse():gsub('^,', '') .. ' gil',
                x + W - 22, ry + 22, 'baseline');
        elseif (c.res.StackSize or 1) > 1 or c.count > 1 then
            local q = ui.label('itp_q' .. r, 'small', { font_height = 16, font_color = 0xFFC8C4B8, font_alignment = text.align.Right });
            text.draw(q, tostring(c.count), x + W - 22, ry + 22, 'baseline');
        end
    end
    if #list > ROWS then
        local more = ui.label('itp_more', 'small', { font_height = 14, font_color = 0xFFB8C0D8, font_alignment = text.align.Right });
        text.draw(more, string.format('%d–%d', first + 1, math.min(#list, first + ROWS)), x + W - (shopping and 130 or 110), y + 26, 'baseline');
    end

    local dy = y + 46 + ROWS * ROW_H + 4;
    draw.image('name_rule', x + 16, dy, { scale = { (W - 32) / 300, 1 } });
    local c = at and list[at];
    if c then
        local d = describe(c.res);
        desc_obj = desc_obj or text.new('small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = W - 44 });
        if desc_obj.settings.text ~= d then text.set(desc_obj, d); end
        text.render(desc_obj, x + 22, dy + 10);
    end
    if c and buy then
        -- can she wear it? (her main job and level against the item's)
        local pl = AshitaCore:GetMemoryManager():GetPlayer();
        local job, lvl = pl:GetMainJob(), pl:GetMainJobLevel();
        local line, col;
        if (c.res.Jobs or 0) ~= 0 and bit.band(c.res.Jobs, bit.lshift(1, job)) == 0 then
            line, col = 'Not for your job.', 0xFFB06A60;
        elseif (c.res.Level or 0) > lvl then
            line, col = string.format('Needs level %d.', c.res.Level), 0xFFB06A60;
        elseif c.price > gil then
            line, col = string.format('%d gil short.', c.price - gil), 0xFFB06A60;
        else
            line, col = string.format('Yours for %d gil.', c.price), 0xFFF0D890;
        end
        local o = ui.label('itp_offer', 'small', { font_height = 18 });
        if o.settings.font_color ~= col then o:set_font_color(col); end
        text.draw(o, line, x + 22, dy + 128, 'baseline');
    end
    if c and sell then
        -- what the shopkeeper offers, and (choosing how many) the amount and the total
        local price = offers[c.index];
        local who = shopkeeper or 'The shopkeeper';
        local line = price and string.format('%s offers %d gil %s.', who, price, c.count > 1 and 'each' or 'for it')
                     or 'Confirm to ask what it fetches.';
        local o = ui.label('itp_offer', 'small', { font_height = 18, font_color = 0xFFF0D890 });
        text.draw(o, line, x + 22, dy + 96, 'baseline');
        local qs = gamewin.slot('itemctrl');
        local qc = qs and gamewin.window('itemctrl') and mem.u32(qs);
        local n, max = qc and mem.u8(qc + 0x23), qc and mem.u8(qc + 0x22);
        if n and max and max >= 1 and n >= 1 and n <= max then
            local q = ui.label('itp_qty', 'name', { font_height = 22 });
            text.draw(q, string.format('Sell %d of %d', n, max), x + 22, dy + 132, 'baseline');
            if price then
                local t = ui.label('itp_total', 'name', { font_height = 22, font_color = 0xFFF0D890, font_alignment = text.align.Right });
                text.draw(t, string.format('%d gil', price * n), x + W - 22, dy + 132, 'baseline');
            end
        end
    end
    if shopping then
        local qs = gamewin.slot('itemctrl');
        local qc = qs and gamewin.window('itemctrl') and mem.u32(qs);
        local rows = {};
        for i, it in ipairs(list) do rows[i] = it.res.Name[1] or '?'; end
        local cur = at and list[at];
        panel.shop = { mode = sell and 'sell' or 'buy', rows = rows, cursor = at, gil = gil,
                       keeper = shopkeeper or nil, at = os.clock(),
                       offer = cur and (sell and offers[cur.index] or cur.price) or nil,
                       qty = qc and mem.u8(qc + 0x23) or nil, qty_max = qc and mem.u8(qc + 0x22) or nil };
    end
    if crystal then
        local hint = ui.label('itp_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
        text.draw(hint, 'Confirm: synthesize with this crystal', x + 22, y + H - 10, 'baseline');
    end
    if not usable and ingredient then
        local hint = ui.label('itp_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
        text.draw(hint, 'Confirm: put it in the synthesis', x + 22, y + H - 10, 'baseline');
    elseif not usable then
        local hint = ui.label('itp_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
        local choosing = sell and gamewin.window('itemctrl') ~= nil;
        text.draw(hint, buy and 'Confirm: buy' or choosing and 'Up / Down: how many    Left: all    Confirm: sell' or sell and 'Confirm: offer it to the shopkeeper' or '+ : Sort  (Auto / Manual / Recycle Bin)',
            x + 22, y + H - 10, 'baseline');
    end
end

panel.describe = describe;
panel.selling = selling;
panel.buying = buying;

return panel;
