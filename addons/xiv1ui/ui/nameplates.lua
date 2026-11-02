--[[
* xiv1ui - names over characters in the HUD's serif, in 1.0's colours (reference §9): other PCs cream, party blue,
* NPCs green, enemies yellow / red-pink (claimed by your party) / purple (claimed by others). Your current target's
* name is drawn a little larger; distant names are smaller and fainter, so crowds stay readable.
*
* The game's own name plates are switched off through the Nameplate plugin ("/nameplate mode none"; it ships with
* HorizonXI), and switched back on ("/nameplate mode all") when xiv1ui unloads or this option is turned off. Without
* the plugin, xiv1ui leaves the game's names alone and draws none of its own (otherwise every name would show twice).
*
* Position: while running, the logical position (LocalPosition) leads the drawn body and the actor's copy at
* actor+0x5FC (x, height, y; the bounding box follows it too) trails it, each by about half a yalm. A name pinned to
* either one ran ahead of the body ("a carrot on a stick") or drifted behind it, so names use the midpoint.
* Height: the actor also holds the model's bounding box (8 corners of x, height, y, w from actor+0x918; corners 0-3
* at the feet, 4-7 at the top), which gives every model its own height, large monsters included. ModelSize reads -1.
* The race table below is only a fallback.
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local world   = require('core.world');
local project = require('core.project');
local store   = require('core.store');
local xi_now  = require('core.now');

local plates = {};
local covered = {};          -- rectangles of the game's visible windows (refreshed with the scan)

local RANGE = 30;                       -- yalms: your target and party members
local NAME_RANGE = 12;                  -- yalms: everyone else. Names aren't hidden behind walls (no way found yet to
                                        -- tell from an addon; see docs/MODDING-NOTES.md), so they stay close.
local HEIGHT = { [1] = 1.95, [2] = 1.85, [3] = 2.15, [4] = 2.05, [5] = 1.15, [6] = 1.15, [7] = 1.75, [8] = 2.35 };
local MOB_HEIGHT = 2.1;
-- per-race fine tuning on top of the box (yalms, + = higher), set by eye: the box is a coarse per-model shape
local RACE_ADJ = { [1] = 0.12, [3] = 0.12, [4] = 0.12, [7] = -0.08, [8] = 0.12 };
local LIFT = -0.08;                      -- name baseline relative to the top of the model's box (yalms; negative = just below it, as the box includes ears and hair)
local NEAR, FAR = 6, NAME_RANGE;         -- other names shrink and fade between these distances (yalms)

local objs = {};                         -- entity index -> text object
local list = {};                         -- indices to draw (rebuilt a few times a second)
local next_scan = 0;
local hiding = false;                    -- the game's names are switched off

local ffi = require('ffi');
local mem = require('core.mem');

local function mm() return AshitaCore:GetMemoryManager(); end


local function plugin_loaded()
    local ok, r = pcall(function () return AshitaCore:GetPluginManager():IsLoaded('Nameplate'); end);
    return ok and r == true;
end

local function set_native(hide)
    if hide == hiding then return; end
    hiding = hide;
    AshitaCore:GetChatManager():QueueCommand(-1, hide and '/nameplate mode none' or '/nameplate mode all');
end

local function active()
    return store.data.nameplates ~= false and plugin_loaded();
end

function plates.release()
    if hiding then set_native(false); end
end

local function wanted(e, i, tgt, party)
    local rf = e:GetRenderFlags0(i);
    if rf == nil or bit.band(rf, 0x200) == 0 or bit.band(rf, 0x4000) ~= 0 then return false; end
    local d = e:GetDistance(i);
    local far = (i == tgt or party[e:GetServerId(i)] ~= nil) and RANGE or NAME_RANGE;
    if d == nil or d > far * far then return false; end
    local name = e:GetName(i);
    if name == nil or name == '' then return false; end
    local sf = e:GetSpawnFlags(i) or 0;
    if bit.band(sf, 0x20) ~= 0 or name:sub(1, 5) == 'Door:' then return false; end     -- doors
    if (e:GetHPPercent(i) or 0) == 0 and bit.band(sf, 0x10) ~= 0 then return false; end  -- defeated enemies
    return true;
end

local function scan()
    local e = mm():GetEntity();
    list = {};
    local tgt, party = world.target_index(), world.party_ids();
    for i = 0, 2303 do
        if wanted(e, i, tgt, party) then list[#list + 1] = i; end
    end
    -- far names first, so nearer ones are drawn on top
    table.sort(list, function (a, b) return (e:GetDistance(a) or 0) > (e:GetDistance(b) or 0); end);
end

local FADE = 0.35;                       -- seconds for a name to fade in or out
local fade = {};                         -- entity index -> current alpha (0..1)
local last_t = nil;

function plates.render()
    if not active() then
        if hiding then set_native(false); end
        return;
    end
    set_native(true);
    -- during an event the HUD (names included) steps aside, but the game's own names stay off too
    if require('core.event').active() then fade = {}; return; end
    -- nor over the full-screen maps (the area map, "mapframe"; Region Info's, "cnqframe")
    local gw = require('core.gamewin');
    if gw.window('mapframe') ~= nil or gw.window('cnqframe') ~= nil then fade = {}; return; end

    local now = xi_now();
    if now >= next_scan then
        scan();
        next_scan = now + 0.25;
        -- the game's own windows (menus xiv1ui leaves to it, a shop's lists, ...) are drawn under the HUD: a name
        -- over one would sit on top of it, so names stay off them
        covered = gw.occupied();
    end
    local dt = last_t and math.min(0.25, now - last_t) or 0;
    last_t = now;

    local e = mm():GetEntity();
    local tgt = world.target_index();
    local party = world.party_ids();

    -- names fading out (no longer wanted) are drawn first, under the current ones
    local inlist, order = {}, {};
    for _, i in ipairs(list) do inlist[i] = true; end
    for i in pairs(fade) do if not inlist[i] then order[#order + 1] = i; end end
    for _, i in ipairs(list) do order[#order + 1] = i; end

    for _, i in ipairs(order) do
        local name = require('core.npcnames').resolve(e:GetName(i), e:GetServerId(i));
        local a = fade[i] or 0;
        a = inlist[i] and math.min(1, a + dt / FADE) or math.max(0, a - dt / FADE);
        if (a <= 0 and not inlist[i]) or name == nil or name == '' then
            fade[i] = nil;
        else
            fade[i] = a;
            local sx, sy, vis;
            local x, ht, y, h = project.anchor(i);
            -- (an anchor without a height, e.g. a model still loading: use the race's height below)
            if x and ht and y and h then
                sx, sy, vis = project.point(x, ht - h - LIFT - (RACE_ADJ[e:GetRace(i) or 0] or 0), y);
            else
                local up = (world.kind(i) == 'mob') and MOB_HEIGHT or (HEIGHT[e:GetRace(i) or 0] or 2.1);
                sx, sy, vis = project.entity(i, up);
            end
            if sx and vis and a > 0 then
                local o = objs[i];
                if o == nil then
                    o = text.new('name', { font_height = 19, font_alignment = text.align.Center, outline_width = 3 });
                    objs[i] = o;
                end
                local is_t = (i == tgt);
                local d = math.sqrt(e:GetDistance(i) or 0);
                local k = math.max(0, math.min(1, (d - NEAR) / (FAR - NEAR)));    -- 0 near .. 1 far
                if is_t or party[e:GetServerId(i)] then k = 0; end
                o:set_font_height(is_t and 22 or math.floor(19 - 5 * k + 0.5));
                o:set_font_color(world.name_color(i));
                o:set_opacity(a * (is_t and 1 or (1 - 0.55 * k)));
                local fh = is_t and 22 or 19;
                local hw = #name * fh * 0.3;           -- (about half the name's width; exactness doesn't matter here)
                local hidden = false;
                for _, r in ipairs(covered) do
                    if sx + hw > r[1] and sx - hw < r[1] + r[3] and sy > r[2] and sy - fh < r[2] + r[4] then
                        hidden = true;
                        break;
                    end
                end
                if not hidden then text.draw(o, name, sx, sy, 'baseline'); end
            end
        end
    end
end

return plates;
