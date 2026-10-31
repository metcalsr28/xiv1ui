--[[
* xiv1ui - events (cutscenes, NPC conversations) in a cinematic frame: black letterbox bars slide in from the top
* and bottom while the HUD steps aside (xiv1ui.lua skips the HUD modules during an event; the dialogue box, the
* choice menu and the item card stay). They slide back out when the event ends.
--]]

local draw   = require('core.draw');
local layout = require('core.layout');
local event  = require('core.event');

local cinema = {};

local BAR = 0.085;           -- each bar's height, as a fraction of the screen

function cinema.render()
    local a = event.amount();
    if a <= 0 then return; end
    local e = 1 - (1 - a) ^ 3;
    local sw, sh = layout.screen();
    local h = math.floor(sh * BAR * e + 0.5);
    draw.rect(0, 0, sw, h, 0xFF000000);
    draw.rect(0, sh - h, sw, h, 0xFF000000);
end

return cinema;
