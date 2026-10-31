--[[
* xiv1ui - micro menu (bottom right), after FFXIV 1.0 (reference §19): two rows of small round buttons.
* Upper row: interactions for the current target (Check, Trade, Invite to party), greyed when they don't apply.
* Lower row: Main Menu, Active/Passive (engage/disengage), Use Item (inventory), Emotes, UI Lock, Popup Help.
* Hover shows the button's name.
--]]

local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local world  = require('core.world');
local store  = require('core.store');

local micro = {};

local function cmd(c) AshitaCore:GetChatManager():QueueCommand(1, c); end
local function has_pc_target()
    local idx = world.target_index();
    return idx ~= 0 and world.kind(idx) == 'pc' and idx ~= AshitaCore:GetMemoryManager():GetParty():GetMemberTargetIndex(0);
end
local function engaged()
    local idx = AshitaCore:GetMemoryManager():GetParty():GetMemberTargetIndex(0);
    return AshitaCore:GetMemoryManager():GetEntity():GetStatus(idx) == 1;
end

local UPPER = {
    { icon = 'check',  name = 'Check',           ok = function () return world.target_index() ~= 0; end, run = function () cmd('/check <t>'); end },
    { icon = 'trade',  name = 'Trade',           ok = has_pc_target, run = function () cmd('/trade <t>'); end },
    { icon = 'invite', name = 'Invite to Party', ok = has_pc_target, run = function () cmd('/pcmd add <t>'); end },
};
local LOWER = {
    { icon = 'menu',   name = 'Main Menu',       run = function () require('ui.mainmenu').toggle(); end },
    { icon = 'battle', name = 'Active / Passive Mode', on = engaged,
      run = function () if engaged() then cmd('/attack off'); else cmd('/attack <t>'); end end },
    { icon = 'item',   name = 'Use Item',        run = function () require('ui.win_inventory').open(); end },
    { icon = 'emote',  name = 'Emotes',          run = function () require('ui.win_emotes').open(); end },
    { icon = 'lock',   name = 'UI Lock',         on = function () return store.data.ui_locked == true; end,
      run = function () store.data.ui_locked = not store.data.ui_locked; store.save(); end },
    { icon = 'help',   name = 'Popup Help',      on = function () return store.data.popup_help ~= false; end,
      run = function () store.data.popup_help = (store.data.popup_help == false); store.save(); end },
};

local STEP = 34;
local rects = {};
local hover = nil;
local tip;

function micro.init()
    tip = text.new('small', { font_height = 15, font_alignment = text.align.Right });
end

function micro.render()
    local W = #LOWER * STEP;
    local x0, y0 = layout.anchor('bottomright', W, 74, -16, -14, 'micromenu');
    layout.bounds('micromenu', x0, y0, W, 74);
    rects = {};
    local function row(list, y, upper)
        local x = x0 + W - #list * STEP;
        for i, b in ipairs(list) do
            local ok = (b.ok == nil) or b.ok();
            local col = ok and 0xFFFFFFFF or 0x70FFFFFF;
            if b.on and b.on() then draw.image('slot_glow', x - 19, y - 19, { scale = 0.65, color = 0xC0FFE08C }); end
            draw.image('micro_' .. b.icon, x, y, { color = col });
            if hover == b then draw.image('slot_glow', x - 19, y - 19, { scale = 0.65, color = 0xA0FFFFFF }); end
            rects[#rects + 1] = { x, y, 34, 34, b, ok };
            x = x + STEP;
        end
    end
    row(UPPER, y0, true);
    row(LOWER, y0 + 38, false);
    if hover then text.draw(tip, hover.name, x0 + W, y0 - 8, 'baseline'); end
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
