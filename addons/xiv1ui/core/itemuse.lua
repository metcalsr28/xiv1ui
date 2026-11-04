--[[
* xiv1ui - an enchanted item's charges and reuse time, as FFXI's item info box writes them:
* "<1/1 33:18/[2:00:00, 0:05]>" (charges left / most, time until it can be used again, [its reuse time, the wait
* after equipping it]).
*
* From the item's extra data (the layout Windower's extdata.lua documents for enchanted equipment): the charges left
* at byte 1, and at 4 the time it can next be used, in seconds from the Vana'diel epoch (2002-01-01 00:00 JST). The
* item's resource gives the most charges and the two delays.
--]]

local itemuse = {};

local VANA_EPOCH = 1009810800;      -- 2002-01-01 00:00 JST as a Unix time

local function u32(s, at)
    return s:byte(at + 1) + s:byte(at + 2) * 256 + s:byte(at + 3) * 65536 + s:byte(at + 4) * 16777216;
end

local function hms(t)
    t = math.max(0, math.floor(t));
    local h, m, s = math.floor(t / 3600), math.floor(t / 60) % 60, t % 60;
    if h > 0 then return string.format('%d:%02d:%02d', h, m, s); end
    return string.format('%d:%02d', m, s);
end

--- The charges line for a container item (IItem) and its resource, or nil if it has no charges.
function itemuse.text(item, res)
    local most = res and tonumber(res.MaxCharges) or 0;
    if item == nil or most <= 0 then return nil; end
    local extra = item.Extra;
    if type(extra) ~= 'string' or #extra < 8 then return nil; end
    local left = extra:byte(2);
    local next_use = u32(extra, 4);
    local wait = next_use > 0 and (next_use + VANA_EPOCH - os.time()) or 0;
    local recast, delay = tonumber(res.RecastDelay) or 0, tonumber(res.CastDelay) or 0;
    return string.format('<%d/%d %s/[%s, %s]>', left, most, hms(wait), hms(recast), hms(delay));
end

return itemuse;
