--[[
* xiv1ui - action bar (bottom centre, above the gauges), modelled on the FFXIV 1.0 action bar:
* ten round slots with the keybind number, the action's cost, and a clockwise recast sweep with a countdown;
* a crest at the left shows the page. Slots can be clicked, triggered with keys 1..0, or with /xiv1ui use <n>.
*
* Each page has two layers, green (LT / Ctrl) and red (RT / Alt); tapping LT or RT switches, holding arms the bar
* (ui/layers.lua handles that input). The crest's shield shows the layer; flipping the page flips both. A slot holds an action, a command, or a macro (several lines, see actions.lua).
*
* Commands:
*   /xiv1ui bind <slot> <ma|ja|ws|item> <name...>    bind on the current page (e.g. /xiv1ui bind 3 ma Cure)
*   /xiv1ui bind <slot> cmd <label> <command...>     any command (e.g. /xiv1ui bind 1 cmd Attack /attack <t>)
*   /xiv1ui unbind <slot> | page <n|next|prev> | use <slot> | keys <on|off> | defaults
*   /xiv1ui import <book> <set>                       FFXI macro set -> the green (Ctrl row) and red (Alt row) layers
* bind / unbind act on the layer currently held (base if none).
--]]

local xi_now = require('core.now');
local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local actions = require('core.actions');
local store   = require('core.store');

local hotbar = {};

local SLOTS   = 10;
local PAGES   = 3;            -- 1.0 had three bars of ten, one shown at a time
local STEP    = 56;          -- distance between slot centres
local RING_W  = 60;          -- slot_ring texture content size
local WELL_IN = 8;           -- the well/disc/recast (44 px) sit this far inside the ring
local SHEET   = { size = 44, cols = 8, frames = 64 };
local KEYS    = { '1', '2', '3', '4', '5', '6', '7', '8', '9', '0' };

local objs = {};             -- per-slot text objects
local crest_num;
local tip;
local assign_obj;
local pending = nil;     -- binding waiting for a slot (assign mode), see hotbar.begin_assign
local recast_start = {};     -- slot -> timer value when the current recast began (for the sweep fraction)
local flash = {};            -- slot -> xi_now() when it was used (brief glow)
local rects = {};            -- slot -> { x, y, w, h } on screen, for mouse hit-testing
local hover = nil;

local function job() return AshitaCore:GetMemoryManager():GetPlayer():GetMainJob(); end

local function page_table(create)
    local hb = store.data.hotbar;
    local j = tostring(job());
    local p = tostring(hb.page);
    if hb.bars[j] == nil then
        if not create then return nil; end
        hb.bars[j] = T{};
    end
    if hb.bars[j][p] == nil then
        if not create then return nil; end
        hb.bars[j][p] = T{};
    end
    return hb.bars[j][p];
end

-- Layer key prefixes inside a page table: green keeps the original plain slot keys ('1'..'10'), red uses 'a1'..
local PREFIX = { '', 'a' };

-- Bars saved with the earlier three-layer scheme ('' base, 'c' LT, 'a' RT): LT bindings move into empty green slots.
local function migrate(t)
    for s = 1, 10 do
        local c = t['c' .. s];
        if c ~= nil then
            if t[tostring(s)] == nil then t[tostring(s)] = c; end
            t['c' .. s] = nil;
        end
    end
end

local function current_layer()
    return (require('ui.layers').current());
end

local function binding(slot, lay)
    local t = page_table(false);
    if t then migrate(t); end
    return t and t[PREFIX[lay or current_layer()] .. tostring(slot)] or nil;
end

local function set_binding(slot, b, lay)
    page_table(true)[PREFIX[lay or current_layer()] .. tostring(slot)] = b;
    store.save();
end

local function fill_defaults()
    local d = actions.defaults();
    for i = 1, SLOTS do set_binding(i, d[i], 1); end
end

local function apply_keys(on)
    local cm = AshitaCore:GetChatManager();
    for i, k in ipairs(KEYS) do
        if on then cm:QueueCommand(-1, string.format('/bind %s /xiv1ui use %d', k, i));
        else cm:QueueCommand(-1, '/unbind ' .. k); end
    end
    -- Shift+Up / Shift+Down cycle bars (1.0 patch 1.20)
    if on then
        cm:QueueCommand(-1, '/bind +up /xiv1ui page prev');
        cm:QueueCommand(-1, '/bind +down /xiv1ui page next');
    else
        cm:QueueCommand(-1, '/unbind +up');
        cm:QueueCommand(-1, '/unbind +down');
    end
end

local function fmt_timer(ticks)
    local s = math.ceil(ticks / 60);
    return string.format('%02d:%02d', math.floor(s / 60), s % 60);
end

function hotbar.init()
    for i = 1, SLOTS do
        objs[i] = {
            glyph = text.new('name', { font_height = 26, font_alignment = text.align.Center }),
            tier  = text.new('slotkey', { font_height = 15 }),
            key   = text.new('slotkey', { font_height = 20, font_color = 0xFFE6E0FF,       -- lavender-white
                                          font_alignment = text.align.Right }),
            cost  = text.new('slotkey', { font_height = 15 }),
            timer = text.new('timer', { font_height = 16, font_alignment = text.align.Center }),
        };
    end
    crest_num = text.new('numeral', { font_height = 24, font_color = 0xFFF2D27A, gradient_style = 0,  -- gold
                                      font_alignment = text.align.Center });
    tip = {
        name = text.new('name', { font_height = 22 }),
        kind = text.new('small', { font_color = 0xFFB8C0D8 }),
        line = text.new('small', { font_color = 0xFFF0DCA0 }),
    };
    if store.data.hotbar.keys then apply_keys(true); end
end

function hotbar.release()
    if store.data.hotbar.keys then apply_keys(false); end
end

-- Pop-up help for the hovered slot (reference: name in white italic, class line, timings with gold labels).
local function draw_tooltip(info, sx, sy)
    local lines = {};
    if info.cast then lines[#lines + 1] = string.format('Cast Time: %g sec.   Recast Time: %g sec.', info.cast, info.recast); end
    if info.cost then lines[#lines + 1] = string.format('%s Cost: %d', info.cost_kind, info.cost); end
    local w, h = 300, 34 + 20 * (#lines + 1);
    local x, y = sx - w / 2, sy - h - 12;
    -- 9-slice-free stretch: the panel art is a plain rounded rect, so scaling it is fine
    local pw, ph = layout.size('tooltip_panel');
    draw.image('tooltip_panel', x, y, { scale = { w / pw, h / ph } });
    text.draw(tip.name, info.label, x + 14, y + 30, 'baseline');
    text.draw(tip.kind, info.kind_label or '', x + 16, y + 52, 'baseline');
    for n, l in ipairs(lines) do
        text.draw(tip.line, l, x + 16, y + 52 + 20 * n, 'baseline');
    end
end

-- Newly learned actions land on the bar by themselves (like a 1.0 character's first weapon skill appearing): every
-- few seconds, anything the defaults would offer (abilities, weapon skills, spells for the current job) that isn't
-- on page 1 of either layer yet goes into the first empty green slot. Each action is added once per job, so one
-- the player removes stays removed (store.data.hotbar.offered[job][name]).
local next_learn_check = 0;
local function add_learned()
    local now = xi_now();
    if now < next_learn_check then return; end
    next_learn_check = now + 5;
    local hb = store.data.hotbar;
    if hb.page ~= 1 then return; end
    local t = page_table(false);
    if t == nil then return; end
    local j = tostring(job());
    hb.offered = hb.offered or T{};
    hb.offered[j] = hb.offered[j] or T{};
    local offered = hb.offered[j];
    local on_bar = {};
    for k, b in pairs(t) do if type(b) == 'table' and b.name then on_bar[b.name] = true; end end
    local changed = false;
    for _, b in ipairs(actions.defaults(true)) do
        if b.kind ~= 'cmd' and not on_bar[b.name] and not offered[b.name] then
            offered[b.name] = true;
            changed = true;
            for s = 1, SLOTS do
                if t[tostring(s)] == nil then
                    t[tostring(s)] = b;
                    on_bar[b.name] = true;
                    break;
                end
            end
        end
    end
    if changed then store.save(); end
end

local CREST = { 'crest_shield_green', 'crest_shield_red' };

function hotbar.render()
    if page_table(false) == nil and store.data.hotbar.page == 1 then fill_defaults(); end
    add_learned();
    local lay, armed, via_pad = require('ui.layers').current();
    local keys = KEYS;
    local sel = armed and via_pad and require('ui.layers').selected(lay) or nil;
    local tint = armed and 0xFFFFFFFF or 0xFFC4C4C4;          -- the bar brightens while armed

    local total = SLOTS * STEP;
    -- sits above the gauges (which are 40 px above the bottom edge)
    local x0, y0 = layout.anchor('bottom', total, RING_W, 30, -128, 'hotbar');
    layout.bounds('hotbar', x0 - 70, y0 - 16, total + 74, RING_W + 30);
    local now = xi_now();
    local hover_info, hover_x;

    -- navy-purple band with the gold rail through the slot centres
    local bw, bh = layout.size('bar_band');
    draw.image('bar_band', x0 + total / 2 - bw / 2 - 2, y0 + RING_W / 2 - bh / 2);

    -- crest: rose shield above a black plate holding the bar number between up/down chevrons
    local sw, sh = layout.size(CREST[lay]);
    local pw, ph = layout.size('crest_plate');
    local cx = x0 - sw - 14;
    draw.image(CREST[lay], cx, y0 - 14);
    draw.image('crest_plate', cx + (sw - pw) / 2, y0 - 14 + sh - 8);
    text.draw(crest_num, tostring(store.data.hotbar.page), cx + sw / 2, y0 - 14 + sh - 8 + ph * 0.74, 'baseline');
    rects.crest = { cx, y0 - 14, sw, sh + ph - 8 };

    for i = 1, SLOTS do
        local x = x0 + (i - 1) * STEP;
        local y = y0;
        rects[i] = { x, y, RING_W, RING_W };
        local o = objs[i];
        local info = actions.resolve(binding(i, lay));

        draw.image('slot_shadow', x, y);
        draw.image('slot_well', x + WELL_IN, y + WELL_IN, { color = tint });
        local recasting = false;
        if info then
            local dim = info.usable and tint or 0xFF6A6A6A;    -- unusable: greyed
            draw.image(info.disc, x + WELL_IN, y + WELL_IN, { color = dim });
            if info.icon then draw.image(info.icon, x + WELL_IN, y + WELL_IN, { color = dim }); end
            if info.lines then
                -- a macro: its name across the slot (or the initials if there's no icon and the name is off)
                if info.show_name then
                    -- the name across the slot: one or two lines (split at the first space), shrunk to fit the ring
                    o.mn1 = o.mn1 or text.new('slotkey', { font_height = 13, font_alignment = text.align.Center });
                    o.mn2 = o.mn2 or text.new('slotkey', { font_height = 13, font_alignment = text.align.Center });
                    local label = info.label;
                    if o.mname_for ~= label then
                        o.mname_for = label;
                        local a, b = label:match('^(%S+)%s+(.+)$');
                        if not (a and #label > 8) then a, b = label, nil; end
                        o.mn_a, o.mn_b = a, b;
                        local fh = b and 12 or 13;
                        o.mn1:set_font_height(fh); o.mn2:set_font_height(fh);
                        text.set(o.mn1, a);
                        local tw = text.size(o.mn1);
                        if b then text.set(o.mn2, b); tw = math.max(tw, (text.size(o.mn2))); end
                        if tw > RING_W - 16 then
                            fh = math.max(8, math.floor(fh * (RING_W - 16) / tw));
                            o.mn1:set_font_height(fh); o.mn2:set_font_height(fh);
                        end
                        o.mn_fh = fh;
                    end
                    local cxs, cys = x + RING_W / 2, y + RING_W / 2;
                    if o.mn_b then
                        text.draw(o.mn1, o.mn_a, cxs, cys - 1, 'baseline');
                        text.draw(o.mn2, o.mn_b, cxs, cys + o.mn_fh - 1, 'baseline');
                    else
                        text.draw(o.mn1, o.mn_a, cxs, cys + o.mn_fh * 0.35, 'baseline');
                    end
                elseif not info.icon then
                    text.draw(o.glyph, info.glyph, x + RING_W / 2, y + RING_W / 2 + 10, 'baseline');
                end
            elseif info.timer == 0 and not info.icon then   -- the countdown replaces the letters while recasting
                text.draw(o.glyph, info.glyph, x + RING_W / 2, y + RING_W / 2 + 10, 'baseline');
                if info.tier ~= '' then text.draw(o.tier, info.tier, x + RING_W / 2 + 10, y + RING_W / 2 + 14, 'baseline'); end
            end

            -- recast: dimmed icon with a cyan arc for the time remaining, and an mm:ss countdown
            if info.timer > 0 then
                recasting = true;
                if recast_start[i] == nil or info.timer > recast_start[i] then recast_start[i] = info.timer; end
                local frac = info.timer / recast_start[i];
                local fr = math.min(SHEET.frames - 1, math.floor((1 - frac) * SHEET.frames));
                draw.image('recast_sheet', x + WELL_IN, y + WELL_IN, {
                    sx = (fr % SHEET.cols) * SHEET.size, sy = math.floor(fr / SHEET.cols) * SHEET.size,
                    sw = SHEET.size, sh = SHEET.size });
                text.draw(o.timer, fmt_timer(info.timer), x + RING_W / 2, y + RING_W / 2 + 6, 'baseline');
            else
                recast_start[i] = nil;
            end
        end

        -- ring state: gold = highlighted (hover / just used), blue = use condition met, plain otherwise
        local f = flash[i] and (now - flash[i]) or 99;
        local ring = 'slot_ring';
        local padsel = require('core.pad').bar_cursor == i;
        if hover == i or f < 0.35 or padsel then ring = 'slot_ring_gold';
        elseif info and info.motif == 'motif_sword' and info.kind_label == 'Weapon Skill' and info.usable
                and require('core.world').combo_left() then
            ring = 'slot_ring_pink';                       -- combo-ready (skillchain window open)
        elseif info and info.ready and not recasting then ring = 'slot_ring_blue'; end
        if sel == i then ring = 'slot_ring_white'; end    -- the controller's selection while armed
        draw.image(ring, x, y, { color = (ring == 'slot_ring') and tint or nil });

        -- weapon motif under the icon, carrying the cost (lower left) and slot number (lower right)
        draw.image(info and info.motif or 'motif_sword', x + 1, y + RING_W - 10,
                   { color = info and 0xFFFFFFFF or 0x80FFFFFF });
        text.draw(o.key, keys[i], x + RING_W - 4, y + RING_W + 9, 'baseline');
        if info and info.cost then
            local col = info.cost_kind == 'TP' and 0xFF8CE6F0 or 0xFFC8F0A0;    -- cyan TP, pale green MP
            if not info.usable then col = 0xFFFF7060; end
            if o.cost.settings.font_color ~= col then o.cost:set_font_color(col); end
            text.draw(o.cost, tostring(info.cost), x + 6, y + RING_W + 8, 'baseline');
        end

        if padsel then
            draw.image('cursor_gold', x + RING_W / 2 - 14, y - 22, { rot = -math.pi / 2 });  -- pointing down at the slot (D3DX rotates counter-clockwise)
            if info then hover_info, hover_x = info, x + RING_W / 2; end
        end
        if hover == i and info then hover_info, hover_x = info, x + RING_W / 2; end
    end

    if pending then
        local a = 0.5 + 0.5 * math.abs(math.sin(now * 4));
        for i = 1, SLOTS do
            draw.image('slot_ring_gold', x0 + (i - 1) * STEP, y0, { color = draw.alpha(0xFFFFFFFF, a) });
        end
        if not assign_obj then assign_obj = text.new('label', { font_height = 18, font_color = 0xFFF0DCA0,
                                                                  font_alignment = text.align.Center }); end
        local pc = require('core.pad').assign_cursor;
        if pc then draw.image('slot_ring_white', x0 + (pc - 1) * STEP, y0); end
        text.draw(assign_obj, 'Choose a slot for ' .. (pending.label or pending.name)
                  .. ':  1–0, click, or D-pad + A   (Esc / B cancels)', x0 + total / 2, y0 - 22, 'baseline');
    elseif hover_info and store.data.popup_help ~= false then draw_tooltip(hover_info, hover_x, y0 - 16); end
end

local function hit(x, y)
    for i, r in pairs(rects) do
        if i == 'crest' then goto continue; end
        if x >= r[1] and x < r[1] + r[3] and y >= r[2] and y < r[2] + r[4] then return i; end
        ::continue::
    end
    local c = rects.crest;
    if c and x >= c[1] and x < c[1] + c[3] and y >= c[2] and y < c[2] + c[4] then return 'crest'; end
    return nil;
end

-- Assign mode (from the Actions & Traits window): the next slot chosen receives this binding instead of firing.
function hotbar.begin_assign(b) pending = b; end
function hotbar.assigning() return pending ~= nil; end
function hotbar.cancel_assign() pending = nil; end

local function use(slot)
    if pending then
        if slot >= 1 and slot <= SLOTS then
            set_binding(slot, pending);
            flash[slot] = xi_now();
        end
        pending = nil;
        return;
    end
    local b = binding(slot);
    if b and actions.use(b) then flash[slot] = xi_now(); end
end
hotbar.use = use;

--- Fire slot (1..10) of a layer (1 base, 2 LT/Ctrl, 3 RT/Alt) on the current page.
function hotbar.use_layer(lay, slot)
    local b = binding(slot, lay);
    if b and actions.use(b) then flash[slot] = xi_now(); end
end

--- Flip the page (all layers together) by +1 / -1.
function hotbar.page_step(d)
    local hb = store.data.hotbar;
    hb.page = (hb.page - 1 + d) % PAGES + 1;
    store.save();
end

--- Copy an FFXI macro set (the game's own macro files) onto this page's LT (Ctrl row) and RT (Alt row) layers.
function hotbar.import(book, set)
    local m = require('core.macros').load(book, set);
    for i = 1, 20 do
        local lay, slot = (i <= 10) and 1 or 2, (i - 1) % 10 + 1;
        local src = m[i];
        if src and #src.lines > 0 then
            set_binding(slot, { kind = 'macro', name = src.title_utf8 ~= '' and src.title_utf8 or ('Macro ' .. i),
                                lines = src.lines, show_name = true }, lay);
        else
            set_binding(slot, nil, lay);
        end
    end
end

--- Development aid: pretend the mouse is over slot n (nil to clear), for screenshots.
function hotbar.dev_hover(n) hover = n; end

function hotbar.mouse(e)
    local i = hit(e.x, e.y);
    if e.message == 0x200 then hover = type(i) == 'number' and i or nil; return; end  -- WM_MOUSEMOVE
    if i == nil then return; end
    if i == 'crest' then                                         -- click the crest: next bar
        if e.message == 0x201 then e.blocked = true;
        elseif e.message == 0x202 then
            e.blocked = true;
            store.data.hotbar.page = store.data.hotbar.page % PAGES + 1;
            store.save();
        end
        return;
    end
    if e.message == 0x201 then e.blocked = true;                 -- WM_LBUTTONDOWN
    elseif e.message == 0x202 then e.blocked = true; use(i); end -- WM_LBUTTONUP
end

function hotbar.command(args)
    local cmd = (args[2] or ''):lower();
    local hb = store.data.hotbar;
    if cmd == 'use' then
        use(tonumber(args[3]) or 0);
    elseif cmd == 'page' then
        local v = (args[3] or ''):lower();
        if v == 'next' then hb.page = hb.page % PAGES + 1;
        elseif v == 'prev' then hb.page = (hb.page - 2) % PAGES + 1;
        else hb.page = math.max(1, math.min(PAGES, tonumber(v) or hb.page)); end
        store.save();
    elseif cmd == 'bind' then
        local slot, kind = tonumber(args[3]), (args[4] or ''):lower();
        if not slot or slot < 1 or slot > SLOTS then return; end
        if kind == 'cmd' then
            set_binding(slot, { kind = 'cmd', name = args[5] or 'Cmd', command = table.concat(args, ' ', 6) });
        elseif kind == 'ma' or kind == 'ja' or kind == 'ws' or kind == 'item' then
            set_binding(slot, { kind = kind, name = table.concat(args, ' ', 5) });
        end
    elseif cmd == 'unbind' then
        local slot = tonumber(args[3]);
        if slot then set_binding(slot, nil); end
    elseif cmd == 'defaults' then
        fill_defaults();
    elseif cmd == 'import' then
        local book, set = tonumber(args[3]), tonumber(args[4]);
        if book and set then hotbar.import(book, set); end
    elseif cmd == 'keys' then
        hb.keys = (args[3] or ''):lower() == 'on';
        apply_keys(hb.keys);
        store.save();
    end
end

return hotbar;
