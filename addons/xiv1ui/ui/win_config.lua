--[[
* xiv1ui - Configuration window (reference §38): xiv1ui's own settings on tabs (General, Chat, HUD, Controls).
* ↑/↓ choose a setting, Enter or click changes it (settings with several values step with ←/→ too); Tab / Page Down
* and Page Up switch tabs, or click a tab. Opened from the Main Menu, the gear in the bottom-right buttons, or
* /xiv1ui config.
--]]

local ui     = require('core.ui');
local text   = require('core.text');
local store  = require('core.store');
local draw   = require('core.draw');
local layout = require('core.layout');

local M = {};

-- A setting that steps through a list of values. get() reads the current value, put(v) stores it; show(v) formats.
local function stepper(label, values, get, put, show)
    local function step(dir)
        local cur, at = get(), nil;
        for i, v in ipairs(values) do
            if (type(v) == 'number' and type(cur) == 'number' and math.abs(v - cur) < 0.001) or v == cur then at = i; end
        end
        at = (at or 0) + dir;
        if at > #values then at = 1; elseif at < 1 then at = #values; end
        put(values[at]);
        store.save();
    end
    return { label = label, value = function () return show(get()); end, step = step };
end

local function flag(label, key, default_on)
    return { label = label,
             get = function () if default_on then return store.data[key] ~= false; end return store.data[key] == true; end,
             set = function (v) store.data[key] = v; store.save(); end };
end

local function pct(v) return string.format('%d%%', math.floor((v or 1) * 100 + 0.5)); end

-- chat settings live in store.data.chat (defaults come from ui/chatlog.lua)
local function chat_get(key) return function () return require('ui.chatlog').cfg()[key]; end; end
local function chat_put(key)
    return function (v) store.data.chat = store.data.chat or {}; rawset(store.data.chat, key, v); end;
end
local function chat_flag(label, key)
    return { label = label, get = chat_get(key),
             set = function (v) chat_put(key)(v); store.save(); end };
end

-- HUD part sizes live in store.data.part_scale (read by xiv1ui.lua)
local PART_SIZES = {};
for v = 60, 160, 5 do PART_SIZES[#PART_SIZES + 1] = v / 100; end         -- 60% to 160% in 5% steps
local function part(label, key)
    return stepper(label, PART_SIZES,
        function () return rawget(store.data.part_scale or {}, key) or 1; end,
        function (v) store.data.part_scale = store.data.part_scale or {}; store.data.part_scale[key] = v; end, pct);
end

-- a channel shown in the logs or not (store.data.chat.hide[channel])
local function channel(label, ch)
    return { label = label,
             get = function () return not (require('ui.chatlog').cfg().hide[ch]); end,
             set = function (v)
                 store.data.chat = store.data.chat or {};
                 store.data.chat.hide = store.data.chat.hide or {};
                 rawset(store.data.chat.hide, ch, (not v) or nil);
                 store.save();
             end };
end

-- the action bar group's sideways position: 10 px steps, 600 either way
local OFFSETS = {};
for v = -600, 600, 10 do OFFSETS[#OFFSETS + 1] = v; end

local function font_values()
    local out = {};
    for _, f in ipairs(require('ui.chatlog').FONTS) do out[#out + 1] = f.id; end
    return out;
end
local function font_label(id)
    for _, f in ipairs(require('ui.chatlog').FONTS) do if f.id == id then return f.label; end end
    return id;
end

local TABS = {
    { title = 'General', rows = {
        stepper('Window style', { 'gold', 'classic' }, function () return store.data.theme or 'gold'; end,
            function (v) store.data.theme = v; end, function (v) return v == 'classic' and 'Classic' or 'Modern'; end),
        stepper('UI scale (everything)', draw.SCALES, function () return store.data.ui_scale or 1; end,
            function (v) store.data.ui_scale = v; end, pct),
        stepper('Minimum text size (labels, numbers, timers)', { 0, 16, 18, 20 },
            function () return store.data.min_text or 0; end, function (v) store.data.min_text = v; end,
            function (v) return v == 0 and 'Off' or (v .. ' px'); end),
        flag('Names over characters in the HUD font', 'nameplates', true),
        flag('Popup help when hovering actions and buttons', 'popup_help', true),
        stepper('Dialogue box font', font_values(), function () return store.data.dlg_font or 'serif'; end,
            function (v) store.data.dlg_font = v; end, font_label),
        stepper('Dialogue box text size', { 16, 17, 18, 19, 20, 22, 24, 26, 28 },
            function () return store.data.dlg_size or 20; end, function (v) store.data.dlg_size = v; end,
            function (v) return v .. ' px'; end),
        stepper('Knocked Out screen', { false, true }, function () return store.data.death_minimal == true; end,
            function (v) store.data.death_minimal = v; end, function (v) return v and 'Minimal' or 'Full'; end),
        flag('Hide the game\'s own panels that xiv1ui replaces', 'hide_native', true),
        flag('Area map in the minimap', 'minimap_hd', true),
        flag('Configuration button in the bottom-right buttons', 'config_button', true),
    } },
    { title = 'Chat', rows = {
        stepper('Font', font_values(), chat_get('font'), chat_put('font'), font_label),
        stepper('Text size', { 12, 13, 14, 15, 16, 17, 18, 20, 22, 24, 26, 28 }, chat_get('size'), chat_put('size'),
            function (v) return v .. ' px'; end),
        stepper('Line spacing', { 0, 1, 2, 3, 4, 6, 8 }, chat_get('spacing'), chat_put('spacing'),
            function (v) return v .. ' px'; end),
        stepper('Text outline', { 0, 1, 2, 3 }, chat_get('outline'), chat_put('outline'),
            function (v) return ({ [0] = 'None', 'Thin', 'Normal', 'Heavy' })[v] or tostring(v); end),
        stepper('Background', { 0, 0.25, 0.5, 0.65, 0.85, 1 }, chat_get('bg'), chat_put('bg'), pct),
        chat_flag('Repeated lines shown once, with a count', 'collapse'),
        chat_flag('Timestamps', 'stamps'),
        chat_flag('Battle text in the General log (one log)', 'merge'),
        flag('Logs fade out after 60 seconds of quiet', 'chat_autohide', true),
        channel('Show shouts and yells', 'shout'),
        channel('Show linkshell chat', 'linkshell'),
        channel('Show emotes', 'emote'),
        channel('Show NPC lines (also in the dialogue box)', 'npc'),
        { label = 'Reset the logs\' size (drag a log\'s top-right corner to resize)', action = true,
          value = function () return ''; end,
          step = function ()
              local c = store.data.chat or {};
              c.w, c.h1, c.h2 = nil, nil, nil;
              store.data.chat = c;
              store.save();
          end },
    } },
    { title = 'HUD', rows = {
        part('Action bar, gauges and cast bar', 'bars'),
        part('Target frame and status', 'target'),
        part('Party list', 'party'),
        part('Minimap', 'minimap'),
        part('Bottom-right buttons', 'buttons'),
        stepper('Action bar group position (left / right)', OFFSETS,
            function () return rawget(store.data.part_offset or {}, 'bars') or 0; end,
            function (v) store.data.part_offset = store.data.part_offset or {}; rawset(store.data.part_offset, 'bars', v); end,
            function (v) return v == 0 and 'Centre' or string.format('%+d', v); end),
        flag('UI Lock (widgets can\'t be dragged)', 'ui_locked', false),
        { label = 'Reset UI positions', action = true, value = function () return ''; end,
          step = function () layout.reset(); end },
        { label = 'Reset HUD sizes', action = true, value = function () return ''; end,
          step = function () store.data.part_scale = nil; store.data.part_offset = nil; store.save(); end },
    } },
    { title = 'Experimental', note = 'Features still in development. They change how the game works, not only how it looks. '
                                     .. 'In-game updates download and install files from the internet: likely safe, but '
                                     .. 'use them at your own risk.',
      rows = {
        flag('Enable experimental options', 'experimental', false),
        { label = 'Actions & Traits window in the Main Menu', needs = 'experimental',
          get = function () return store.data.extras == true; end,
          set = function (v) store.data.extras = v; store.save(); end },
        { label = 'In-game updates (/xiv1ui update) - at your own risk', needs = 'experimental',
          get = function () return store.data.updater == true; end,
          set = function (v) store.data.updater = v; store.save(); end },
    } },
    { title = 'Controls', rows = {
        { label = 'Number keys fire the action bar (1–0, Shift+↑/↓ pages)',
          get = function () return store.data.hotbar.keys; end,
          set = function (v) AshitaCore:GetChatManager():QueueCommand(-1, '/xiv1ui keys ' .. (v and 'on' or 'off')); end },
        { label = 'Action bar layers on Ctrl/Alt and LT/RT (macro palettes)',
          get = function () return store.data.macro.palette == true; end,
          set = function (v) store.data.macro.palette = v; store.save(); end },
        flag('Controller drives xiv1ui (Back+X menu, Back+A action bar)', 'pad', true),
        flag('Command menu (Enter / A) in the FF style', 'cmd_menu', true),
        flag('Event choices (Yes / No, NPC options) in the FF style', 'choice_menu', true),
        flag('Status window in the FF style', 'status_panel', true),
    } },
};

local ROW_H, TAB_H = 28, 34;
local most = 0;
for _, t in ipairs(TABS) do most = math.max(most, #t.rows); end
local win = { id = 'config', title = 'Configuration', w = 640, sel = 1, tab = 1, rows = {}, tabs = {} };
win.h = 52 + TAB_H + 16 + most * ROW_H + 24 + 40;      -- (+ room for a tab's note under its rows)

local function rows() return TABS[win.tab].rows; end

win.draw = function (w, x, y)
    local focused = ui.top() == w;
    -- tabs: the current one lit, the others dim
    w.tabs = {};
    local tx = x + 24;
    for i, t in ipairs(TABS) do
        local o = ui.label('cfgtab' .. i, 'label', { font_height = 18 });
        if o.settings.text ~= t.title then text.set(o, t.title); end
        local tw = text.size(o);
        local bw = tw + 32;
        local on = i == w.tab;
        draw.rect(tx, y + 48, bw, TAB_H - 6, on and 0x60C8A860 or 0x30000000);
        if on then draw.rect(tx, y + 48 + TAB_H - 8, bw, 2, 0xFFC8A860); end
        o:set_font_color(on and 0xFFF4EBD0 or 0xFFA8A49A);
        text.draw(o, t.title, tx + 16, y + 48 + TAB_H - 13, 'baseline');
        w.tabs[i] = { tx, y + 48, bw, TAB_H - 6 };
        tx = tx + bw + 6;
    end
    local items = {};
    for i, o in ipairs(rows()) do
        if o.value then
            items[i] = { label = o.label, right = o.value(), color = 0xFFF4F0E6 };
        else
            local on = o.get();
            items[i] = { label = o.label, right = on and 'On' or 'Off', color = on and 0xFFF4F0E6 or 0xFFB0B4C0 };
        end
        -- a row that needs another setting on (the experimental options) is greyed out until it is
        if o.needs and store.data[o.needs] ~= true then items[i].disabled = true; end
    end
    if TABS[w.tab].note then
        local n = ui.label('cfgnote', 'small', { font_height = 15, font_color = 0xFFC8A860, box_width = w.w - 80 });
        if n.settings.text ~= TABS[w.tab].note then text.set(n, TABS[w.tab].note); end
        local _, nh = text.size(n);
        text.render(n, x + 40, y + w.h - 18 - nh);      -- (measured: the note wraps to two lines)
    end
    w.rows = ui.list(w, 'cfg' .. w.tab, items, w.sel, x + 40, y + 52 + TAB_H + 12, w.w - 70, ROW_H, #items, 0, focused);
end

local function change(i, dir)
    local o = rows()[i];
    if o == nil or (o.needs and store.data[o.needs] ~= true) then return; end
    if o.step then o.step(dir or 1);
    else o.set(not o.get()); end
end

local function set_tab(t)
    win.tab = (t - 1) % #TABS + 1;
    win.sel = 1;
end

win.key = function (w, vk)
    local n = #rows();
    if vk == ui.VK.UP then w.sel = (w.sel - 2) % n + 1;
    elseif vk == ui.VK.DOWN then w.sel = w.sel % n + 1;
    elseif vk == ui.VK.RETURN then change(w.sel, 1);
    elseif vk == ui.VK.TAB or vk == ui.VK.NEXT then set_tab(w.tab + 1);
    elseif vk == ui.VK.PRIOR then set_tab(w.tab - 1);
    elseif (vk == ui.VK.LEFT or vk == ui.VK.RIGHT) and rows()[w.sel].step and not rows()[w.sel].action then
        change(w.sel, vk == ui.VK.LEFT and -1 or 1);
    elseif vk == ui.VK.ESCAPE then return false; end
    return true;
end

win.click = function (w, mx, my, button)
    for i, r in ipairs(w.tabs) do
        if ui.hit(r, mx, my) then set_tab(i); return; end
    end
    for _, r in ipairs(w.rows) do
        -- left click steps forward, right click back
        if ui.hit(r, mx, my) then w.sel = r[5]; change(r[5], button == 2 and -1 or 1); return; end
    end
end

function M.open() ui.open(win); end
function M.toggle() ui.toggle(win); end

return M;
