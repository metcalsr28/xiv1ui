--[[
* xiv1ui - the diagnostics log (Configuration » Experimental, off by default), for bug reports from players.
*
* Most bugs seen only on other setups were silent disagreements between xiv1ui and the game: a different row lit
* than the game's cursor, a list handed back to FFXI because the counts differed, a signature not found on another
* client build. While it's on, those are written to addons/xiv1ui/diag.log (the last few minutes), with a header
* describing the setup; /xiv1ui report puts it together with errors.log in one file to attach.
*
* Never logged: chat text, tells, other players' names. Everything here is wrapped: diagnostics must never break
* what they watch, and cost nothing while off.
--]]

local store = require('core.store');
local now   = require('core.now');

local diag = {};

local MAX_LINES, MAX_FILE, MAX_AGE = 2000, 3000, 300;    -- ring size, file lines, file age (s)
local root, version = nil, '?';
local lines = {};            -- { t = os.time(), s = 'HH:MM:SS kind message' }
local dirty, flushed = false, 0;
local header = nil;          -- (built when switched on, again for a report)
local was_on = false;
local last_focus = false;
local missed_sigs = {};      -- signatures not found this load (kept even while off, for the header)
local once_seen = {};        -- diag.once keys
local changes = {};          -- diag.change key -> { msg, t }
local agrees = {};           -- diag.agree key -> { since, t, logged }

function diag.on() return store.data.diag == true; end

local function add(kind, msg)
    lines[#lines + 1] = { t = os.time(), s = os.date('%H:%M:%S') .. ' ' .. kind .. ' ' .. msg:gsub('[\r\n]+', ' | ') };
    if #lines > MAX_LINES + 200 then         -- (trimmed in batches: shifting the table every line costs)
        local keep = {};
        for i = #lines - MAX_LINES + 1, #lines do keep[#keep + 1] = lines[i]; end
        lines = keep;
    end
    dirty = true;
end

--- Append a line ("HH:MM:SS kind message"). Does nothing while the log is off.
function diag.log(kind, fmt, ...)
    if store.data.diag ~= true then return; end
    local ok, msg = pcall(string.format, fmt, ...);
    pcall(add, tostring(kind), ok and msg or tostring(fmt));
end

--- Log only the first time `key` is seen this load.
function diag.once(key, kind, fmt, ...)
    if store.data.diag ~= true or once_seen[key] then return; end
    once_seen[key] = true;
    diag.log(kind, fmt, ...);
end

--- Log when the message for `key` changes; the same message again only after a second without it (a new
-- occurrence, not the same one seen every frame).
function diag.change(key, kind, fmt, ...)
    if store.data.diag ~= true then return; end
    local ok, msg = pcall(string.format, fmt, ...);
    if not ok then return; end
    local t, c = now(), changes[key];
    if c and c.msg == msg and t - c.t < 1 then c.t = t; return; end
    changes[key] = { msg = msg, t = t };
    pcall(add, tostring(kind), msg);
end

--- Watch xiv1ui and the game agreeing about `key` (ok): a disagreement lasting over half a second is logged once,
-- with detail() (called only then), and its end too. Call every frame while the screen is up.
function diag.agree(key, ok, kind, detail)
    if store.data.diag ~= true then return; end
    local t, a = now(), agrees[key];
    if a and t - a.t > 1 then a = nil; agrees[key] = nil; end         -- (the screen was closed meanwhile)
    if ok then
        if a and a.logged then pcall(add, kind, string.format('%s: agree again after %.1f s', key, t - a.since)); end
        agrees[key] = nil;
        return;
    end
    if a == nil then a = { since = t }; agrees[key] = a; end
    a.t = t;
    if not a.logged and t - a.since > 0.5 then
        a.logged = true;
        local okd, msg = pcall(detail);
        pcall(add, kind, key .. ': ' .. (okd and tostring(msg) or ('(detail failed: ' .. tostring(msg) .. ')')));
    end
end

--- A memory signature not found (core/mem.lua mem.find): remembered for the header, logged once.
function diag.missed(module, sig, off, idx)
    local key = module .. ' ' .. sig .. ' +' .. tostring(off) .. ' #' .. tostring(idx);
    if missed_sigs[key] then return; end
    missed_sigs[key] = true;
    missed_sigs[#missed_sigs + 1] = key;
    diag.log('signature', 'not found: %s', key);
end

-- The setup, for the header. Each part on its own pcall: a missing API just leaves its line out.
local ffi = require('ffi');
pcall(ffi.cdef, 'void* __stdcall GetModuleHandleA(const char* name);');
pcall(ffi.cdef, 'uint32_t __stdcall GetModuleFileNameA(void* module, char* name, uint32_t size);');
pcall(ffi.cdef, 'int __stdcall GetSystemMetrics(int index);');
pcall(ffi.cdef, 'const char* wine_get_version(void);');

local function os_name()
    local ok, v = pcall(function () return ffi.string(ffi.load('ntdll').wine_get_version()); end);
    return ok and ('Wine ' .. v) or 'Windows';
end

-- FFXiMain.dll's link time (PE header) and file size: they tell client builds apart
local function client()
    local h = ffi.C.GetModuleHandleA('FFXiMain.dll');
    if h == nil then return 'FFXiMain.dll not loaded'; end
    local mem = require('core.mem');
    local base = tonumber(ffi.cast('uintptr_t', h));
    local pe = mem.u32(base + 0x3C);
    local stamp = pe and mem.u32(base + pe + 8);
    local out = 'FFXiMain.dll';
    if stamp then out = out .. string.format(' built %s (0x%08X)', os.date('!%Y-%m-%d %H:%M', stamp), stamp); end
    local buf = ffi.new('char[520]');
    local n = ffi.C.GetModuleFileNameA(h, buf, 520);
    if n > 0 then
        local f = io.open(ffi.string(buf, n), 'rb');
        if f then out = out .. string.format(', %d bytes', f:seek('end') or 0); f:close(); end
    end
    return out;
end

local function registry(key)
    return AshitaCore:GetConfigurationManager():GetString('boot', 'ffxi.registry', key) or '?';
end

local function names(mgr)
    local out = {};
    for i = 0, (mgr:Count() or 0) do
        local ok, v = pcall(mgr.Get, mgr, i);
        if ok and type(v) ~= 'string' and v ~= nil then
            ok, v = pcall(function () return v:GetName(); end);
        end
        if ok and type(v) == 'string' and v ~= '' then out[#out + 1] = v; end
    end
    return table.concat(out, ', ');
end

local function build_header()
    local h = { '# xiv1ui diagnostics, ' .. os.date('%Y-%m-%d %H:%M:%S') };
    local function line(fn)
        local ok, s = pcall(fn);
        if ok and s and s ~= '' then h[#h + 1] = '# ' .. s; end
    end
    line(function () return 'xiv1ui ' .. version; end);
    line(function ()
        if ashita.addons_version == nil then return nil; end
        return string.format('Ashita addons plugin %s, interface %s', tostring(ashita.addons_version),
        tostring(ashita.interface_version)); end);
    line(function () return 'OS: ' .. os_name(); end);
    line(client);
    line(function ()
        return string.format('Screen %dx%d, game window %sx%s, game UI %sx%s, xiv1ui UI scale %s',
            ffi.C.GetSystemMetrics(0), ffi.C.GetSystemMetrics(1), registry('0001'), registry('0002'),
            registry('0037'), registry('0038'), tostring(store.data.ui_scale));
    end);
    line(function () return 'Addons: ' .. names(AddonManager); end);
    line(function () return 'Plugins: ' .. names(AshitaCore:GetPluginManager()); end);
    line(function ()
        local pl = AshitaCore:GetMemoryManager():GetPlayer();
        return string.format('Job %d/%d, level %d/%d', pl:GetMainJob(), pl:GetSubJob(), pl:GetMainJobLevel(),
            pl:GetSubJobLevel());
    end);
    line(function ()
        local s = {};
        for _, k in ipairs({ 'hide_native', 'cmd_menu', 'choice_menu', 'status_panel', 'pad', 'experimental' }) do
            s[#s + 1] = k .. '=' .. tostring(store.data[k]);
        end
        return 'Settings: ' .. table.concat(s, ' ');
    end);
    line(function ()
        if #missed_sigs == 0 then return 'Signatures: all found so far'; end
        return 'Signatures not found: ' .. table.concat(missed_sigs, '; ');
    end);
    return table.concat(h, '\n') .. '\n';
end

local function write_file()
    if not root then return; end
    local f = io.open(root .. 'diag.log', 'w');
    if not f then return; end
    f:write(header or build_header());
    local cut, first = os.time() - MAX_AGE, math.max(1, #lines - MAX_FILE + 1);
    for i = first, #lines do
        if lines[i].t >= cut then f:write(lines[i].s, '\n'); end
    end
    f:close();
end

--- Write the file now if anything is new and a second has passed (force: anyway).
function diag.flush(force)
    if not dirty or not root then return; end
    local t = now();
    if not force and t - flushed < 1 then return; end
    flushed, dirty = t, false;
    pcall(write_file);
end

-- The last session's lines (e.g. what led up to an automatic reload) carry on at the top of the new log.
local carried = false;
local function carry_over()
    if carried then return; end
    carried = true;
    local f = root and io.open(root .. 'diag.log', 'r');
    if not f then return; end
    local old = {};
    for l in f:lines() do
        if l:sub(1, 1) == '#' then old = {}; elseif l ~= '' then old[#old + 1] = l; end
    end
    f:close();
    if #old == 0 then return; end
    local t, out = os.time(), {};
    out[1] = { t = t, s = '-- previous session --' };
    for i = math.max(1, #old - 500 + 1), #old do out[#out + 1] = { t = t, s = old[i] }; end
    out[#out + 1] = { t = t, s = '-- this session --' };
    for _, l in ipairs(lines) do out[#out + 1] = l; end        -- (anything logged while modules loaded)
    lines = out;
end

local function start()
    header = build_header();
    pcall(carry_over);
    add('diag', 'on');
    diag.flush(true);
end

--- At load: where the files go and xiv1ui's version.
function diag.init(addon_root, addon_version)
    root, version = addon_root, tostring(addon_version);
    if diag.on() then was_on = true; pcall(start); end
end

-- Once a frame: switching on / off, the focused game window, and the flush.
local function tick()
    local on = store.data.diag == true;
    if on ~= was_on then
        was_on = on;
        if on then start(); else add('diag', 'off'); diag.flush(true); end
    end
    if not on then return; end
    local _, name = require('core.native').focused();
    name = name or '';
    if name ~= last_focus then
        add('focus', (name ~= '' and name or '(none)') .. (last_focus and (' (was ' .. (last_focus ~= '' and last_focus or 'none') .. ')') or ''));
        last_focus = name;
    end
    diag.flush();
end

function diag.tick()
    if store.data.diag ~= true and not was_on then return; end
    pcall(tick);
end

--- /xiv1ui report: header + errors.log + diag.log in report.txt. Returns true if written.
function diag.report()
    if not root then return false; end
    local ok = pcall(function ()
        diag.flush(true);
        local function slurp(name)
            local f = io.open(root .. name, 'r');
            if not f then return nil; end
            local s = f:read('*a');
            f:close();
            return s;
        end
        local out = { build_header() };
        out[#out + 1] = '\n==== errors.log ====\n';
        out[#out + 1] = slurp('errors.log') or '(none)\n';
        out[#out + 1] = '\n==== diag.log ====\n';
        out[#out + 1] = slurp('diag.log') or
            '(the diagnostics log is off: Configuration » Experimental » Diagnostics log)\n';
        local f = assert(io.open(root .. 'report.txt', 'w'));
        f:write(table.concat(out));
        f:close();
    end);
    return ok;
end

return diag;
