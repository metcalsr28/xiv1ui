--[[
* xiv1ui - the game's own clock. FFXI keeps the server's Unix time in memory; using it (rather than the computer's
* clock) keeps Vana'diel time and buff timers in step with the server even when the two clocks drift.
--]]

local clock = {};

-- Pointer to the client's real-time structure (signature as used by several Ashita addons, e.g. tTimers).
local ptr = require('core.mem').find('FFXiMain.dll', '8B0D????????8B410C8B49108D04808D04808D04808D04C1C3', 2, 0);

--- Server Unix time as the client knows it (falls back to the computer's clock).
function clock.now()
    if ptr ~= nil and ptr ~= 0 then
        local p = ashita.memory.read_uint32(ptr);
        if p ~= 0 then p = ashita.memory.read_uint32(p); end
        if p ~= 0 then
            local t = ashita.memory.read_uint32(p + 0x0C);
            if t and t > 1009810800 then return t; end
        end
    end
    return os.time();
end

clock.EPOCH = 1009810800;   -- 2002-01-01 00:00 JST, the Vana'diel epoch

--- Vana'diel weekday (0 = Firesday), hour, minute and day count; time runs 25x real time.
function clock.vana()
    local vmin = math.floor((clock.now() - clock.EPOCH) * 25 / 60);
    local day = math.floor(vmin / 1440);
    return day % 8, math.floor(vmin / 60) % 24, vmin % 60, day;
end

return clock;
