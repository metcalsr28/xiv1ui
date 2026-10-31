--[[
* xiv1ui - the knocked-out screen, in place of FFXI's small "Time Left / Back to Home Point" box.
*
* The game keeps running its window ("menu    dead"): Enter / A still returns you to your home point, and a Raise
* still brings up the game's own prompt. xiv1ui hides the box and draws a full-screen treatment: a dark crimson
* vignette, a band across the screen with "Knocked Out", who defeated you (from the battle log), the time left to be
* raised (the window's class object counts it down at +0x20, in 60ths of a second, from 60 minutes) as a draining
* line, and the menu's options as buttons, the selected one glowing. The options are read from the game's rows and
* named from their help texts: the game has two, "...return to your current home point" and "...return to your
* camp" (Campaign / Besieged areas); a Raise comes as the game's own separate prompt. Clicking a button chooses it
* (the game's cursor is moved to it and it is confirmed with the same key presses as the keyboard).
*
* Configuration » General » Knocked Out screen: Minimal draws the same things in a small panel instead (no
* darkened screen, no band).
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local store   = require('core.store');
local mem     = require('core.mem');
local native  = require('core.native');
local gamewin = require('core.gamewin');
local xi_now  = require('core.now');

local death = {};

local hider = gamewin.new();
local shown_since = nil;
local killer = nil;           -- "the Huge Hornet", from "<you> was defeated by the Huge Hornet."
local FULL = 60 * 60 * 60;    -- the game's countdown starts at 60 minutes (in 60ths of a second)

function death.release() hider:restore(); end

function death.text_in(e)
    local s = e.message_modified or e.message or '';
    local me = AshitaCore:GetMemoryManager():GetParty():GetMemberName(0) or '';
    if me == '' then return; end
    s = s:gsub('\30.', ''):gsub('\31.', ''):gsub('[%c]', '');
    local who = s:match(me .. ' was defeated by (.-)%.');
    if who then killer = who; end
end

local function time_left()
    local slot = gamewin.slot('dead');
    local cls = slot and mem.u32(slot);
    local v = cls and mem.u32(cls + 0x20);
    if v == nil or v > FULL * 2 then return nil; end
    return v / 60;
end

-- An option's label from its help text (the game draws the labels as pictures; the help texts are the only words).
local function label_of(help)
    if help:find('your camp') then return 'Return to Camp'; end
    if help:find('home point') then return 'Return to Home Point'; end
    return (help:match('^[^%.,]+') or help);
end

--- The death menu's options: { label, sel }, in screen order.
local function options()
    local w = gamewin.window('dead');
    if w == nil then return {}; end
    local cur = mem.u32(w + 0x08);
    local out, seen = {}, {};
    for _, r in ipairs(gamewin.rows(w)) do
        local e = mem.u32(r + 0x0C);
        local h = e and mem.u32(e + 8);
        local help = (h and mem.ok(h, 8)) and (ashita.memory.read_string(h, 160) or ''):match('^[^%z]*') or '';
        local n = mem.u16(r + 0x3A);
        if help ~= '' and n and not seen[n] then
            seen[n] = true;
            out[#out + 1] = { y = mem.u16(r + 0x2C) or 0, label = label_of(help), sel = (r == cur) };
        end
    end
    table.sort(out, function (a, b) return a.y < b.y; end);
    if #out == 1 then out[1].sel = true; end
    return out;
end

local function sel_index(opts)
    for i, o in ipairs(opts) do if o.sel then return i; end end
    return 1;
end

-- Clicking a button: the game's cursor is moved to that option (Up / Down) and it is confirmed (Enter), the same
-- presses the keyboard would make.
local buttons, hover = {}, nil;     -- { x, y, w, h, index, selected index, key back, key on } (HUD units)
function death.mouse(e)
    if gamewin.window('dead') == nil then hover = nil; return; end
    local hit = nil;
    for _, b in ipairs(buttons) do
        if e.x >= b[1] and e.x < b[1] + b[3] and e.y >= b[2] and e.y < b[2] + b[4] then hit = b; end
    end
    if e.message == 0x200 then hover = hit and hit[5] or nil; return; end
    if hit == nil then return; end
    if e.message == 0x201 then e.blocked = true;
    elseif e.message == 0x202 then
        e.blocked = true;
        local gamein = require('ui.gamein');
        local d = hit[5] - hit[6];
        for _ = 1, math.abs(d) do gamein.press(d > 0 and hit[8] or hit[7]); end
        gamein.press(0x1C);
    end
end

local function centred(key, style, size, color)
    return ui.label(key, style, { font_height = size, font_color = color, font_alignment = text.align.Center });
end

-- The game's yes / no window ("menu    comyn") when it asks to confirm: its question is a string its class object
-- points to at +0x1C; Yes and No are its two rows, and the window's +0x4C is the cursor (1 Yes, 2 No).
local function question()
    local w = gamewin.window('comyn');
    if w == nil then return nil; end
    local slot = gamewin.slot('comyn');
    local cls = slot and mem.u32(slot);
    local p = cls and mem.u32(cls + 0x1C);
    local txt = (p and mem.ok(p, 8)) and (ashita.memory.read_string(p, 120) or ''):match('^[^%z]*') or '';
    local c = mem.u32(w + 0x4C);
    if txt == '' or c == nil or c < 1 or c > 2 then return nil; end
    return { text = txt, cursor = c };
end

-- One button: the selected one glows (pulsing), a hovered one glows faintly. Recorded for clicks with the keys that
-- move the game's cursor back / forward.
local function button(i, px, py, w, h, label, sel, ease, now, sel_i, key_prev, key_next)
    local gw, gh = layout.size('button_glow');
    local bw, bh = layout.size('wide_button');
    local sx = (w + gw - bw) / gw;
    buttons[#buttons + 1] = { px, py, w, h, i, sel_i, key_prev, key_next };
    local glow = sel and (0.75 + 0.25 * math.sin(now * 3)) or (hover == i and 0.5 or 0);
    if glow > 0 then
        for _ = 1, sel and 3 or 1 do      -- layered: one pass is too faint over a bright scene
            draw.image('button_glow', px - (gw * sx - w) / 2, py - (gh - h) / 2,
                { scale = { sx, 1 }, color = draw.alpha(0xFFFFFFFF, ease * glow) });
        end
    end
    draw.image('wide_button', px, py, { scale = { w / bw, h / bh },
        color = draw.alpha(sel and 0xFFFFFFFF or 0xFF9A9A9A, ease * (sel and 1 or 0.7)) });
    local t = centred('death_btn' .. i, 'label', 20, sel and 0xFFFFF4E4 or 0xFFB8B0A8);
    if t.settings.font_color ~= (sel and 0xFFFFF4E4 or 0xFFB8B0A8) then t:set_font_color(sel and 0xFFFFF4E4 or 0xFFB8B0A8); end
    t:set_opacity(ease);
    text.draw(t, label, px + w / 2, py + h / 2 + 7, 'baseline');
end


function death.render()
    if store.data.cmd_menu == false or gamewin.window('dead') == nil then
        if hider:active() then hider:restore(); end
        shown_since, buttons, hover = nil, {}, nil;
        return;
    end
    hider:hide({ 'dead', 'comyn', 'helpwind', 'titlewin' });      -- (+ the game's help bar across the top)
    local now = xi_now();
    shown_since = shown_since or now;
    local t = math.min(1, (now - shown_since) / 1.2);
    local ease = 1 - (1 - t) ^ 3;
    local sw, sh = layout.screen();
    if store.data.death_minimal == true then return death.render_minimal(ease, now, sw, sh); end

    -- the whole screen darkens toward the edges
    local vw, vh = layout.size('death_vignette');
    draw.image('death_vignette', 0, 0, { scale = { sw / vw, sh / vh }, color = draw.alpha(0xFFFFFFFF, ease) });

    -- the band across the screen
    local bw, bh = layout.size('death_band');
    local BH = 230;
    local by = math.floor(sh * 0.40 - BH / 2);
    draw.image('death_band', 0, by, { scale = { sw / bw, BH / bh }, color = draw.alpha(0xFFFFFFFF, ease) });
    local cx = sw / 2;

    local title = centred('death_title', 'name', 58, 0xFFF2E6E0);
    title:set_opacity(ease);
    text.draw(title, 'Knocked Out', cx, by + 78 - (1 - ease) * 12, 'baseline');

    local sub = centred('death_sub', 'small', 20, 0xFFC8B8B0);
    sub:set_opacity(ease);
    text.draw(sub, killer and ('Defeated by ' .. killer .. '.') or 'You have been defeated.', cx, by + 112, 'baseline');

    -- time left to be raised, as a line that drains
    local left = time_left();
    if left then
        local LW = 420;
        local lx, ly = cx - LW / 2, by + 140;
        local pct = math.max(0, math.min(1, left / (FULL / 60)));
        local hw, hh = layout.size('hair_line');
        draw.image('hair_line', lx, ly, { scale = { LW / hw, 1 }, color = draw.alpha(0x38FFFFFF, ease) });
        if pct > 0 then
            draw.image('hair_line', lx + LW * (1 - pct) / 2, ly, { scale = { LW * pct / hw, 1 }, color = draw.alpha(0xFFE8B878, ease) });
        end
        local secs = math.floor(left);
        local tm = centred('death_time', 'small', 17, 0xFFE8D8C8);
        tm:set_opacity(ease);
        text.draw(tm, string.format('Raise possible for %d:%02d', math.floor(secs / 60), secs % 60), cx, ly + 32, 'baseline');
    end

    buttons = {};
    local bw2, bh2 = layout.size('wide_button');
    local q = question();
    if q then
        -- the game asks to confirm ("Return to Home Point?"): its question, and Yes / No side by side
        local qt = centred('death_q', 'name', 26, 0xFFF4ECE0);
        qt:set_opacity(ease);
        text.draw(qt, q.text, cx, by + BH + 40, 'baseline');
        local W = 170;
        for i, label in ipairs({ 'Yes', 'No' }) do
            local px = cx - W - 10 + (i - 1) * (W + 20);
            button(i, px, by + BH + 58, W, bh2, label, q.cursor == i, ease, now, q.cursor, 0xCB, 0xCD);
        end
        return;
    end
    -- the menu's options, as the game has them (its rows, with the selected one glowing); confirming still goes
    -- to the game's menu
    local opts = options();
    local si = sel_index(opts);
    for i, o in ipairs(opts) do
        button(i, cx - bw2 / 2, by + BH + 24 + (i - 1) * (bh2 + 14), bw2, bh2, o.label, o.sel, ease, now, si, 0xC8, 0xD0);
    end
end

-- The minimal style: a small panel a little below the middle of the screen with the same contents.
function death.render_minimal(ease, now, sw, sh)
    local W = 400;
    local q = question();
    local opts = q and {} or options();
    local nbtn = q and 1 or #opts;
    local BH2 = 36;
    local H = 118 + nbtn * (BH2 + 10) + (q and 34 or 0);
    local x, y = (sw - W) / 2, math.floor(sh * 0.56);
    local pw, ph = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, pw, ph, draw.alpha(0xFFFFFFFF, ease));
    local cx = x + W / 2;
    local title = centred('death_title_m', 'name', 30, 0xFFF2C8C0);
    title:set_opacity(ease);
    text.draw(title, 'Knocked Out', cx, y + 40, 'baseline');
    local sub = centred('death_sub_m', 'small', 17, 0xFFC8B8B0);
    sub:set_opacity(ease);
    text.draw(sub, killer and ('Defeated by ' .. killer .. '.') or 'You have been defeated.', cx, y + 64, 'baseline');
    local left = time_left();
    if left then
        local secs = math.floor(left);
        local tm = centred('death_time_m', 'small', 15, 0xFFE8D8C8);
        tm:set_opacity(ease);
        text.draw(tm, string.format('Raise possible for %d:%02d', math.floor(secs / 60), secs % 60), cx, y + 86, 'baseline');
    end
    buttons = {};
    local by = y + 100;
    if q then
        local qt = centred('death_q_m', 'label', 19, 0xFFF4ECE0);
        qt:set_opacity(ease);
        text.draw(qt, q.text, cx, by + 22, 'baseline');
        local BW = 150;
        for i, label in ipairs({ 'Yes', 'No' }) do
            button(i, cx - BW - 8 + (i - 1) * (BW + 16), by + 34, BW, BH2, label, q.cursor == i, ease, now, q.cursor, 0xCB, 0xCD);
        end
        return;
    end
    local si = sel_index(opts);
    for i, o in ipairs(opts) do
        button(i, cx - 150, by + (i - 1) * (BH2 + 10), 300, BH2, o.label, o.sel, ease, now, si, 0xC8, 0xD0);
    end
end

return death;
