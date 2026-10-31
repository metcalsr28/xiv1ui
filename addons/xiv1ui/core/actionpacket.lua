--[[
* xiv1ui - action packet (0x028) parser. Read-only: it decodes what the server tells the client about actions
* (who acted, what kind, which targets, the per-target result and message id) so the HUD can show it.
*
* Layout (bit offsets from the start of the packet): actor id @40 (32), target count @72 (6), category @82 (4),
* param @86 (32), recast @118 (32), then per target: id (32), action count (4), and per action: reaction (5),
* animation (12), effect (7), knockback (3), param (17), message (10), unknown (31), [additional effect flag (1)
* + 10/17/10], [spikes flag (1) + 10/14/10].
--]]

local M = {};

function M.parse(e)
    local data, size = e.data_raw, e.size * 8;
    local pos = 40;
    local bad = false;
    local function bits(n)
        if pos + n > size then bad = true; return 0; end
        local v = ashita.bits.unpack_be(data, 0, pos, n);
        pos = pos + n;
        return v;
    end
    local a = {};
    a.actor = bits(32);
    local count = bits(6);
    pos = pos + 4;
    a.category = bits(4);
    a.param = bits(32);
    a.recast = bits(32);
    a.targets = {};
    for _ = 1, count do
        local t = { id = bits(32), actions = {} };
        local n = bits(4);
        for _ = 1, n do
            local act = {};
            act.reaction  = bits(5);
            act.animation = bits(12);
            act.effect    = bits(7);
            act.knockback = bits(3);
            act.param     = bits(17);
            act.message   = bits(10);
            bits(31);
            if bits(1) == 1 then act.add = { param = (function () bits(10); return bits(17); end)(), message = bits(10) }; end
            if bits(1) == 1 then bits(10); bits(14); bits(10); end
            t.actions[#t.actions + 1] = act;
        end
        a.targets[#a.targets + 1] = t;
        if bad then break; end
    end
    if bad then return nil; end
    return a;
end

-- Message ids, grouped for display (from FFXI's battle message table).
M.HEAL = { [7] = true, [24] = true, [102] = true, [103] = true, [238] = true, [263] = true, [306] = true,
           [318] = true, [367] = true, [373] = true };
M.MISS = { [15] = true, [63] = true, [85] = true, [158] = true, [188] = true, [245] = true, [282] = true,
           [324] = true, [354] = true };
M.CRIT = { [67] = true, [353] = true };

return M;
