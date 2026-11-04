--[[
* xiv1ui - Macros window (Main Menu » Macros): xiv1ui's own macros, for the action bar. A macro is a name, up to six
* lines run in order (with "/wait N" and a trailing "<wait N>" for pauses), an icon, and whether the name is shown on
* the icon. Action-bar slots refer to a macro by id, so editing it updates every slot that uses it.
*
* Left: the macro list ("New Macro" at the top). Right: the selected macro's fields.
*   ↑/↓ choose, → / ← move between the list and the fields, Enter edits the field:
*     Name / Line n  a text field (type, Enter to keep, Esc to cancel)
*     Icon           a grid of icons (the macro icons, then every action icon): arrows choose, Enter picks
*     Show name      toggles
*     Place on bar   a map of every bar (Green / Red, bars 1–3, slots 1–10) with what's on them: choose a slot,
*                    Enter places the macro there (e.g. "Green 3, slot 2")
* Abilities & Spells: everything the character has learned, by category (Left / Right), with New on what isn't
* on a bar yet; Enter places the action on a bar with the same map as a macro.
* The last row, Edit Action Bars, shows the same map of every bar: choose a slot, Enter picks one of your macros to
* put there, Delete / Backspace (or RB on the controller) clears it, Esc goes back.
*     Delete         press Enter twice
* Commands: /xiv1ui macro new | name <id> <text> | line <id> <n> <text> | icon <id> <name> | delete <id>
--]]

local ui     = require('core.ui');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local store  = require('core.store');
local ti     = require('core.textinput');
local MACRO_ICONS = require('core.macro_icons');

-- The icons a macro can have: the macro icons (stored by name), then every action icon (stored as its texture,
-- ai_...), without repeats.
local ICONS = {};
for _, n in ipairs(MACRO_ICONS) do ICONS[#ICONS + 1] = n; end
do
    local seen, extra = {}, {};
    for _, group in pairs(require('core.action_icons')) do
        for _, tex in pairs(group) do
            -- (not the category emblems, ai_gen_*: they stand for no one action)
            if not seen[tex] and tex:sub(1, 7) ~= 'ai_gen_' then seen[tex] = true; extra[#extra + 1] = tex; end
        end
    end
    table.sort(extra);
    for _, t in ipairs(extra) do ICONS[#ICONS + 1] = t; end
end
local function icon_tex(n) return n and (n:match('^ai_') and n or ('mi_' .. n)) or nil; end
local GRID_ROWS = 6;          -- rows of icons shown at once (the grid scrolls)

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

-- the last two list rows open the abilities & spells list and the action bar editor
local function acts_row(w) return w.sel == #ids() + 2; end
local function books_row(w) return w.sel == #ids() + 3; end

-- Abilities & Spells: the categories that have something in them, and the list of one
local function act_cats(w)
    local out = {};
    for _, c in ipairs(require('core.actions').CATEGORIES) do
        if w.acts.data[c] and #w.acts.data[c] > 0 then out[#out + 1] = c; end
    end
    return out;
end
local function is_new(b)
    local hb = require('ui.hotbar');
    return not hb.offered(b.name) and not hb.on_any_bar(b.name);
end
local function open_acts(w)
    w.acts = { data = require('core.actions').learned(), cat = 1, sel = 1, first = 0 };
    -- start on the first category with something new in it
    for i, c in ipairs(act_cats(w)) do
        for _, b in ipairs(w.acts.data[c]) do if is_new(b) then w.acts.cat = i; return; end end
    end
end

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
        local lay = require('ui.layers').current();
        w.place = { r = (store.data.hotbar.page - 1) * 2 + (lay or 1), c = 1 };
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
    items[#items + 1] = { label = 'Abilities & Spells', color = 0xFF9BD0F0 };
    items[#items + 1] = { label = 'Edit Action Bars', color = 0xFF9BE08C };
    if w.sel > #items then w.sel = #items; end
    if w.sel - 1 < w.first then w.first = w.sel - 1; end
    if w.sel > w.first + LIST_ROWS then w.first = w.sel - LIST_ROWS; end
    ui.header('mcr_list', 'Macros', x + 24, y + 62, 250);
    w.rows = ui.list(w, 'mcrlist', items, w.sel, x + 40, y + 76, 240, 32, LIST_ROWS, w.first,
                     w.focus == 'list' and not (w.bars or w.place or w.acts));
    -- small icons in the list
    for _, r in ipairs(w.rows) do
        local i = r[5];
        if i > 1 then
            local m = get(list[i - 1]);
            if m and m.icon then draw.image(icon_tex(m.icon), r[1] + 6, r[2] + 2, { scale = 26 / 44 }); end
        end
    end

    local id = selected_id(w);
    local m = get(id);
    local dx = x + 320;
    ui.header('mcr_detail', m and m.name or (books_row(w) and 'Action Bars')
              or (acts_row(w) and 'Abilities & Spells') or 'New Macro', dx, y + 62, w.w - 350);
    if m == nil then
        w.frows = {};
        if w.acts and not w.place then
            -- the list of what she has learned, one category at a time
            local a = w.acts;
            local cats = act_cats(w);
            if #cats == 0 then
                local none = ui.label('mcr_actnone', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
                text.draw(none, 'Nothing learned yet.', dx + 4, y + 110, 'baseline');
                return;
            end
            a.cat = math.max(1, math.min(a.cat, #cats));
            local list = a.data[cats[a.cat]];
            a.sel = math.max(1, math.min(a.sel, #list));
            local ROWS = 11;
            if a.sel - 1 < a.first then a.first = a.sel - 1; end
            if a.sel > a.first + ROWS then a.first = a.sel - ROWS; end
            local ct = ui.label('mcr_actcat', 'label', { font_height = 19 });
            text.draw(ct, cats[a.cat], dx + 34, y + 104, 'baseline');
            draw.image('dlg_arrow', dx + 4, y + 88, { rot = -math.pi / 2 });
            draw.image('dlg_arrow', dx + w.w - 400, y + 88, { rot = math.pi / 2 });
            local cn = ui.label('mcr_actn', 'small', { font_height = 14, font_color = 0xFFB8C0D8,
                                                       font_alignment = text.align.Right });
            text.draw(cn, string.format('%d / %d   %d of %d', a.cat, #cats, a.sel, #list), dx + w.w - 410, y + 103,
                      'baseline');
            local items = {};
            for i, b in ipairs(list) do
                items[i] = { label = b.name, indent = 34, right = is_new(b) and 'New' or (b.cost and b.cost > 0 and
                             (b.cost .. ' MP')) or nil };
            end
            w.arows = ui.list(w, 'mcracts', items, a.sel, dx + 4, y + 118, w.w - 360, 32, ROWS, a.first, true);
            for _, r in ipairs(w.arows) do
                local info = require('core.actions').resolve(list[r[5]]);
                if info then
                    draw.image(info.disc, r[1] + 4, r[2] + 2, { scale = 26 / 44 });
                    if info.icon then draw.image(info.icon, r[1] + 4, r[2] + 2, { scale = 26 / 44 }); end
                end
            end
            local hint = ui.label('mcr_acth', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
            text.draw(hint, 'Enter: place on a bar   Left / Right: category   Esc: back', dx + 4, y + w.h - 24, 'baseline');
            return;
        end
        local hint = ui.label('mcr_hint0', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
        text.draw(hint, books_row(w) and 'Enter: see every bar, put your macros on them or clear slots'
                                      or acts_row(w) and 'Enter: the abilities and spells you have, to put on your bars'
                                      or 'Enter: create a new macro', dx + 4, y + 110, 'baseline');
        if not (w.bars or w.place) then return; end
    end
    if m then
    -- preview: the macro as it looks on the bar
    draw.image('slot_shadow', dx + 4, y + 84);
    draw.image('slot_well', dx + 12, y + 92);
    if m.icon then draw.image(icon_tex(m.icon), dx + 12, y + 92); end
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

    end
    -- on-screen keyboard while a field is being typed into
    if ti.active() then ti.draw_osk(x + 8, y + 140); end      -- over the macro list (the field being typed stays in view)

    -- icon picker
    if w.grid then
        local gx, gy = dx - 10, y + 150;
        local total_rows = math.ceil(#ICONS / GRID_COLS);
        local gw, gh = GRID_COLS * 52 + 24, GRID_ROWS * 52 + 56;
        -- keep the chosen icon's row in view
        local row = math.floor((w.grid - 1) / GRID_COLS);
        w.grid_first = w.grid_first or 0;
        if row < w.grid_first then w.grid_first = row; end
        if row >= w.grid_first + GRID_ROWS then w.grid_first = row - GRID_ROWS + 1; end
        local bw, bh = layout.size('win_body');
        draw.nine('win_body', gx, gy, gw, gh, 12, bw, bh);
        draw.nine('win_body', gx, gy, gw, gh, 12, bw, bh);       -- twice: opaque enough to hide the fields under it
        local t = ui.label('mcr_gridt', 'label', { font_height = 18 });
        text.draw(t, 'Choose an icon', gx + 16, gy + 28, 'baseline');
        local more = ui.label('mcr_gridn', 'small', { font_height = 14, font_color = 0xFFB8C0D8,
                                                      font_alignment = text.align.Right });
        text.draw(more, string.format('%d of %d   (scroll for more)', w.grid, #ICONS), gx + gw - 16, gy + 26, 'baseline');
        w.gcells = {};
        for i, n in ipairs(ICONS) do
            local r = math.floor((i - 1) / GRID_COLS) - w.grid_first;
            if r >= 0 and r < GRID_ROWS then
                local cx = gx + 12 + ((i - 1) % GRID_COLS) * 52;
                local cy = gy + 40 + r * 52;
                draw.image(icon_tex(n), cx + 4, cy + 4);
                if i == w.grid then draw.image('slot_ring_white', cx - 4, cy - 4, { scale = 52 / 60 }); end
                w.gcells[#w.gcells + 1] = { cx, cy, 52, 52, i };
            end
        end
        -- a scroll bar along the right edge
        if total_rows > GRID_ROWS then
            local th = (gh - 56) * GRID_ROWS / total_rows;
            local ty = gy + 40 + (gh - 56 - th) * w.grid_first / (total_rows - GRID_ROWS);
            draw.rect(gx + gw - 8, gy + 40, 3, gh - 56, 0x40FFFFFF);
            draw.rect(gx + gw - 8, ty, 3, th, 0xC0C8A860);
        end
    end

    -- the bar map: placing a macro (w.place) or editing the bars (w.bars)
    local map = w.place or w.bars;
    if map then
        local hb = require('ui.hotbar');
        local nrows = hb.pages() * 2;
        local CW = 48;
        local gx, gy = x + 40, y + 120;
        local gw, gh = 130 + 10 * CW + 24, nrows * CW + 96;
        local bw, bh = layout.size('win_body');
        draw.nine('win_body', gx, gy, gw, gh, 12, bw, bh);
        draw.nine('win_body', gx, gy, gw, gh, 12, bw, bh);
        local t = ui.label('mcr_placet', 'label', { font_height = 18 });
        local what = w.place and (w.place.binding and w.place.binding.name or (m and m.name)) or '';
        text.draw(t, w.place and ('Place "' .. what .. '" on a bar') or 'Action bars', gx + 16, gy + 28, 'baseline');
        w.pcells = {};
        for r = 1, nrows do
            local page, lay = math.floor((r - 1) / 2) + 1, (r - 1) % 2 + 1;
            local ry = gy + 44 + (r - 1) * CW;
            local lab = ui.label('mcr_pl' .. r, 'small', { font_height = 16 });
            lab:set_font_color(lay == 1 and 0xFF9BE08C or 0xFFFF9080);
            text.draw(lab, (lay == 1 and 'Green ' or 'Red ') .. page, gx + 18, ry + CW - 16, 'baseline');
            for c = 1, 10 do
                local cx = gx + 120 + (c - 1) * CW;
                draw.image('slot_well', cx + 2, ry + 2, { scale = (CW - 6) / 44 });
                local bd = hb.binding_at(lay, page, c);
                local info = bd and require('core.actions').resolve(bd);
                if info and info.icon then draw.image(info.icon, cx + 2, ry + 2, { scale = (CW - 6) / 44 }); end
                if r == map.r and c == map.c then
                    draw.image('slot_ring_white', cx - 3, ry - 3, { scale = (CW + 2) / 60 });
                end
                w.pcells[#w.pcells + 1] = { cx, ry, CW, CW, r, c };
            end
        end
        local page, lay = math.floor((map.r - 1) / 2) + 1, (map.r - 1) % 2 + 1;
        local bd = hb.binding_at(lay, page, map.c);
        local info = bd and require('core.actions').resolve(bd);
        local now = info and (info.label or bd.name) or 'empty';
        local foot = ui.label('mcr_placef', 'small', { font_height = 15, font_color = 0xFFE8E4D8 });
        local keys = w.place and 'Enter: place here   Esc: cancel'
                     or 'Enter: put a macro here   Delete / RB: clear   Esc: back';
        text.draw(foot, string.format('%s %d, slot %d (now: %s).   %s', lay == 1 and 'Green' or 'Red', page, map.c, now,
            keys), gx + 18, gy + gh - 18, 'baseline');
        -- choosing which macro to put in the slot
        if w.bars and w.bars.pick then
            local list = ids();
            local px, py, pw = gx + gw + 8, gy, 280;           -- beside the map, so the chosen slot stays in view
            local ph = math.min(#list, 10) * 30 + 56;
            draw.nine('win_body', px, py, pw, ph, 12, bw, bh);
            draw.nine('win_body', px, py, pw, ph, 12, bw, bh);
            local pt = ui.label('mcr_pickt', 'label', { font_height = 17 });
            text.draw(pt, 'Put which macro here?', px + 14, py + 26, 'baseline');
            local items = {};
            for i, id in ipairs(list) do items[i] = { label = get(id).name, indent = 30 }; end
            local first = math.max(0, w.bars.pick - 10);
            w.pickrows = ui.list(w, 'mcrpick', items, w.bars.pick, px + 18, py + 38, pw - 32, 30, 10, first, true);
            for _, r in ipairs(w.pickrows) do
                local mm = get(list[r[5]]);
                if mm and mm.icon then draw.image(icon_tex(mm.icon), r[1] + 4, r[2] + 2, { scale = 24 / 44 }); end
            end
        end
    end
end

local function place_here(w)
    local id = selected_id(w);
    local m = get(id);
    if w.place and w.place.binding then
        -- an ability or spell from Abilities & Spells
        local b = w.place.binding;
        local page, lay = math.floor((w.place.r - 1) / 2) + 1, (w.place.r - 1) % 2 + 1;
        require('ui.hotbar').assign_to(lay, page, w.place.c, { kind = b.kind, name = b.name });
        require('ui.hotbar').mark_offered(b.name);
        store.save();
    elseif m and w.place then
        local page, lay = math.floor((w.place.r - 1) / 2) + 1, (w.place.r - 1) % 2 + 1;
        require('ui.hotbar').assign_to(lay, page, w.place.c, { kind = 'macro', ref = id, name = m.name });
    end
    w.place = nil;
end

win.key = function (w, vk)
    -- while typing, keys that reach the window come from the controller: they drive the on-screen keyboard
    if ti.active() then
        if ti.osk() then return ti.pad(vk); end
        return true;
    end
    if w.bars then
        local hb = require('ui.hotbar');
        local b = w.bars;
        local page, lay = math.floor((b.r - 1) / 2) + 1, (b.r - 1) % 2 + 1;
        if b.pick then
            local list = ids();
            if vk == ui.VK.UP then b.pick = (b.pick - 2) % #list + 1;
            elseif vk == ui.VK.DOWN then b.pick = b.pick % #list + 1;
            elseif vk == ui.VK.RETURN then
                local id = list[b.pick];
                if id then hb.assign_to(lay, page, b.c, { kind = 'macro', ref = id, name = get(id).name }); end
                b.pick = nil;
            elseif vk == ui.VK.ESCAPE then b.pick = nil; end
            return true;
        end
        local nrows = hb.pages() * 2;
        if vk == ui.VK.LEFT then b.c = (b.c - 2) % 10 + 1;
        elseif vk == ui.VK.RIGHT then b.c = b.c % 10 + 1;
        elseif vk == ui.VK.UP then b.r = (b.r - 2) % nrows + 1;
        elseif vk == ui.VK.DOWN then b.r = b.r % nrows + 1;
        elseif vk == ui.VK.RETURN then if #ids() > 0 then b.pick = 1; end
        elseif vk == 0x2E or vk == 0x08 or vk == ui.VK.TAB then hb.assign_to(lay, page, b.c, nil);
        elseif vk == ui.VK.ESCAPE then w.bars = nil; end
        return true;
    end
    if w.place then
        local nrows = require('ui.hotbar').pages() * 2;
        if vk == ui.VK.LEFT then w.place.c = (w.place.c - 2) % 10 + 1;
        elseif vk == ui.VK.RIGHT then w.place.c = w.place.c % 10 + 1;
        elseif vk == ui.VK.UP then w.place.r = (w.place.r - 2) % nrows + 1;
        elseif vk == ui.VK.DOWN then w.place.r = w.place.r % nrows + 1;
        elseif vk == ui.VK.RETURN then place_here(w);
        elseif vk == ui.VK.ESCAPE then w.place = nil; end
        return true;
    end
    local nlist = #ids() + 3;
    if w.acts then
        local a = w.acts;
        local cats = act_cats(w);
        local list = cats[a.cat] and a.data[cats[a.cat]] or {};
        if vk == ui.VK.UP then a.sel = (a.sel - 2) % math.max(1, #list) + 1;
        elseif vk == ui.VK.DOWN then a.sel = a.sel % math.max(1, #list) + 1;
        elseif vk == ui.VK.PRIOR then a.sel = math.max(1, a.sel - 11);
        elseif vk == ui.VK.NEXT then a.sel = math.min(#list, a.sel + 11);
        elseif vk == ui.VK.LEFT then a.cat = (a.cat - 2) % math.max(1, #cats) + 1; a.sel, a.first = 1, 0;
        elseif vk == ui.VK.RIGHT or vk == ui.VK.TAB then a.cat = a.cat % math.max(1, #cats) + 1; a.sel, a.first = 1, 0;
        elseif vk == ui.VK.RETURN then
            if list[a.sel] then
                local lay = require('ui.layers').current();
                w.place = { r = (store.data.hotbar.page - 1) * 2 + (lay or 1), c = 1, binding = list[a.sel] };
            end
        elseif vk == ui.VK.ESCAPE then w.acts = nil; end
        return true;
    end
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
            if acts_row(w) then
                if vk == ui.VK.RETURN then open_acts(w); end
                return true;
            end
            if books_row(w) then
                if vk == ui.VK.RETURN then
                    local lay = require('ui.layers').current();
                    w.bars = { r = (store.data.hotbar.page - 1) * 2 + (lay or 1), c = 1 };
                end
                return true;
            end
            if w.sel == 1 then
                new_macro();
                w.sel = #ids() + 1;
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

win.click = function (w, mx, my, button)
    if ti.active() then return true; end
    if w.bars then
        local hb = require('ui.hotbar');
        if w.bars.pick then
            for _, r in ipairs(w.pickrows or {}) do
                if ui.hit(r, mx, my) then w.bars.pick = r[5]; win.key(w, ui.VK.RETURN); return true; end
            end
            w.bars.pick = nil;
            return true;
        end
        for _, c in ipairs(w.pcells or {}) do
            if ui.hit(c, mx, my) then
                w.bars.r, w.bars.c = c[5], c[6];
                if button == 2 then
                    local page, lay = math.floor((c[5] - 1) / 2) + 1, (c[5] - 1) % 2 + 1;
                    hb.assign_to(lay, page, c[6], nil);                  -- right click clears
                elseif #ids() > 0 then
                    w.bars.pick = 1;
                end
                return true;
            end
        end
        return true;
    end
    if w.acts and not w.place then
        for _, r in ipairs(w.arows or {}) do
            if ui.hit(r, mx, my) then w.acts.sel = r[5]; win.key(w, ui.VK.RETURN); return true; end
        end
        return true;
    end
    if w.place then
        for _, c in ipairs(w.pcells or {}) do
            if ui.hit(c, mx, my) then w.place.r, w.place.c = c[5], c[6]; place_here(w); return true; end
        end
        return true;
    end
    if w.grid then
        for _, c in ipairs(w.gcells or {}) do
            if ui.hit(c, mx, my) then
                local m = get(selected_id(w));
                if m then m.icon = ICONS[c[5]]; store.save(); end
                w.grid = nil;
                return true;
            end
        end
        return true;
    end
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then
            w.sel, w.focus = r[5], 'list';
            if r[5] == 1 or books_row(w) or acts_row(w) then win.key(w, ui.VK.RETURN); end
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

win.wheel = function (w, delta)
    if w.acts and not w.place then
        win.key(w, delta > 0 and ui.VK.UP or ui.VK.DOWN);
        return;
    end
    if w.grid then
        local n = #ICONS;
        w.grid = math.max(1, math.min(n, w.grid + (delta > 0 and -GRID_COLS or GRID_COLS)));
    end
end

function M.open() ui.open(win); end

return M;
