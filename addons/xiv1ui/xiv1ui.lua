--[[
* xiv1ui - an interface for FINAL FANTASY XI modelled on FINAL FANTASY XIV 1.0.
*
* Display-and-command only: every action goes through the game's own text commands (/ma, /ja, /item, ...).
* Modules live in ui/; each exposes optional init(), render(), command(args) and release().
--]]

addon.name    = 'xiv1ui';
addon.author  = 'xiv1ui project';
addon.version = '0.1';
addon.desc    = 'FINAL FANTASY XIV 1.0 style interface.';
addon.link    = '';

require('common');

local xi_now = require('core.now');
local draw = require('core.draw');
local text = require('core.text');
local layout = require('core.layout');
local native = require('core.native');
local store  = require('core.store');
local world  = require('core.world');
local ui     = require('core.ui');

local ROOT = addon.path:gsub('[\\/]?$', '\\');

local MODULES = {
    'gamein',           -- first: keeps navigation input from the game while an xiv1ui window is open
    'cinema',           -- letterbox bars during events (under everything)
    'nameplates',
    'worldfx',
    'gauges',
    'hotbar',
    'target',
    'party',
    'status',
    'expbar',
    'castbar',
    'dialogue',
    'chatlog',
    'deathscreen',      -- the knocked-out screen (under the menus)
    'itemcard',         -- after the dialogue box (sits above it)
    'confirm',          -- the game's yes / no questions
    'cmdmenu',          -- after the chat logs: menus and panels draw over them
    'statuspanel',
    'equippanel',
    'itempanel',
    'listpanel',
    'roe',              -- Records of Eminence / currency figures from the server's packets
    'mainmenu',
    'micromenu',
    'minimap',
    'layers',
};
local modules = {};
-- HUD parts that can be resized on their own (Configuration » HUD): module -> part key in store.data.part_scale
local PARTS = { hotbar = 'bars', gauges = 'bars', expbar = 'bars', castbar = 'bars', layers = 'bars',
                target = 'target', status = 'target', party = 'party', minimap = 'minimap', micromenu = 'buttons' };
local function part_dx(name)
    local key = PARTS[name or ''];
    local t = key and store.data.part_offset;
    return t and tonumber(rawget(t, key)) or 0;
end
local function part_k(name)
    local key = PARTS[name or ''];
    local t = key and store.data.part_scale;
    local k = t and tonumber(rawget(t, key)) or 1;
    return (k > 0.4 and k < 3) and k or 1;
end
-- the modules still drawn during an event (everything else is the HUD, which steps aside)
local EVENT_PARTS = { gamein = true, cinema = true, nameplates = true, dialogue = true, itemcard = true, cmdmenu = true,
                      deathscreen = true, confirm = true, mainmenu = true, layers = true, botexport = true, roe = true };
for _, n in ipairs(MODULES) do
    local m = require('ui.' .. n);
    m.name = n;                    -- for /xiv1ui hide <name>
    modules[#modules + 1] = m;
end
-- development tools, absent from releases (dev/)
do
    local ok, m = pcall(require, 'dev.botexport');
    if ok and type(m) == 'table' then m.name = 'botexport'; modules[#modules + 1] = m; end
    pcall(require, 'dev.ccchat');
end

local hotbar   = require('ui.hotbar');
local mainmenu = require('ui.mainmenu');
mainmenu.register('actions', require('ui.win_actions'));
mainmenu.register('config',  require('ui.win_config'));
mainmenu.register('inventory', require('ui.win_inventory'));
mainmenu.register('gear', require('ui.win_gear'));
mainmenu.register('attributes', require('ui.win_attributes'));
mainmenu.register('partywin', require('ui.win_party'));
mainmenu.register('exit',    require('ui.win_exit'));
mainmenu.register('macros',  require('ui.win_macros'));

local ready = false;

ashita.events.register('load', 'xiv1ui_load', function ()
    ready = draw.init(ROOT);
    layout.init(ROOT);
    text.init(ROOT);
    for _, m in ipairs(modules) do
        if m.init then m.init(); end
        native.want(m.replaces);
    end
end);

ashita.events.register('unload', 'xiv1ui_unload', function ()
    native.restore();
    pcall(require('ui.lobby').release);
    for _, m in ipairs(modules) do
        if m.release then
            local ok, err = pcall(m.release);      -- a failing cleanup must never stop xiv1ui unloading / reloading
            if not ok then print('[xiv1ui] ' .. tostring(err)); end
        end
    end
    text.release();
    draw.release();
end);

-- Start of each scene: let the menu restyle hide a just-opened game menu before the game draws it.
local frame_no = 0;
ashita.events.register('d3d_beginscene', 'xiv1ui_beginscene', function ()
    if not ready then return; end
    local ok, err = pcall(require('ui.lobby').early);
    if not ok then print('[xiv1ui] ' .. tostring(err)); end
    ok, err = pcall(require('ui.cmdmenu').early);
    if not ok then print('[xiv1ui] ' .. tostring(err)); end
    ok, err = pcall(require('ui.chatlog').early);
    if not ok then print('[xiv1ui] ' .. tostring(err)); end
    ok, err = pcall(require('core.gamewin').early);
    if not ok then print('[xiv1ui] ' .. tostring(err)); end
end);

ashita.events.register('d3d_present', 'xiv1ui_present', function ()
    frame_no = frame_no + 1;
    if not ready then return; end
    -- the lobby (title, character select, creation) has its own screens and no HUD
    local lobby = require('ui.lobby');
    local loading = lobby.loading();
    if lobby.active() or loading then
        draw.set_scale(store.data.ui_scale);
        if not draw.begin_frame() then return; end
        local ok, err = pcall(loading and lobby.render_loading or lobby.render);
        if not ok then print('[xiv1ui] ' .. tostring(err)); end
        draw.end_frame();
        return;
    end
    local player = AshitaCore:GetMemoryManager():GetPlayer();
    if player == nil or player:GetIsZoning() ~= 0 or player:GetMainJob() == 0 then return; end
    -- logged out (character select, creation): the party / player data stays in memory, so check the login status
    -- and that the player's entity exists
    if player:GetLoginStatus() == 0 then return; end
    local me = AshitaCore:GetMemoryManager():GetParty():GetMemberTargetIndex(0);
    if me == nil or me == 0 or (AshitaCore:GetMemoryManager():GetEntity():GetServerId(me) or 0) == 0 then return; end
    local t0 = xi_now();
    native.tick(store.data.hide_native);
    require('core.project').begin();
    draw.set_scale(store.data.ui_scale);
    if not draw.begin_frame() then return; end
    local dev_hidden = store.data.dev_hidden or {};
    -- during an event (cutscene, NPC conversation) only the parts that belong to it are drawn
    local in_event = require('core.event').active();
    for _, m in ipairs(modules) do
        if m.render and not dev_hidden[m.name or ''] and (not in_event or EVENT_PARTS[m.name]) then
            local k = part_k(m.name);
            if k ~= 1 then draw.push_part(k); end
            layout.part_dx = part_dx(m.name);
            local ok, err = xpcall(m.render, debug.traceback);
            layout.part_dx = 0;
            if k ~= 1 then draw.pop_part(); end
            if not ok then
                print('[xiv1ui] ' .. m.name .. ': ' .. tostring(err):match('^[^\n]*'));
                _G.xiv1ui_last_error = err;          -- (with the traceback, for /xiv1ui eval)
                m.render = nil;
            end
        end
    end
    local ok, err = pcall(ui.render);
    if not ok then print('[xiv1ui] ' .. tostring(err)); end
    draw.end_frame();
    -- performance counters (read with /xiv1ui eval return xiv1ui_perf)
    local perf = _G.xiv1ui_perf or { frames = 0, cost = 0, since = xi_now() };
    perf.frames = perf.frames + 1;
    perf.cost = perf.cost + (xi_now() - t0);
    _G.xiv1ui_perf = perf;
end);

-- (controller buttons are read from the XInput state in ui/gamein.lua, not from xinput_button events)

ashita.events.register('key', 'xiv1ui_key', function (e)
    if not ready then return; end
    -- a text field being edited takes every key
    if require('core.textinput').key(e) then e.blocked = true; return; end
    pcall(require('ui.dialogue').key, e);
    local down = bit.band(e.lparam, 0x80000000) == 0;
    -- placing an action from the Actions & Traits window: 1..0 choose the slot, Esc cancels
    if hotbar.assigning() then
        local vk = e.wparam;
        if vk >= 0x30 and vk <= 0x39 then
            if down then hotbar.use(vk == 0x30 and 10 or vk - 0x30); end
            e.blocked = true;
            return;
        elseif vk == ui.VK.ESCAPE then
            if down then hotbar.cancel_assign(); end
            e.blocked = true;
            return;
        end
    end
    if mainmenu.key(e) or ui.key(e) then e.blocked = true; end
end);

-- HUD layout editing (1.0: every widget can be dragged; UI Lock freezes them). A press on a widget only becomes a
-- drag after 6 px of movement, so ordinary clicks on its buttons still work.
local drag = nil;      -- { id, x, y, moved }

local function widget_at(x, y)
    for id, r in pairs(layout.widgets) do
        if x >= r[1] and x < r[1] + r[3] and y >= r[2] and y < r[2] + r[4] then return id; end
    end
end

local function handle_drag(e)
    if store.data.ui_locked then drag = nil; return false; end
    if e.message == 0x201 then
        local id = widget_at(e.x, e.y);
        if id then drag = { id = id, x = e.x, y = e.y, moved = false }; end
        return false;
    elseif e.message == 0x200 and drag then
        local dx, dy = e.x - drag.x, e.y - drag.y;
        if drag.moved or dx * dx + dy * dy > 36 then
            drag.moved = true;
            layout.move(drag.id, dx, dy);
            drag.x, drag.y = e.x, e.y;
            return true;
        end
    elseif e.message == 0x202 and drag then
        local moved = drag.moved;
        drag = nil;
        if moved then store.save(); return true; end
    end
    return false;
end

ashita.events.register('mouse', 'xiv1ui_mouse', function (raw)
    if not ready then return; end
    -- modules work in HUD units; reads of other fields and writes (e.blocked) go through to the real event
    local e = setmetatable({ x = raw.x / draw.scale, y = raw.y / draw.scale },
        { __index = raw, __newindex = raw });
    local lobby = require('ui.lobby');
    if lobby.active() then lobby.mouse(e); return; end
    if ui.mouse(e) then e.blocked = true; return; end
    local okr, resized = pcall(require('ui.chatlog').resize_mouse, e);
    if okr and resized then return; end
    if handle_drag(e) then e.blocked = true; return; end
    for _, m in ipairs(modules) do
        if m.mouse then
            local k = part_k(m.name);
            if k ~= 1 then
                -- a scaled part works in its own units: hand it the pointer in them
                draw.push_part(k);
                local pe = setmetatable({ x = e.x / k, y = e.y / k }, { __index = raw, __newindex = raw });
                pcall(m.mouse, pe);
                draw.pop_part();
            else
                m.mouse(e);
            end
        end
        if e.blocked then return; end
    end
end);

-- DirectInput buffered keyboard events (the game reads the arrows this way too, e.g. for the camera).
ashita.events.register('key_data', 'xiv1ui_key_data', function (e)
    if not ready then return; end
    pcall(ui.key_data, e);
end);

-- DirectInput keyboard state, before the game reads it (the macro palette takes Ctrl/Alt from the game).
ashita.events.register('key_state', 'xiv1ui_key_state', function (e)
    if not ready then return; end
    -- while a text field is edited the game sees no keys at all (typing mustn't walk the character around)
    if require('core.textinput').active() then
        local p = require('ffi').cast('uint8_t*', e.data_raw);
        for k = 0, 255 do p[k] = 0; end
        return;
    end
    -- an open xiv1ui window keeps its navigation keys from the game (camera, menus)
    pcall(ui.key_state, e);
    for _, m in ipairs(modules) do
        if m.key_state then
            local ok, err = pcall(m.key_state, e);
            if not ok then print('[xiv1ui] ' .. tostring(err)); m.key_state = nil; end
        end
    end
end);

-- XInput controller state, before the game reads it (the macro palette takes LT/RT from the game).
ashita.events.register('xinput_state', 'xiv1ui_xinput_state', function (e)
    if not ready then return; end
    for _, m in ipairs(modules) do
        if m.xinput_state then
            local ok, err = pcall(m.xinput_state, e);
            if not ok then print('[xiv1ui] ' .. tostring(err)); m.xinput_state = nil; end
        end
    end
end);

ashita.events.register('text_in', 'xiv1ui_text_in', function (e)
    -- lines printed by addons: only xiv1ui's own and those the chat log was told to accept (chatlog.extend)
    if e.injected and not require('ui.chatlog').accepts_injected(e.message) then return; end
    for _, m in ipairs(modules) do
        if m.text_in then
            local ok, err = pcall(m.text_in, e);
            if not ok then print('[xiv1ui] ' .. tostring(err)); m.text_in = nil; end
        end
    end
end);

ashita.events.register('packet_in', 'xiv1ui_packet_in', function (e)
    world.on_packet(e);
    local ok, err = pcall(require('ui.worldfx').packet, e);
    if not ok then print('[xiv1ui] ' .. tostring(err)); end
    ok, err = pcall(require('ui.dialogue').packet, e);
    if not ok then print('[xiv1ui] ' .. tostring(err)); end
    -- any other module that reads the server's packets (roe, itempanel ...)
    for _, m in ipairs(modules) do
        if m.packet and m.name ~= 'dialogue' then
            ok, err = pcall(m.packet, e);
            if not ok then print('[xiv1ui] ' .. m.name .. ': ' .. tostring(err)); m.packet = nil; end
        end
    end
end);

ashita.events.register('packet_out', 'xiv1ui_packet_out', function (e)
    local ok, err = pcall(require('ui.dialogue').packet_out, e);
    if not ok then print('[xiv1ui] ' .. tostring(err)); end
end);

ashita.events.register('command', 'xiv1ui_command', function (e)
    local args = e.command:args();
    if #args == 0 or args[1]:lower() ~= '/xiv1ui' then return; end
    e.blocked = true;
    -- development only, absent from releases (dev/eval.lua): /xiv1ui eval <lua>
    if args[2] == 'eval' then
        local ok, run = pcall(require, 'dev.eval');
        if ok and type(run) == 'function' then run(e); end
        return;
    end
    if args[2] == 'layout' and args[3] == 'reset' then layout.reset(); return; end
    -- /xiv1ui config: the Configuration window; /xiv1ui configbutton on|off: its button in the bottom-right menu
    if (args[2] or ''):lower() == 'config' then require('ui.win_config').toggle(); return; end
    if (args[2] or ''):lower() == 'configbutton' then
        local a3 = (args[3] or ''):lower();
        if a3 == 'on' then store.data.config_button = true;
        elseif a3 == 'off' then store.data.config_button = false;
        else store.data.config_button = (store.data.config_button == false); end
        store.save();
        print('[xiv1ui] Configuration button ' .. (store.data.config_button ~= false and 'shown' or 'hidden') .. '.');
        return;
    end
    if (args[2] or ''):lower() == 'macro' then require('ui.win_macros').command(args); return; end
    -- /xiv1ui hide <part> / show <part>: stop drawing one HUD part (e.g. to see what's behind it); not saved
    if (args[2] == 'hide' or args[2] == 'show') and args[3] then
        store.data.dev_hidden = store.data.dev_hidden or {};
        store.data.dev_hidden[args[3]:lower()] = (args[2] == 'hide') or nil;
        return;
    end
    -- /xiv1ui scale 1.25 (or 125)
    if args[2] == 'scale' and tonumber(args[3]) then
        local v = tonumber(args[3]);
        if v > 5 then v = v / 100; end
        draw.set_scale(v);
        store.data.ui_scale = draw.user_scale;
        store.save();
        return;
    end
    for _, m in ipairs(modules) do
        if m.command then m.command(args); end
    end
end);
