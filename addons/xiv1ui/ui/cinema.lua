--[[
* xiv1ui - events (cutscenes, NPC conversations) in a cinematic frame: black letterbox bars slide in from the top
* and bottom while the HUD steps aside (xiv1ui.lua skips the HUD modules during an event; the dialogue box, the
* choice menu and the item card stay). They slide back out when the event ends. A bar never covers one of FFXI's
* own windows (one xiv1ui leaves to the game, e.g. an exchange list): it gives way down to that window's edge.
--]]

local draw   = require('core.draw');
local layout = require('core.layout');
local event  = require('core.event');

local cinema = {};
local top_h, bot_h = 0, 0;   -- each bar's height last frame (it eases toward where it may go)

local BAR = 0.085;           -- each bar's height, as a fraction of the screen

function cinema.render()
    local a = event.amount();
    if a <= 0 then return; end
    local e = 1 - (1 - a) ^ 3;
    local sw, sh = layout.screen();
    local h = math.floor(sh * BAR * e + 0.5);
    -- room each bar has before the game's own windows (their edge, less a small gap)
    local top_room, bot_room = h, h;
    for _, r in ipairs(require('core.gamewin').occupied()) do
        if r[2] < h then top_room = math.min(top_room, math.max(0, r[2] - 4)); end
        if r[2] + r[4] > sh - h then bot_room = math.min(bot_room, math.max(0, sh - (r[2] + r[4]) - 4)); end
    end
    top_h = top_h + (top_room - top_h) * 0.3;
    bot_h = bot_h + (bot_room - bot_h) * 0.3;
    if math.abs(top_h - top_room) < 0.5 then top_h = top_room; end
    if math.abs(bot_h - bot_room) < 0.5 then bot_h = bot_room; end
    if top_h >= 1 then draw.rect(0, 0, sw, math.floor(top_h + 0.5), 0xFF000000); end
    if bot_h >= 1 then draw.rect(0, sh - math.floor(bot_h + 0.5), sw, math.floor(bot_h + 0.5), 0xFF000000); end
end

return cinema;
