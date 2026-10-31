--[[
* xiv1ui - hiding the native FFXI panels that xiv1ui modules replace.
*
* Each module lists the panel keys it replaces in `replaces`; when the module is active those panels are hidden, and
* they come back when xiv1ui unloads. Most panels are hidden through the HXIUIBegone addon (GPL, approved on
* HorizonXI) and its command interface; if it isn't loaded they simply stay visible.
*
* The target box and the network box are hidden here instead, because HXIUIBegone's method (moving it off-screen) has no effect on this
* client. Like the party list, the box is a game window whose object carries two visibility bytes (+0x69, +0x6A);
* clearing them hides the box and the arrow over the target, which xiv1ui's own target cursor replaces. The window
* is found by its name in the game's menu table ("menu    targetwi", window slot pointer 0x20 bytes after it), and
* every access is checked (core/mem.lua).
--]]

local xi_now = require('core.now');
local mem    = require('core.mem');

local native = {};

local wanted = {};        -- key -> true
local applied = false;
local load_time = xi_now();

-- Panels xiv1ui hides itself: key -> game menu name.
-- (the network box: HXIUIBegone's hide doesn't hold on this client, it comes back whenever something is targeted;
-- the chat log and the party list: HXIUIBegone's hides don't work on CatsEyeXI's client build)
local OWN = { target = 'targetwi', connection = 'netstat', gauges = 'gaugewin', chat1 = 'logwindo', party = 'partywin',
              castbar = 'casttime' };
local SPECIAL = { compass = true, clock = true };      -- hidden here too, not through windows (see compass_hide)
local own = {};           -- key -> { slot, obj, orig = { b69, b6a } }

--- The window slot for a game menu name, or nil. The name appears more than once in memory; the real entry is
-- followed by 16 zero bytes and then a readable slot pointer.
local slot_cache = {};       -- name -> slot (a descriptor's slot never moves; a scan costs milliseconds)
local function find_slot(name)
    local c = slot_cache[name];
    if c and mem.ok(c, 4) then return c; end
    local hex = '6D656E7520202020';
    for i = 1, 8 do hex = hex .. string.format('%02X', (name .. '        '):byte(i)); end
    for n = 0, 7 do
        local a = ashita.memory.find('FFXiMain.dll', 0, hex, 0, n);
        if a == nil or a == 0 then break; end
        local slot = mem.u32(a + 0x20);
        if mem.u32(a + 0x10) == 0 and mem.u32(a + 0x1C) == 0 and slot and mem.ok(slot, 4) then
            slot_cache[name] = slot;
            return slot;
        end
    end
    return nil;
end

local function own_hide(key)
    local h = own[key];
    if h == nil then
        h = { slot = find_slot(OWN[key]) or false };
        own[key] = h;
    end
    if not h.slot then return; end
    local obj = mem.chain(h.slot, 0, 8);
    if obj == nil then h.obj = nil; return; end         -- window not open (no target)
    if obj ~= h.obj then
        local a, b = mem.u8(obj + 0x69), mem.u8(obj + 0x6A);
        if (a ~= 0 and a ~= 1) or (b ~= 0 and b ~= 1) then return; end    -- not the layout we expect: leave it alone
        h.obj, h.orig = obj, { a, b };
    end
    if mem.u8(obj + 0x69) ~= 0 then mem.w8(obj + 0x69, 0); end
    if mem.u8(obj + 0x6A) ~= 0 then mem.w8(obj + 0x6A, 0); end
end

local function own_restore()
    for _, h in pairs(own) do
        -- only an object the slot still points at, and only bytes still holding our value
        if h.obj and h.slot and mem.chain(h.slot, 0, 8) == h.obj then
            if mem.u8(h.obj + 0x69) == 0 then mem.w8(h.obj + 0x69, h.orig[1]); end
            if mem.u8(h.obj + 0x6A) == 0 then mem.w8(h.obj + 0x6A, h.orig[2]); end
        end
        h.obj = nil;
    end
end

native.find_slot = find_slot;

-- The compass and the clock aren't windows. The compass is drawn unless one byte in the game's code is 0 (FFXiMain.dll,
-- 0x24 bytes after the signature below; researched for HXIUIBegone from Arielfy's FancyCompass); it is patched only when
-- the signature matches exactly once and the byte holds the expected 1, so another client build keeps its compass.
-- The clock is the game's own /clock off; the game then prints the time in the log, which the chat log drops
-- (native.quiet()).
local compass = nil;         -- { addr } while patched; false if unavailable
local quiet_until = 0;

local function code_write(addr, value)
    local ok, prev = ashita.memory.unprotect(addr, 1);
    if not ok or prev == nil then return false; end
    ashita.memory.write_uint8(addr, value);
    ashita.memory.protect(addr, 1, prev);
    return true;
end

local function compass_hide()
    if compass ~= nil then return; end
    compass = false;
    local sig = '33C0668B81????????483DE3000000';
    local m = ashita.memory.find('FFXiMain.dll', 0, sig, 0, 0);
    if m == nil or m == 0 or ashita.memory.find('FFXiMain.dll', 0, sig, 0, 1) ~= 0 then return; end
    local addr = m + 0x24;
    if mem.u8(addr) ~= 1 then return; end
    if code_write(addr, 0) then compass = { addr = addr }; end
end

local function compass_restore()
    if compass and mem.u8(compass.addr) == 0 then code_write(compass.addr, 1); end
    compass = nil;
end

-- HXIUIBegone still hides what xiv1ui doesn't (the second chat window, the alliance lists) when it's loaded. Ashita
-- builds without the AddonManager object (CatsEyeXI's) can't say, and HXIUIBegone refuses to work there anyway.
local function hxiui_loaded()
    local ok, r = pcall(function () return AddonManager ~= nil and AddonManager:IsLoaded('HXIUIBegone'); end);
    return ok and r == true;
end

local function clock(on)
    quiet_until = xi_now() + 2;
    AshitaCore:GetChatManager():QueueCommand(-1, on and '/clock on' or '/clock off');
end

--- True for a moment after xiv1ui switched the game's clock: the time lines the game prints then aren't news.
function native.quiet() return xi_now() < quiet_until; end

function native.want(keys)
    for _, k in ipairs(keys or {}) do wanted[k] = true; end
end

--- Called every frame; applies the hides once, a moment after load (HXIUIBegone may load after us).
function native.tick(enabled)
    if not enabled then
        if applied then native.restore(); end
        return;
    end
    if xi_now() - load_time < 3 then return; end
    if not applied then
        applied = true;
        local cm = AshitaCore:GetChatManager();
        local hx = hxiui_loaded();
        for k in pairs(wanted) do
            if hx and not OWN[k] and not SPECIAL[k] then cm:QueueCommand(-1, '/hxiui hide ' .. k .. ' on'); end
        end
        if wanted.compass then compass_hide(); end
        if wanted.clock then clock(false); end
    end
    -- the game rebuilds its windows (e.g. on every new target), so own hides are re-checked each frame
    for k in pairs(wanted) do
        if OWN[k] then own_hide(k); end
    end
end

--- The window that has the game's input focus: obj, its 8-character menu name (trailing spaces cut). nil if none.
-- (The focus pointer is found with the Balloon addon's pattern; see docs/MODDING-NOTES.md.)
local focus_ptr = nil;
function native.focused()
    if focus_ptr == nil then
        local p = ashita.memory.find('FFXiMain.dll', 0, '8B480C85C974??8B510885D274??3B05', 16, 0);
        focus_ptr = (p and p ~= 0) and p or false;
    end
    if not focus_ptr then return nil; end
    local obj = mem.chain(focus_ptr, 0, 0);
    if obj == nil then return nil; end
    local hdr = mem.u32(obj + 4);
    if hdr == nil or not mem.ok(hdr + 0x4E, 8) then return nil; end
    return obj, (ashita.memory.read_string(hdr + 0x4E, 8) or ''):gsub('[%z ]+$', '');
end

function native.restore()
    own_restore();
    compass_restore();
    if not applied then return; end
    local cm = AshitaCore:GetChatManager();
    local hx = hxiui_loaded();
    for k in pairs(wanted) do
        if hx and not OWN[k] and not SPECIAL[k] then cm:QueueCommand(-1, '/hxiui hide ' .. k .. ' off'); end
    end
    if wanted.clock then clock(true); end
    applied = false;
end

return native;
