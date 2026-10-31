--[[
* xiv1ui - Main Menu (reference §18): a tall translucent panel docked on the right screen edge with "◆ Main Menu"
* and 1.0's entries. Open/close with the Home key (1.0 Type A) or /xiv1ui menu; ↑/↓ + Enter or click to choose,
* Esc to back out. Entries open xiv1ui windows (ui/win_*.lua) or run the matching game command; entries that have no
* FFXI counterpart yet are greyed out.
--]]

local ui    = require('core.ui');
local text  = require('core.text');

local mainmenu = {};

local windows = {};          -- name -> window module (registered by xiv1ui.lua)
function mainmenu.register(name, mod) windows[name] = mod; end

local ENTRIES = {
    { label = 'Attributes',       win = 'attributes' },
    { label = 'Gear',             win = 'gear' },
    { label = 'Actions & Traits', win = 'actions', extra = true },     -- an "extra change" (Configuration » General)
    { label = 'Macros',           win = 'macros' },
    { label = 'Inventory',        win = 'inventory' },
    { label = 'Journal' },
    { label = 'Search',           cmd = '/sea all' },
    { label = 'Party',            win = 'partywin' },
    { label = 'Social Lists' },
    { label = 'Linkshells' },
    { label = 'Map' },
    { label = 'Return' },
    { label = 'Configuration',    win = 'config' },
    { label = 'Exit Game',        win = 'exit' },
};

local menu = {
    id = 'mainmenu', title = nil, style = 'hud', w = 220, h = 70 + #ENTRIES * 26,
    sel = 1, rows = {},
};

local function available(e)
    if e.disabled then return false; end
    if e.win then return windows[e.win] ~= nil; end
    return e.cmd ~= nil;
end

local function activate(e)
    if not available(e) then return; end
    if e.win then
        windows[e.win].open();
    elseif e.cmd then
        AshitaCore:GetChatManager():QueueCommand(1, e.cmd);
        ui.close(menu.id);
    end
end

menu.x = function (win)
    local sw, sh = require('core.layout').screen();
    return sw - win.w - 18, math.floor((sh - win.h) / 2) - 60;
end

-- Entries marked extra are xiv1ui's own replacements for how the game works (not only how it looks); they show
-- only with Configuration » Experimental: "Enable experimental options" and the entry's own switch both on.
local function shown()
    local out = {};
    local d = require('core.store').data;
    local extras = d.experimental == true and d.extras == true;
    for _, e in ipairs(ENTRIES) do if extras or not e.extra then out[#out + 1] = e; end end
    return out;
end

menu.draw = function (win, x, y)
    ui.header('mainmenu', 'Main Menu', x + 16, y + 30, win.w - 30);
    local entries = shown();
    win.h = 70 + #entries * 26;
    if win.sel > #entries then win.sel = #entries; end
    local items = {};
    for i, e in ipairs(entries) do items[i] = { label = e.label, disabled = not available(e) }; end
    win.rows = ui.list(win, 'mm', items, win.sel, x + 26, y + 44, win.w - 40, 26, #items, 0, ui.top() == win);
end

menu.key = function (win, vk)
    if vk == ui.VK.ESCAPE then return false; end      -- not handled: Esc / B closes the menu
    local entries = shown();
    if vk == ui.VK.UP then win.sel = (win.sel - 2) % #entries + 1;
    elseif vk == ui.VK.DOWN then win.sel = win.sel % #entries + 1;
    elseif vk == ui.VK.RETURN then activate(entries[win.sel]); end
    return true;
end

menu.click = function (win, mx, my)
    for _, r in ipairs(win.rows) do
        if ui.hit(r, mx, my) then win.sel = r[5]; activate(shown()[r[5]]); return true; end
    end
end

menu.hover = function (win, mx, my)
    for _, r in ipairs(win.rows) do
        if ui.hit(r, mx, my) then win.sel = r[5]; end
    end
end

function mainmenu.toggle() ui.toggle(menu); end

function mainmenu.key(e)
    -- Home toggles the menu (unless typing in chat)
    if e.wparam == ui.VK.HOME and bit.band(e.lparam, 0x80000000) == 0 then
        local ok, open = pcall(function () return AshitaCore:GetChatManager():IsInputOpen(); end);
        if ok and open and open ~= 0 then return false; end
        mainmenu.toggle();
        return true;
    end
    return false;
end

function mainmenu.command(args)
    if (args[2] or ''):lower() == 'menu' then mainmenu.toggle(); end
end

return mainmenu;
