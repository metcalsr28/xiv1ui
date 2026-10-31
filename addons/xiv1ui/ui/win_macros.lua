--[[
* xiv1ui - Macros window (Main Menu » Macros): xiv1ui's own macros, for the action bar. A macro is a name, up to six
* lines run in order (with "/wait N" and a trailing "<wait N>" for pauses), an icon, and whether the name is shown on
* the icon. Action-bar slots refer to a macro by id, so editing it updates every slot that uses it.
*
* Left: the macro list ("New Macro" at the top). Right: the selected macro's fields.
*   ↑/↓ choose, → / ← move between the list and the fields, Enter edits the field:
*     Name / Line n  a text field (type, Enter to keep, Esc to cancel)
*     Icon           a grid of icons: arrows choose, Enter picks
*     Show name      toggles
*     Place on bar   then press 1–0 or click a slot (on the layer and page shown)
*     Delete         press Enter twice
* Commands: /xiv1ui macro new | name <id> <text> | line <id> <n> <text> | icon <id> <name> | delete <id>
--]]

local ui     = require('core.ui');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local store  = require('core.store');
local ti     = require('core.textinput');
local ICONS  = require('core.macro_icons');

local M = {};

local FIELDS = { 'Name', 'Icon', 'Show name', 'Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5', 'Line 6',
                 'Place on bar', 'Delete' };
local LIST_ROWS = 13;
local GRID_COLS = 9;

local win = { id = 'macros', title = 'Macros', w = 820, h = 560, sel = 1, first = 0, focus = 'list', field = 1,
              rows = {}, frows = {}, grid = nil, armed_delete = false };

local function data()
    store.data.macros = store.data.macros or T{};
    store.data.macro_next = store.data.macro_next or 1;
    return store.data.macros;
end

--- Macro ids in creation order.
local function ids()
    local out = {};
    for id in pairs(data()) do out[#out + 1] = tonumber(id); end
    table.sort(out);
    return out;
end

local function get(id) return id and data()[tostring(id)] or nil; end
M.get = get;

local function new_macro()
    local id = store.data.macro_next or 1;
    store.data.macro_next = id + 1;
    data()[tostring(id)] = T{ name = 'Macro ' .. id, lines = T{}, icon = 'star', show_name = true };
    store.save();
    return id;
end

local function selected_id(w)
    local list = ids();
    return w.sel > 1 and list[w.sel - 1] or nil;
end

-- the last list row opens FFXI's own macro books
local function books_row(w) return w.sel == #ids() + 2; end

local function edit_text(initial, apply)
    ti.begin(initial, function (s) if s ~= nil then apply(s); store.save(); end end);
end

local function activate_field(w)
    local id = selected_id(w);
    local m = get(id);
    if m == nil then return; end
    local f = FIELDS[w.field];
    if f == 'Name' then
        edit_text(m.name, function (s) if s ~= '' then m.name = s; end end);
    elseif f == 'Icon' then
        local at = 1;
        for i, n in ipairs(ICONS) do if n == m.icon then at = i; end end
        w.grid = at;
    elseif f == 'Show name' then
        m.show_name = not m.show_name; store.save();
    elseif f:match('^Line') then
        local n = tonumber(f:match('%d'));
        edit_text(m.lines[n] or '', function (s)
            m.lines[n] = s;
            -- keep lines contiguous: drop empty ones
            local out = T{};
            for i = 1, 6 do if m.lines[i] and m.lines[i]:match('%S') then out[#out + 1] = m.lines[i]; end end
            m.lines = out;
        end);
    elseif f == 'Place on bar' then
        require('ui.hotbar').begin_assign({ kind = 'macro', ref = id, name = m.name });
        ui.close(w.id); ui.close('mainmenu');
    elseif f == 'Delete' then
        if w.armed_delete then
            data()[tostring(id)] = nil; store.save();
            w.armed_delete = false; w.focus = 'list'; w.sel = math.max(1, w.sel - 1);
        else
            w.armed_delete = true;
        end
    end
end

win.draw = function (w, x, y)
    local list = ids();
    local items = { { label = '+ New Macro', color = 0xFFF0DCA0 } };
    for _, id in ipairs(list) do
        local m = get(id);
        items[#items + 1] = { label = m.name, indent = 34 };
    end
    items[#items + 1] = { label = 'FFXI Macro Books', color = 0xFFB8C0D8 };
    if w.sel > #items then w.sel = #items; end
    if w.sel - 1 < w.first then w.first = w.sel - 1; end
    if w.sel > w.first + LIST_ROWS then w.first = w.sel - LIST_ROWS; end
    ui.header('mcr_list', 'Macros', x + 24, y + 62, 250);
    w.rows = ui.list(w, 'mcrlist', items, w.sel, x + 40, y + 76, 240, 32, LIST_ROWS, w.first, w.focus == 'list');
    -- small icons in the list
    for _, r in ipairs(w.rows) do
        local i = r[5];
        if i > 1 then
            local m = get(list[i - 1]);
            if m and m.icon then draw.image('mi_' .. m.icon, r[1] + 6, r[2] + 2, { scale = 26 / 44 }); end
        end
    end

    local id = selected_id(w);
    local m = get(id);
    local dx = x + 320;
    ui.header('mcr_detail', m and m.name or 'New Macro', dx, y + 62, w.w - 350);
    if m == nil then
        local hint = ui.label('mcr_hint0', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
        text.draw(hint, books_row(w) and 'Enter: open FFXI\'s own macro books (Ctrl / Alt palettes)'
                                      or 'Enter: create a new macro', dx + 4, y + 110, 'baseline');
        w.frows = {};
        return;
    end
    -- preview: the macro as it looks on the bar
    draw.image('slot_shadow', dx + 4, y + 84);
    draw.image('slot_well', dx + 12, y + 92);
    if m.icon then draw.image('mi_' .. m.icon, dx + 12, y + 92); end
    draw.image('slot_ring', dx + 4, y + 84);
    local hint = ui.label('mcr_pvh', 'small', { font_height = 14, font_color = 0xFFB8C0D8, font_alignment = text.align.Center });
    text.draw(hint, 'as on the bar', dx + 34, y + 164, 'baseline');

    -- fields
    local fitems = {};
    for i, f in ipairs(FIELDS) do
        local right;
        if f == 'Name' then right = m.name;
        elseif f == 'Icon' then right = m.icon or '';
        elseif f == 'Show name' then right = m.show_name and 'On' or 'Off';
        elseif f:match('^Line') then right = m.lines[tonumber(f:match('%d'))] or '';
        elseif f == 'Delete' then right = w.armed_delete and 'Press Enter again to delete' or ''; end
        -- the field being typed into shows the text with a caret
        if ti.active() and w.focus == 'fields' and i == w.field then
            right = ti.before_caret() .. ((math.floor(require('core.now')() * 3) % 2 == 0) and '|' or ' ') .. ti.text():sub(#ti.before_caret() + 1);
        end
        fitems[i] = { label = f, right = right,
                      color = (f == 'Delete' and 0xFFFF9080) or (f == 'Place on bar' and 0xFF9BE08C) or nil };
    end
    w.frows = ui.list(w, 'mcrfields', fitems, w.field, dx + 100, y + 84, w.w - 450, 32, #FIELDS, 0, w.focus == 'fields');

    -- on-screen keyboard while a field is being typed into
    if ti.active() then ti.draw_osk(x + 8, y + 140); end      -- over the macro list (the field being typed stays in view)

    -- icon picker
    if w.grid then
        local gx, gy = dx - 10, y + 150;
        local gw, gh = GRID_COLS * 52 + 24, math.ceil(#ICONS / GRID_COLS) * 52 + 56;
        local bw, bh = layout.size('win_body');
        draw.nine('win_body', gx, gy, gw, gh, 12, bw, bh);
        draw.nine('win_body', gx, gy, gw, gh, 12, bw, bh);       -- twice: opaque enough to hide the fields under it
        local t = ui.label('mcr_gridt', 'label', { font_height = 18 });
        text.draw(t, 'Choose an icon', gx + 16, gy + 28, 'baseline');
        for i, n in ipairs(ICONS) do
            local cx = gx + 12 + ((i - 1) % GRID_COLS) * 52;
            local cy = gy + 40 + math.floor((i - 1) / GRID_COLS) * 52;
            draw.image('mi_' .. n, cx + 4, cy + 4);
            if i == w.grid then draw.image('slot_ring_white', cx - 4, cy - 4, { scale = 52 / 60 }); end
        end
    end
end

win.key = function (w, vk)
    -- while typing, keys that reach the window come from the controller: they drive the on-screen keyboard
    if ti.active() then return ti.pad(vk); end
    local nlist = #ids() + 2;
    if w.grid then
        local n = #ICONS;
        if vk == ui.VK.LEFT then w.grid = (w.grid - 2) % n + 1;
        elseif vk == ui.VK.RIGHT then w.grid = w.grid % n + 1;
        elseif vk == ui.VK.UP then w.grid = (w.grid - 1 - GRID_COLS) % n + 1;
        elseif vk == ui.VK.DOWN then w.grid = (w.grid - 1 + GRID_COLS) % n + 1;
        elseif vk == ui.VK.RETURN then
            local m = get(selected_id(w));
            if m then m.icon = ICONS[w.grid]; store.save(); end
            w.grid = nil;
        elseif vk == ui.VK.ESCAPE then w.grid = nil; end
        return true;
    end
    if w.focus == 'list' then
        if vk == ui.VK.UP then w.sel = (w.sel - 2) % nlist + 1;
        elseif vk == ui.VK.DOWN then w.sel = w.sel % nlist + 1;
        elseif vk == ui.VK.RETURN or vk == ui.VK.RIGHT then
            if books_row(w) then
                if vk == ui.VK.RETURN then require('ui.gamein').ffxi_macros(); end
                return true;
            end
            if w.sel == 1 then
                new_macro();
                w.sel = nlist;
            end
            w.focus, w.field = 'fields', 1;
        elseif vk == ui.VK.ESCAPE then return false; end
    else
        if vk ~= ui.VK.RETURN then w.armed_delete = false; end
        if vk == ui.VK.UP then w.field = (w.field - 2) % #FIELDS + 1;
        elseif vk == ui.VK.DOWN then w.field = w.field % #FIELDS + 1;
        elseif vk == ui.VK.LEFT or vk == ui.VK.ESCAPE then w.focus = 'list';
        elseif vk == ui.VK.RETURN then activate_field(w); end
    end
    return true;
end

win.click = function (w, mx, my)
    if ti.active() then return true; end
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then
            w.sel, w.focus = r[5], 'list';
            if r[5] == 1 or books_row(w) then win.key(w, ui.VK.RETURN); end
            return true;
        end
    end
    for _, r in ipairs(w.frows) do
        if ui.hit(r, mx, my) then w.field, w.focus = r[5], 'fields'; activate_field(w); return true; end
    end
end

--- /xiv1ui macro ...
function M.command(args)
    if (args[2] or ''):lower() ~= 'macro' then return; end
    local sub = (args[3] or ''):lower();
    local m = get(tonumber(args[4]));
    if sub == 'new' then new_macro();
    elseif sub == 'name' and m then m.name = table.concat(args, ' ', 5);
    elseif sub == 'line' and m then m.lines[tonumber(args[5]) or 1] = table.concat(args, ' ', 6);
    elseif sub == 'icon' and m then m.icon = args[5];
    elseif sub == 'delete' and m then data()[args[4]] = nil; end
    store.save();
end

function M.open() ui.open(win); end

return M;
