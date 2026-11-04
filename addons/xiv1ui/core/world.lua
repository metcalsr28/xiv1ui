--[[
* xiv1ui - world helpers: entity kinds, 1.0 name/claim colours, party membership and an enmity estimate.
--]]

local xi_now = require('core.now');

local world = {};

local function mm() return AshitaCore:GetMemoryManager(); end

-- 1.0 name colours (reference §9).
world.COLOR = {
    pc      = 0xFFF4F0E6,   -- other PCs: white/cream
    party   = 0xFF8CC8FF,   -- party member: blue
    npc     = 0xFF9BE08C,   -- NPC: green
    mob     = 0xFFF0D060,   -- enemy, not claimed: yellow
    claimed = 0xFFFF7C91,   -- claimed by you / your party: red-pink
    other   = 0xFFB496E6,   -- claimed by another party: purple
    hostile = 0xFFF0A040,   -- attacking but unclaimed: orange
    self    = 0xFFF4E070,   -- your own name in the party list: yellow (1.18)
};

--- Index of the current main target (0 if none). While a sub-target cursor is up, the main target is slot 1.
function world.target_index()
    local t = mm():GetTarget();
    local slot = (t:GetIsSubTargetActive() == 1) and 1 or 0;
    return t:GetTargetIndex(slot) or 0;
end

--- The entity a sub-target cursor is on (choosing who a spell or command goes to: slot 0 while the main target
-- waits in slot 1), or 0 when no sub-target cursor is up. FFXI's own arrows go with its target box, which xiv1ui
-- hides, so this is what xiv1ui marks while the player chooses.
function world.subtarget_index()
    local t = mm():GetTarget();
    if t:GetIsSubTargetActive() ~= 1 then return 0; end
    return t:GetTargetIndex(0) or 0;
end

--- A target that is a model with no entity behind it (the Mog House door, "Door: Back to Town"): its name and
-- world position x, height, y (the actor keeps them at +0x34), or nil. Only while no entity is targeted.
function world.target_actor()
    local t = mm():GetTarget();
    if (t:GetTargetIndex(0) or 0) ~= 0 or t:GetIsActive() ~= 1 then return nil; end
    local a = t:GetActorPointer();
    local name = t:GetWindowName();
    if a == nil or a == 0 or name == nil or name == '' or not require('core.mem').ok(a + 0x34, 12) then return nil; end
    local f = require('ffi').cast('float*', a + 0x34);
    return name, f[0], f[1], f[2];
end

function world.locked()
    return mm():GetTarget():GetLockedOnFlags() ~= 0;
end

--- 'pc' | 'npc' | 'mob' for an entity index.
function world.kind(idx)
    local flags = mm():GetEntity():GetSpawnFlags(idx) or 0;
    if bit.band(flags, 0x0001) ~= 0 then return 'pc'; end
    if bit.band(flags, 0x0010) ~= 0 then return 'mob'; end
    return 'npc';
end

--- Set of party member server ids -> party slot (0 = you).
function world.party_ids()
    local p = mm():GetParty();
    local ids = {};
    for i = 0, 5 do
        if p:GetMemberIsActive(i) == 1 then ids[p:GetMemberServerId(i)] = i; end
    end
    return ids;
end

--- Claim state of a mob: 'none' | 'party' | 'other', plus whether it is engaged (fighting).
function world.claim(idx)
    local e = mm():GetEntity();
    local claimer = e:GetClaimStatus(idx) or 0;
    local engaged = (e:GetStatus(idx) == 1);
    if claimer == 0 then return 'none', engaged; end
    if world.party_ids()[claimer] ~= nil then return 'party', engaged; end
    return 'other', engaged;
end

--- 1.0 name colour for an entity.
function world.name_color(idx)
    local kind = world.kind(idx);
    if kind == 'pc' then
        local sid = mm():GetEntity():GetServerId(idx);
        return world.party_ids()[sid] ~= nil and world.COLOR.party or world.COLOR.pc;
    elseif kind == 'npc' then
        return world.COLOR.npc;
    end
    local claim, engaged = world.claim(idx);
    if claim == 'party' then return world.COLOR.claimed; end
    if claim == 'other' then return world.COLOR.other; end
    return engaged and world.COLOR.hostile or world.COLOR.mob;
end

-- Who each mob last acted on, from incoming action packets (0x028): actor server id -> { target = server id, t }.
-- Read-only; FFXI doesn't fill in a mob's target in its entity data, so this is how the enmity capsule knows.
local mob_targets = {};

-- What we are casting right now (from our own action packets): { kind = 8 (spell) | 9 (item), id, t } or nil.
world.casting = nil;

-- Skillchain window, the FFXI counterpart of 1.0's combo: after a party weapon skill lands on a mob, another weapon
-- skill on it within ~8 s can chain. combo = { target = server id, ends = xi_now() deadline, ws = ability id }.
world.combo = nil;

--- packet_in handler (registered by xiv1ui.lua).
function world.on_packet(e)
    if e.id ~= 0x028 then return; end
    local data = e.data_raw;
    local size = e.size * 8;
    if size < 182 then return; end
    local actor = ashita.bits.unpack_be(data, 0, 40, 32);
    local count = ashita.bits.unpack_be(data, 0, 72, 6);
    local kind  = ashita.bits.unpack_be(data, 0, 82, 4);
    -- our own casting: category 8 = magic start (param 24931) or interrupt (28787); 4 = magic finished;
    -- 9 = item start; 5 = item finished. The first action's param holds the spell/item id.
    if actor == mm():GetParty():GetMemberServerId(0) then
        local param = ashita.bits.unpack_be(data, 0, 86, 16);
        if kind == 8 or kind == 9 then
            if param == 28787 then
                world.casting = nil;
            elseif count > 0 then
                world.casting = { kind = kind, id = ashita.bits.unpack_be(data, 0, 213, 17), t = xi_now() };
            end
        elseif kind == 4 or kind == 5 then
            world.casting = nil;
        end
    end
    -- party weapon skill (category 3) landing on a mob opens a skillchain window
    if kind == 3 and count > 0 and world.party_ids()[actor] ~= nil then
        local tgt = ashita.bits.unpack_be(data, 0, 150, 32);
        if bit.band(tgt, 0x1000000) ~= 0 then
            world.combo = { target = tgt, ends = xi_now() + 8, ws = ashita.bits.unpack_be(data, 0, 86, 16) };
        end
    end
    if count == 0 or bit.band(actor, 0x1000000) == 0 then return; end      -- only mobs/NPCs (0x01xxxxxx ids)
    local target = ashita.bits.unpack_be(data, 0, 150, 32);
    mob_targets[actor] = { target = target, t = xi_now() };
end

--- Enmity estimate for a mob (FFXI doesn't expose real enmity): 'red' when it is attacking you, 'orange' when it
-- is attacking someone else in your party, 'green' when your party has it but it hasn't acted on anyone yet.
-- Returns also whether to flash (it is attacking you).
function world.enmity(idx)
    local claim, engaged = world.claim(idx);
    if claim ~= 'party' then return nil; end
    local last = mob_targets[mm():GetEntity():GetServerId(idx)];
    if engaged and last then
        local slot = world.party_ids()[last.target];
        if slot == 0 then return 'red', true; end
        if slot ~= nil then return 'orange', false; end
    end
    return 'green', false;
end

--- Seconds left in the skillchain window on the current target, or nil.
function world.combo_left()
    local c = world.combo;
    if c == nil then return nil; end
    local left = c.ends - xi_now();
    if left <= 0 then world.combo = nil; return nil; end
    local idx = world.target_index();
    if idx == 0 or mm():GetEntity():GetServerId(idx) ~= c.target then return nil; end
    return left;
end

return world;
