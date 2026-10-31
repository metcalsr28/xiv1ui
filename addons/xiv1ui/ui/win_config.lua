--[[
* xiv1ui - Configuration window (reference §38): xiv1ui's own options as a list of On/Off rows, plus UI scale.
* ↑/↓ choose, Enter or click toggles (UI scale: ←/→ or Enter/click steps through the sizes).
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

local OPTIONS = {
    { label = 'Window style',
      value = function () return (store.data.theme or 'gold') == 'gold' and 'Modern' or 'Classic'; end,
      step = step_theme },
    { label = 'UI scale (Left/Right or click to change)',
      value = function () return string.format('%d%%', math.floor((store.data.ui_scale or 1) * 100 + 0.5)); end,
      step = step_scale },
    { label = 'Minimum text size (small labels, numbers, timers)',
      value = function () local v = store.data.min_text or 0; return v == 0 and 'Off' or string.format('%d px', v); end,
      step = step_min },
    { label = 'Chat text size',
      value = function () return string.format('%d px', store.data.chat_size or 16); end,
      step = step_chat },
    { label = 'Number keys fire the action bar (1–0, Shift+↑/↓ pages)',
      get = function () return store.data.hotbar.keys; end,
      set = function (v) AshitaCore:GetChatManager():QueueCommand(-1, '/xiv1ui keys ' .. (v and 'on' or 'off')); end },
    { label = 'Hide the game\'s own panels that xiv1ui replaces',
      get = function () return store.data.hide_native; end,
      set = function (v)
          store.data.hide_native = v; store.save();
          AshitaCore:GetChatManager():QueueCommand(-1, '/hxiui ' .. (v and 'on' or 'off'));
      end },
    { label = 'Action bar layers on Ctrl/Alt and LT/RT (replaces the game\'s macro palette)',
      get = function () return store.data.macro.palette == true; end,
      set = function (v) store.data.macro.palette = v; store.save(); end },
    { label = 'Area map in the minimap (HD Remapster maps when installed)',
      get = function () return store.data.minimap_hd ~= false; end,
      set = function (v) store.data.minimap_hd = v; store.save(); end },
    { label = 'Command menu (Enter / A) in the FF style',
      get = function () return store.data.cmd_menu ~= false; end,
      set = function (v) store.data.cmd_menu = v; store.save(); end },
    { label = 'Names over characters in the HUD font (needs the Nameplate plugin)',
      get = function () return store.data.nameplates ~= false; end,
      set = function (v) store.data.nameplates = v; store.save(); end },
    { label = 'Controller drives xiv1ui (Back+X menu, Back+A action bar)',
      get = function () return store.data.pad ~= false; end,
      set = function (v) store.data.pad = v; store.save(); end },
    { label = 'UI Lock (widgets can\'t be dragged)',
      get = function () return store.data.ui_locked == true; end,
      set = function (v) store.data.ui_locked = v; store.save(); end },
    { label = 'Reset UI positions',
      get = function () return false; end,
      set = function () require('core.layout').reset(); end },
    { label = 'Chat logs fade out after 60 seconds',
      get = function () return store.data.chat_autohide ~= false; end,
      set = function (v) store.data.chat_autohide = v; store.save(); end },
};

local win = { id = 'config', title = 'Configuration', w = 560, h = 70 + #OPTIONS * 30 + 40, sel = 1, rows = {} };

win.draw = function (w, x, y)
    ui.header('cfg', 'Interface', x + 24, y + 62, w.w - 60);
    local items = {};
    for i, o in ipairs(OPTIONS) do
        if o.value then
            items[i] = { label = o.label, right = o.value(), color = 0xFFF4F0E6 };
        else
            items[i] = { label = o.label, right = o.get() and 'On' or 'Off',
                color = o.get() and 0xFFF4F0E6 or 0xFFB0B4C0 };
        end
    end
    w.rows = ui.list(w, 'cfg', items, w.sel, x + 40, y + 76, w.w - 70, 30, #items, 0, ui.top() == w);
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
    elseif (vk == ui.VK.LEFT or vk == ui.VK.RIGHT) and OPTIONS[w.sel].step then
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

return M;
