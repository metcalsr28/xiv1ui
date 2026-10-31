--[[
* xiv1ui - is the player in an event (a cutscene, or talking to an NPC)? The server sets the player's status to 4
* for the whole event (the entity's client-side status stays 0).
--]]

local xi_now = require('core.now');

local event = { since = nil, ended = nil };

--- True while an event runs; event.since / event.ended give when it started / last ended (for fades).
function event.active()
    local party = AshitaCore:GetMemoryManager():GetParty();
    local i = party:GetMemberTargetIndex(0);
    local on = i ~= nil and i ~= 0 and AshitaCore:GetMemoryManager():GetEntity():GetStatusServer(i) == 4;
    if on and event.since == nil then event.since = xi_now(); end
    if not on and event.since ~= nil then event.since, event.ended = nil, xi_now(); end
    return on;
end

--- 0..1: how far the event look has eased in (1 = fully in an event), with a fade either way.
function event.amount()
    local now = xi_now();
    if event.active() then return math.min(1, (now - event.since) / 0.5); end
    if event.ended then return math.max(0, 1 - (now - event.ended) / 0.4); end
    return 0;
end

return event;
