--[[
* xiv1ui - Inventory window (reference §23): a list (not a grid), as in 1.0, with tabs for FFXI's containers
* (Items, Crystals, Satchel, Sack, Case, Wardrobe) and Currency; "◆ Items  n/max" with gil; an item detail block
* (icon, name, level/jobs in green, description) on the right. Enter opens the item command popup:
* Use / Equip (through the game's own /item and /equip) / Close. Tab or ←/→ switch tabs.
--]]

local ui   = require('core.ui');
local draw = require('core.draw');
local text = require('core.text');

local M = {};

local TABS = {
    { label = 'Items',    bag = 0, filter = function (it) return it.Type ~= 8; end },
    { label = 'Crystals', bag = 0, filter = function (it) return it.Type == 8; end },
    { label = 'Satchel',  bag = 5 },
    { label = 'Sack',     bag = 6 },
    { label = 'Case',     bag = 7 },
    { label = 'Wardrobe', bag = 8 },
    { label = 'Currency', currency = true },
};
local SLOT_NAMES = { 'main', 'sub', 'range', 'ammo', 'head', 'body', 'hands', 'legs', 'feet', 'neck', 'waist',
                     'ear1', 'ear2', 'ring1', 'ring2', 'back' };

local ROWS = 14;
local win = { id = 'inventory', title = 'Inventory', w = 640, h = 500, tab = 1, sel = 1, first = 0, rows = {}, tabs = {} };

local function gil()
    local g = AshitaCore:GetMemoryManager():GetInventory():GetContainerItem(0, 0);
    return g and g.Count or 0;
end

local function gather(tab)
    local t = TABS[tab];
    local out = {};
    if t.currency then return out; end
    local inv = AshitaCore:GetMemoryManager():GetInventory();
    local r = AshitaCore:GetResourceManager();
    local max = inv:GetContainerCountMax(t.bag) or 0;
    for i = 1, max do
        local e = inv:GetContainerItem(t.bag, i);
        if e and e.Id ~= 0 and e.Id ~= 65535 then
            local it = r:GetItemById(e.Id);
            if it and (t.filter == nil or t.filter(it)) then
                out[#out + 1] = { id = e.Id, count = e.Count, res = it, name = it.Name[1] };
            end
        end
    end
    return out, max;
end

local function refresh(w)
    w.items, w.max = gather(w.tab);
    w.sel = math.max(1, math.min(w.sel, #w.items));
    w.first = 0;
    w.popup = nil;
end

win.on_open = function (w) refresh(w); end

local function jobs_text(mask)
    if mask == nil or mask == 0 then return nil; end
    local r = AshitaCore:GetResourceManager();
    local out = {};
    for j = 1, 22 do
        if bit.band(mask, bit.lshift(1, j)) ~= 0 then
            local a = r:GetString('jobs.names_abbr', j);
            out[#out + 1] = (a and a ~= '') and a or tostring(j);
        end
    end
    if #out >= 22 then return 'All Jobs'; end
    return table.concat(out, ' ');
end

local function popup_items(entry)
    local list = {};
    if entry.res.Slots and entry.res.Slots ~= 0 then list[#list + 1] = { label = 'Equip', act = 'equip' };
    else list[#list + 1] = { label = 'Use', act = 'use' }; end
    list[#list + 1] = { label = 'Close', act = 'close' };
    return list;
end

local function act(w, a)
    local e = w.items[w.sel];
    w.popup = nil;
    if not e or a == 'close' then return; end
    local cm = AshitaCore:GetChatManager();
    if a == 'use' then
        cm:QueueCommand(1, string.format('/item "%s" <me>', e.name));
    elseif a == 'equip' then
        for b = 0, 15 do
            if bit.band(e.res.Slots, bit.lshift(1, b)) ~= 0 then
                cm:QueueCommand(1, string.format('/equip %s "%s"', SLOT_NAMES[b + 1], e.name));
                break;
            end
        end
    end
end

win.draw = function (w, x, y)
    -- tabs as text labels separated by thin bars; active one brighter and underlined
    w.tabs = {};
    local tx = x + 24;
    for i, t in ipairs(TABS) do
        local o = ui.label('invtab' .. i, 'label', { font_height = 17 });
        local col = (i == w.tab) and 0xFFFFFFFF or 0xFF9AA4C4;
        if o.settings.font_color ~= col then o:set_font_color(col); end
        text.draw(o, t.label, tx, y + 62, 'baseline');
        local tw = text.size(o);
        if i == w.tab then draw.image('name_rule', tx - 2, y + 64, { scale = { (tw + 6) / 300, 1 } }); end
        w.tabs[i] = { tx - 4, y + 44, tw + 8, 24 };
        tx = tx + tw + 22;
    end

    local t = TABS[w.tab];
    if t.currency then
        ui.header('invcur', 'Currency', x + 30, y + 104, 280);
        local o = ui.label('invgil', 'name', { font_height = 22 });
        text.draw(o, string.format('Gil   %s', tostring(gil()):reverse():gsub('(%d%d%d)', '%1,'):reverse():gsub('^,', '')),
                  x + 50, y + 144, 'baseline');
        return;
    end

    ui.header('invhdr', string.format('%s   %d/%d', t.label, #w.items, w.max or 0), x + 30, y + 98, 300);

    local items = {};
    for i, e in ipairs(w.items) do items[i] = { label = e.name, indent = 26, right = e.count > 1 and tostring(e.count) or nil }; end
    if #items == 0 then items[1] = { label = '(empty)', disabled = true }; end
    if w.sel > w.first + ROWS then w.first = w.sel - ROWS; end
    if w.sel <= w.first then w.first = w.sel - 1; end
    w.rows = ui.list(w, 'inv', items, w.sel, x + 40, y + 110, 300, 26, ROWS, w.first, ui.top() == w and not w.popup);
    for r = 1, math.min(ROWS, #w.items - w.first) do
        local e = w.items[r + w.first];
        draw.entry(draw.item_icon(e.id), x + 46, y + 110 + (r - 1) * 26 + 2, 20, 20);
    end

    -- detail block
    local e = w.items[w.sel];
    if e then
        local dx = x + 360;
        draw.image('slot_square', dx, y + 104);
        draw.entry(draw.item_icon(e.id), dx + 4, y + 108, 32, 32);
        local nm = ui.label('invname', 'name', { font_height = 20, box_width = 230 });
        text.draw(nm, e.name, dx + 50, y + 128, 'baseline');
        local ly = y + 164;
        local function line(key, str, col)
            if not str or str == '' then return; end
            local o = ui.label('invd' .. key, 'small', { font_height = 15, font_color = col or 0xFFE8E4D8, box_width = 250 });
            text.draw(o, str, dx, ly, 'baseline');
            local _, h = text.size(o);
            ly = ly + math.max(20, h - 2);
        end
        if e.res.Level and e.res.Level > 0 then line('lvl', 'Required Level: ' .. e.res.Level, 0xFF9BE08C); end
        local jt = jobs_text(e.res.Jobs);
        if jt and e.res.Slots ~= 0 then line('jobs', 'Requires: ' .. jt, 0xFF9BE08C); end
        local desc = e.res.Description and e.res.Description[1] or '';
        line('desc', desc);
        if e.count > 1 then line('cnt', 'Quantity: ' .. e.count, 0xFFF0DCA0); end
    end

    -- command popup
    if w.popup then
        local px, py = x + 200, y + 110 + (w.sel - w.first - 1) * 26;
        local pw, ph = 160, 18 + #w.popup.items * 26;
        local cw, ch = require('core.layout').size('win_body');
        draw.nine('win_body', px, py, pw, ph, 12, cw, ch);
        w.popup.rows = ui.list(w, 'invpop', w.popup.items, w.popup.sel, px + 20, py + 8, pw - 30, 26, #w.popup.items, 0, true);
    end
end

win.key = function (w, vk)
    if w.popup then
        local p = w.popup;
        if vk == ui.VK.UP then p.sel = (p.sel - 2) % #p.items + 1;
        elseif vk == ui.VK.DOWN then p.sel = p.sel % #p.items + 1;
        elseif vk == ui.VK.RETURN then act(w, p.items[p.sel].act);
        elseif vk == ui.VK.ESCAPE then w.popup = nil; end
        return true;
    end
    local n = #w.items;
    if vk == ui.VK.UP then w.sel = math.max(1, w.sel - 1);
    elseif vk == ui.VK.DOWN then w.sel = math.min(math.max(1, n), w.sel + 1);
    elseif vk == ui.VK.PRIOR then w.sel = math.max(1, w.sel - ROWS);
    elseif vk == ui.VK.NEXT then w.sel = math.min(math.max(1, n), w.sel + ROWS);
    elseif vk == ui.VK.LEFT then w.tab = (w.tab - 2) % #TABS + 1; refresh(w);
    elseif vk == ui.VK.RIGHT or vk == ui.VK.TAB then w.tab = w.tab % #TABS + 1; refresh(w);
    elseif vk == ui.VK.RETURN then
        if w.items[w.sel] then w.popup = { sel = 1, items = popup_items(w.items[w.sel]) }; end
    elseif vk == ui.VK.ESCAPE then return false; end
    return true;
end

win.click = function (w, mx, my, button)
    if w.popup and w.popup.rows then
        for _, r in ipairs(w.popup.rows) do
            if ui.hit(r, mx, my) then act(w, w.popup.items[r[5]].act); return; end
        end
        w.popup = nil;
        return;
    end
    for i, r in ipairs(w.tabs) do
        if ui.hit(r, mx, my) then w.tab = i; refresh(w); return; end
    end
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then
            if w.sel == r[5] or button == 2 then
                w.sel = r[5];
                if w.items[w.sel] then w.popup = { sel = 1, items = popup_items(w.items[w.sel]) }; end
            else
                w.sel = r[5];
            end
            return;
        end
    end
end

win.wheel = function (w, delta)
    w.sel = math.max(1, math.min(#w.items, w.sel + (delta > 0 and -3 or 3)));
end

function M.open() ui.open(win); end

return M;
