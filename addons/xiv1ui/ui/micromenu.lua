--[[
* xiv1ui - the button row at the bottom right: quick ways into the menus, after FFXIV 1.0's small round buttons
* (reference §19). Upper row: Trade and Invite (for the targeted player; greyed otherwise). Lower row: Commands
* (FFXI's own Commands menu), Inventory (its Items menu), Map, Emotes, UI Lock, Configuration. The buttons open the
* game's own menus where it has them (xiv1ui only restyles those). Hover shows the button's name; the Configuration
* button can be hidden (/xiv1ui configbutton off).
--]]

local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local store  = require('core.store');
local world  = require('core.world');

local micro = {};

local function cmd(c) AshitaCore:GetChatManager():QueueCommand(1, c); end
local function has_pc_target()
    local idx = world.target_index();
    return idx ~= 0 and world.kind(idx) == 'pc' and idx ~= AshitaCore:GetMemoryManager():GetParty():GetMemberTargetIndex(0);
end

local UPPER = {
    { icon = 'trade',  name = 'Trade',          ok = has_pc_target, run = function () cmd('/trade <t>'); end },
    { icon = 'invite', name = 'Invite to Party', ok = has_pc_target, run = function () cmd('/pcmd add <t>'); end },
};
local BUTTONS = {
    -- FFXI opens its Commands menu with numpad minus (DIK 0x4A)
    { icon = 'menu',   name = 'Commands',       run = function () require('ui.gamein').press(0x4A); end },
    { icon = 'item',   name = 'Inventory',      run = function () require('ui.gamein').open_command('Items'); end },
    { icon = 'map',    name = 'Map',            run = function () cmd('/map'); end },
    { icon = 'emote',  name = 'Emotes',         run = function () require('ui.win_emotes').open(); end },
    { icon = 'lock',   name = 'UI Lock',        on = function () return store.data.ui_locked == true; end,
      run = function () store.data.ui_locked = not store.data.ui_locked; store.save(); end },
    { icon = 'config', name = 'Configuration',  show = function () return store.data.config_button ~= false; end,
      run = function () require('ui.win_config').toggle(); end },
};

local STEP, SIZE = 38, 34;
local rects = {};
local hover = nil;
local tip;

function micro.init()
    tip = text.new('small', { font_height = 15, font_alignment = text.align.Right });
end

function micro.render()
    local list = {};
    for _, b in ipairs(BUTTONS) do if b.show == nil or b.show() then list[#list + 1] = b; end end
    local W, H = #list * STEP - (STEP - SIZE), SIZE * 2 + 6;
    local x0, ytop = layout.anchor('bottomright', W, H, -16, -16, 'micromenu');
    layout.bounds('micromenu', x0, ytop, W, H);
    rects = {};
    -- the upper row is right-aligned over the lower one
    local function place(row, y)
        local out = {};
        local rw = #row * STEP - (STEP - SIZE);
        for i, b in ipairs(row) do out[i] = { b, x0 + W - rw + (i - 1) * STEP, y }; end
        return out;
    end
    local cells = place(UPPER, ytop);
    for _, c in ipairs(place(list, ytop + SIZE + 6)) do cells[#cells + 1] = c; end
    for _, cell in ipairs(cells) do
        local b, x, y0 = cell[1], cell[2], cell[3];
        local ok = b.ok == nil or b.ok();
        if b.on and b.on() then draw.image('slot_glow', x - 19, y0 - 19, { scale = 0.65, color = 0xC0FFE08C }); end
        draw.image('micro_' .. b.icon, x, y0, { color = ok and 0xFFFFFFFF or 0x70FFFFFF });
        if hover == b then draw.image('slot_glow', x - 19, y0 - 19, { scale = 0.65, color = 0xA0FFFFFF }); end
        rects[#rects + 1] = { x, y0, SIZE, SIZE, b, ok };
    end
    if hover then text.draw(tip, hover.name, x0 + W - #UPPER * STEP - 6, ytop + 24, 'baseline'); end
end

function micro.mouse(e)
    local found, ok;
    for _, r in ipairs(rects) do
        if e.x >= r[1] and e.x < r[1] + r[3] and e.y >= r[2] and e.y < r[2] + r[4] then found, ok = r[5], r[6]; end
    end
    if e.message == 0x200 then hover = found; return; end
    if not found then return; end
    if e.message == 0x201 then e.blocked = true;
    elseif e.message == 0x202 then
        e.blocked = true;
        if ok then found.run(); end
    end
end

return micro;
