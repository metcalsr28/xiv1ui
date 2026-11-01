--[[
* xiv1ui - things drawn in the world, after FFXIV 1.0:
*   - the target cursor (reference §11): a gold broken ring over the current target that turns slowly, replaced by
*     three gold shards pointing inward while locked on;
*   - pop-up numbers (reference §15): damage in white italic numerals, criticals larger in gold, heals in green and
*     "Miss" in grey, rising from whoever was hit and fading out. Only actions involving you, your party or your
*     target are shown.
--]]

local xi_now = require('core.now');
local draw    = require('core.draw');
local text    = require('core.text');
local world   = require('core.world');
local project = require('core.project');
local ap      = require('core.actionpacket');

local worldfx = {};

local pops = {};          -- { obj, idx, t0, dx }
local pool = {};
local LIFE = 1.4;

local function get_obj()
    local o = table.remove(pool);
    if o then return o; end
    return text.new('numeral', { font_height = 34, font_alignment = text.align.Center, gradient_style = 0 });
end

local function index_of(server_id)
    if bit.band(server_id, 0x1000000) ~= 0 then
        local idx = bit.band(server_id, 0xFFF);
        if idx >= 0x900 then idx = idx - 0x100; end
        if AshitaCore:GetMemoryManager():GetEntity():GetServerId(idx) == server_id then return idx; end
    end
    local e = AshitaCore:GetMemoryManager():GetEntity();
    for i = 0, 2303 do if e:GetServerId(i) == server_id then return i; end end
    return nil;
end

function worldfx.debug_pops() return #pops; end

-- Several numbers for one target at once (a round of double / triple attacks, a multi-hit weapon skill, the party
-- hitting together) come one after another, a beat apart, and each new one lifts those already up by a line, so they
-- stack instead of piling up in one spot. A backlog is squeezed so nothing waits more than
-- about three quarters of a second.
local GAP, MAX_WAIT = 0.25, 0.75;
local next_at = {};       -- target index -> when its next number may start
local function pop(idx, str, color, height)
    local o = get_obj();
    o:set_font_color(color);
    o:set_font_height(height);
    o:set_text(str);
    local now = xi_now();
    local t0 = math.max(now, next_at[idx] or 0);
    local wait = t0 - now;
    if wait > MAX_WAIT then t0, wait = now + MAX_WAIT, MAX_WAIT; end
    next_at[idx] = t0 + GAP * math.max(0.3, 1 - wait / MAX_WAIT);
    local k = math.floor(wait / GAP + 0.5);           -- its place in the run: 0, 1, 2 ...
    pops[#pops + 1] = { obj = o, idx = idx, t0 = t0, dx = (k % 2 == 0 and -1 or 1) * 14 + math.random(-6, 6), lift = 0 };
end

worldfx.pop = function (...) return pop(...); end

function worldfx.packet(e)
    if e.id ~= 0x028 then return; end
    local a = ap.parse(e);
    if a == nil then return; end
    local party = world.party_ids();
    local tgt = world.target_index();
    local tgt_id = tgt ~= 0 and AshitaCore:GetMemoryManager():GetEntity():GetServerId(tgt) or -1;
    local involved = party[a.actor] ~= nil or a.actor == tgt_id;
    for _, t in ipairs(a.targets) do
        local mine = involved or party[t.id] ~= nil or t.id == tgt_id;
        if mine then
            local idx = index_of(t.id);
            if idx then
                for _, act in ipairs(t.actions) do
                    if ap.MISS[act.message] then
                        pop(idx, 'Miss', 0xFFB8BCC8, 30);
                    elseif ap.HEAL[act.message] and act.param > 0 then
                        pop(idx, tostring(act.param), 0xFF9BF08C, 38);
                    elseif act.param > 0 and (a.category == 1 or a.category == 2 or a.category == 3 or a.category == 4
                            or a.category == 6 or a.category == 11 or a.category == 13) then
                        if ap.CRIT[act.message] then pop(idx, tostring(act.param), 0xFFFFD86A, 52);
                        else pop(idx, tostring(act.param), 0xFFFFFFFF, 40); end
                    end
                end
            end
        end
    end
end

function worldfx.render()
    local now = xi_now();

    -- target cursor
    local idx = world.target_index();
    local name_a, ax, ah, ay = nil, nil, nil, nil;
    if idx == 0 then name_a, ax, ah, ay = world.target_actor(); end
    if name_a then
        -- a target with no entity (the Mog House door): the ring at FFXI's own arrow height above it
        local sx, sy, vis = project.point(ax, ah - 0.4, ay);
        if sx and vis then draw.image('target_ring', sx - 36, sy - 36, { rot = now * 0.6, color = 0xE0FFFFFF }); end
    elseif idx ~= 0 then
        -- middle of the model, where it's drawn; objects without a model (doors) at FFXI's own arrow height
        local door = bit.band(AshitaCore:GetMemoryManager():GetEntity():GetSpawnFlags(idx) or 0, 0x20) ~= 0;
        local sx, sy, vis = project.on_model(idx, 0.55, 0, door and 0.4 or 1.2);
        if sx and vis then
            if world.locked() then
                draw.image('lock_mark', sx - 26, sy - 26, { scale = 2, rot = now * 0.8 });
            else
                draw.image('target_ring', sx - 36, sy - 36, { rot = now * 0.6, color = 0xE0FFFFFF });
            end
        end
    end

    -- pop-up numbers
    for i = #pops, 1, -1 do
        local p = pops[i];
        local age = now - p.t0;
        if age > LIFE then
            pool[#pool + 1] = p.obj;
            table.remove(pops, i);
        elseif age >= 0 then
            -- lifted a line for each newer number on the same target that has appeared since
            local above = 0;
            for _, q in ipairs(pops) do
                if q.idx == p.idx and q.t0 > p.t0 and q.t0 <= now then above = above + 1; end
            end
            p.lift = p.lift + (above * 36 - p.lift) * math.min(1, (now - (p.drawn or now)) * 14);
            p.drawn = now;
            local sx, sy, vis = project.on_model(p.idx, 0.9, 0, 1.8);
            if sx and vis then
                local rise = 36 * math.min(1, age / GAP) + 14 * age + p.lift;
                local alpha = age < LIFE - 0.4 and 1 or (LIFE - age) / 0.4;
                p.obj:set_opacity(alpha);
                text.draw(p.obj, p.obj.settings.text, sx + p.dx, sy - rise, 'baseline');
            end
        end
    end
end

return worldfx;
