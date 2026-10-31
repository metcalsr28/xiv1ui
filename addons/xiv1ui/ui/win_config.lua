--[[
* xiv1ui - Configuration window (reference §38): xiv1ui's own settings in sections (Appearance, Chat, HUD, Menus,
* Controls, Layout). ↑/↓ choose, Enter or click toggles; settings with several values step with ←/→ or Enter/click.
* Opened from the Main Menu, the gear in the bottom-right menu, or /xiv1ui config.
--]]

local ui    = require('core.ui');
local text  = require('core.text');
local store = require('core.store');
local draw  = require('core.draw');

local M = {};

-- UI scale: step through draw.SCALES (dir = +1 / -1, wrapping when stepping up from the largest)
local function step_scale(dir)
    local cur, at = store.data.ui_scale or 1, 1;
    for i, v in ipairs(draw.SCALES) do if math.abs(v - cur) < 0.001 then at = i; end end
    at = at + dir;
    if at > #draw.SCALES then at = 1; elseif at < 1 then at = 1; end
    store.data.ui_scale = draw.SCALES[at];
    store.save();
end

local CHAT_SIZES = { 16, 18, 20, 22 };
local function step_chat(dir)
    local cur, at = store.data.chat_size or 16, 1;
    for i, v in ipairs(CHAT_SIZES) do if v == cur then at = i; end end
    at = at + dir;
    if at > #CHAT_SIZES then at = 1; elseif at < 1 then at = 1; end
    store.data.chat_size = CHAT_SIZES[at];
    store.save();
end

local MIN_SIZES = { 0, 16, 18, 20 };
local function step_min(dir)
    local cur, at = store.data.min_text or 0, 1;
    for i, v in ipairs(MIN_SIZES) do if v == cur then at = i; end end
    at = at + dir;
    if at > #MIN_SIZES then at = 1; elseif at < 1 then at = 1; end
    store.data.min_text = MIN_SIZES[at];
    store.save();
end

local function step_theme()
    store.data.theme = (store.data.theme or 'gold') == 'gold' and 'classic' or 'gold';
    store.save();
end

local function flag(key, default_on)
    return function () if default_on then return store.data[key] ~= false; end return store.data[key] == true; end,
           function (v) store.data[key] = v; store.save(); end;
end
local function opt(label, key, default_on)
    local get, set = flag(key, default_on);
    return { label = label, get = get, set = set };
end

-- The settings, by section. A row has value+step (a choice to step through) or get+set (On / Off).
local SECTIONS = {
    { title = 'Appearance', rows = {
        { label = 'Window style',
          value = function () return (store.data.theme or 'gold') == 'gold' and 'Modern' or 'Classic'; end,
          step = step_theme },
        { label = 'UI scale',
          value = function () return string.format('%d%%', math.floor((store.data.ui_scale or 1) * 100 + 0.5)); end,
          step = step_scale },
        { label = 'Minimum text size (small labels, numbers, timers)',
          value = function () local v = store.data.min_text or 0; return v == 0 and 'Off' or string.format('%d px', v); end,
          step = step_min },
        opt('Names over characters in the HUD font (needs the Nameplate plugin)', 'nameplates', true),
    } },
    { title = 'Chat', rows = {
        { label = 'Chat text size',
          value = function () return string.format('%d px', store.data.chat_size or 16); end,
          step = step_chat },
        opt('Chat logs fade out after 60 seconds of quiet', 'chat_autohide', true),
    } },
    { title = 'HUD', rows = {
        opt('Hide the game\'s own panels that xiv1ui replaces', 'hide_native', true),
        opt('Area map in the minimap (HD maps when available)', 'minimap_hd', true),
        opt('Popup help when hovering actions and buttons', 'popup_help', true),
        opt('Configuration button in the bottom-right menu', 'config_button', true),
    } },
    { title = 'Menus', rows = {
        opt('Command menu (Enter / A) in the FF style', 'cmd_menu', true),
        opt('Event choices (Yes / No, NPC options) in the FF style', 'choice_menu', true),
        opt('Status window in the FF style', 'status_panel', true),
    } },
    { title = 'Controls', rows = {
        { label = 'Number keys fire the action bar (1–0, Shift+↑/↓ pages)',
          get = function () return store.data.hotbar.keys; end,
          set = function (v) AshitaCore:GetChatManager():QueueCommand(-1, '/xiv1ui keys ' .. (v and 'on' or 'off')); end },
        { label = 'Action bar layers on Ctrl/Alt and LT/RT (replaces the game\'s macro palette)',
          get = function () return store.data.macro.palette == true; end,
          set = function (v) store.data.macro.palette = v; store.save(); end },
        opt('Controller drives xiv1ui (Back+X menu, Back+A action bar)', 'pad', true),
    } },
    { title = 'Layout', rows = {
        opt('UI Lock (widgets can\'t be dragged)', 'ui_locked', false),
        { label = 'Reset UI positions', action = true, value = function () return ''; end,
          step = function () require('core.layout').reset(); end },
    } },
};

-- all rows in order (the cursor moves through them as one list)
local OPTIONS = {};
for _, sec in ipairs(SECTIONS) do
    for _, r in ipairs(sec.rows) do OPTIONS[#OPTIONS + 1] = r; end
end

local ROW_H, HEAD_H = 28, 34;
local win = { id = 'config', title = 'Configuration', w = 600, sel = 1, rows = {} };
win.h = 52 + #SECTIONS * HEAD_H + #OPTIONS * ROW_H + 24;

win.draw = function (w, x, y)
    w.rows = {};
    local focused = ui.top() == w;
    local cy, base = y + 52, 0;
    for si, sec in ipairs(SECTIONS) do
        ui.header('cfg' .. si, sec.title, x + 24, cy + 22, w.w - 60);
        cy = cy + HEAD_H;
        local items = {};
        for i, o in ipairs(sec.rows) do
            if o.value then
                items[i] = { label = o.label, right = o.value(), color = 0xFFF4F0E6 };
            else
                local on = o.get();
                items[i] = { label = o.label, right = on and 'On' or 'Off', color = on and 0xFFF4F0E6 or 0xFFB0B4C0 };
            end
        end
        local rects = ui.list(w, 'cfg' .. si, items, w.sel - base, x + 40, cy, w.w - 70, ROW_H, #items, 0, focused);
        for _, r in ipairs(rects) do w.rows[#w.rows + 1] = { r[1], r[2], r[3], r[4], r[5] + base }; end
        cy = cy + #items * ROW_H;
        base = base + #items;
    end
end

local function toggle(i)
    local o = OPTIONS[i];
    if o and o.step then o.step(1);
    elseif o then o.set(not o.get()); end
end

win.key = function (w, vk)
    if vk == ui.VK.UP then w.sel = (w.sel - 2) % #OPTIONS + 1;
    elseif vk == ui.VK.DOWN then w.sel = w.sel % #OPTIONS + 1;
    elseif vk == ui.VK.RETURN then toggle(w.sel);
    elseif (vk == ui.VK.LEFT or vk == ui.VK.RIGHT) and OPTIONS[w.sel].step and not OPTIONS[w.sel].action then
        OPTIONS[w.sel].step(vk == ui.VK.LEFT and -1 or 1);
    elseif vk == ui.VK.ESCAPE then return false; end
    return true;
end

win.click = function (w, mx, my)
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then w.sel = r[5]; toggle(r[5]); return; end
    end
end

function M.open() ui.open(win); end
function M.toggle() ui.toggle(win); end

return M;
