--[[
* xiv1ui - in-game updates from the project's GitHub releases. Off unless the player turns it on
* (Configuration » Experimental); it only ever runs when asked:
*
*   /xiv1ui update        check for a newer release and say what's available
*   /xiv1ui update now    download it, check every file, install it and reload xiv1ui
* With updates on, xiv1ui also checks once at each start (15 s into the world) and says when a newer release exists.
*
* Each release has manifest.txt at its root: "version <v>", then one "<sha256> <size> <path>" line per file of
* the addon (paths relative to addons/xiv1ui, with forward slashes). Files are fetched over HTTPS from
* raw.githubusercontent.com at the release's tag, written to a staging folder and checked against the manifest; only
* when all of them match are they moved into place. Files the manifest doesn't list are left alone, and so are the
* player's settings (Ashita keeps those in its config folder). A file Windows keeps locked (a font in use) is
* swapped in on the next start instead.
*
* Downloads use Windows' WinINet and checksums its BCrypt, through LuaJIT's FFI. The game pauses while the files
* download (a few seconds).
--]]

local ffi = require('ffi');
local bit = require('bit');

local updater = {};

updater.REPO = 'metcalsr28/xiv1ui';

pcall(ffi.cdef, [[
void* __stdcall InternetOpenA(const char* agent, uint32_t access, const char* proxy, const char* bypass, uint32_t flags);
void* __stdcall InternetOpenUrlA(void* h, const char* url, const char* headers, uint32_t hlen, uint32_t flags, uintptr_t ctx);
int __stdcall InternetReadFile(void* h, void* buf, uint32_t n, uint32_t* read);
int __stdcall InternetCloseHandle(void* h);
int32_t __stdcall BCryptOpenAlgorithmProvider(void** h, const uint16_t* alg, const uint16_t* impl, uint32_t flags);
int32_t __stdcall BCryptCreateHash(void* alg, void** h, void* obj, uint32_t objlen, void* secret, uint32_t slen, uint32_t flags);
int32_t __stdcall BCryptHashData(void* h, const uint8_t* data, uint32_t n, uint32_t flags);
int32_t __stdcall BCryptFinishHash(void* h, uint8_t* out, uint32_t n, uint32_t flags);
int32_t __stdcall BCryptDestroyHash(void* h);
int32_t __stdcall BCryptCloseAlgorithmProvider(void* h, uint32_t flags);
int __stdcall CreateDirectoryA(const char* path, void* sec);
int __stdcall MoveFileExA(const char* from, const char* to, uint32_t flags);
]]);

local function say(s) print('\30\8[xiv1ui] ' .. s .. '\30\1'); end

-- WinINet and BCrypt stay loaded for the rest of the game: WinINet runs threads of its own, and freeing the DLL
-- when the addon unloads (LuaJIT frees ffi.load'ed libraries with the Lua state) deadlocks the game. An extra
-- LoadLibrary reference, never released, keeps them in memory.
pcall(ffi.cdef, 'void* __stdcall LoadLibraryA(const char* name);');
local pinned = false;
local function pin()
    if pinned then return; end
    pinned = true;
    ffi.C.LoadLibraryA('wininet.dll');
    ffi.C.LoadLibraryA('bcrypt.dll');
end

-- HTTPS GET; returns the body or nil, error
local function fetch(url)
    pin();
    local ok, wininet = pcall(ffi.load, 'wininet');
    if not ok then return nil, 'WinINet is not available'; end
    local net = wininet.InternetOpenA('xiv1ui-updater', 0, nil, nil, 0);
    if net == nil then return nil, 'could not open a connection'; end
    -- INTERNET_FLAG_RELOAD | NO_CACHE_WRITE | SECURE
    local h = wininet.InternetOpenUrlA(net, url, 'User-Agent: xiv1ui-updater\r\n', 0xFFFFFFFF,
                                       bit.bor(0x80000000, 0x04000000, 0x00800000), 0);
    if h == nil then wininet.InternetCloseHandle(net); return nil, 'could not reach ' .. url; end
    local parts, buf, got = {}, ffi.new('uint8_t[16384]'), ffi.new('uint32_t[1]');
    while wininet.InternetReadFile(h, buf, 16384, got) ~= 0 and got[0] > 0 do
        parts[#parts + 1] = ffi.string(buf, got[0]);
    end
    wininet.InternetCloseHandle(h);
    wininet.InternetCloseHandle(net);
    return table.concat(parts);
end

local function wide(s)
    local w = ffi.new('uint16_t[?]', #s + 1);
    for i = 1, #s do w[i - 1] = s:byte(i); end
    return w;
end

local function sha256(data)
    pin();
    local bc = ffi.load('bcrypt');
    local alg, h = ffi.new('void*[1]'), ffi.new('void*[1]');
    if bc.BCryptOpenAlgorithmProvider(alg, wide('SHA256'), nil, 0) ~= 0 then return nil; end
    local out = ffi.new('uint8_t[32]');
    local ok = bc.BCryptCreateHash(alg[0], h, nil, 0, nil, 0, 0) == 0
        and bc.BCryptHashData(h[0], ffi.cast('const uint8_t*', data), #data, 0) == 0
        and bc.BCryptFinishHash(h[0], out, 32, 0) == 0;
    if h[0] ~= nil then bc.BCryptDestroyHash(h[0]); end
    bc.BCryptCloseAlgorithmProvider(alg[0], 0);
    if not ok then return nil; end
    local hex = {};
    for i = 0, 31 do hex[#hex + 1] = string.format('%02x', out[i]); end
    return table.concat(hex);
end
updater.sha256 = sha256;

-- "0.2.10" > "0.2.9"
local function newer(a, b)
    local pa, pb = {}, {};
    for n in tostring(a):gmatch('%d+') do pa[#pa + 1] = tonumber(n); end
    for n in tostring(b):gmatch('%d+') do pb[#pb + 1] = tonumber(n); end
    for i = 1, math.max(#pa, #pb) do
        if (pa[i] or 0) ~= (pb[i] or 0) then return (pa[i] or 0) > (pb[i] or 0); end
    end
    return false;
end

--- The latest release: tag (e.g. "v0.2.0") and version ("0.2.0"), or nil, error.
function updater.latest()
    local body, err = fetch('https://api.github.com/repos/' .. updater.REPO .. '/releases/latest');
    if body == nil then return nil, err; end
    local tag = body:match('"tag_name"%s*:%s*"([^"]+)"');
    if tag == nil then return nil, 'no release found'; end
    return tag, tag:gsub('^v', '');
end

local function parse_manifest(s)
    local m = { files = {} };
    for line in s:gmatch('[^\r\n]+') do
        local v = line:match('^version%s+(%S+)');
        if v then m.version = v; end
        local hash, size, path = line:match('^(%x+)%s+(%d+)%s+(.+)$');
        if hash and #hash == 64 then m.files[#m.files + 1] = { hash = hash:lower(), size = tonumber(size), path = path }; end
    end
    return m;
end

local function mkdirs(path)
    local acc = '';
    for part in path:gmatch('[^\\]+') do
        acc = acc == '' and part or (acc .. '\\' .. part);
        if not acc:match('^%a:$') then ffi.C.CreateDirectoryA(acc, nil); end
    end
end

local function write(path, data)
    local f = io.open(path, 'wb');
    if f == nil then return false; end
    f:write(data);
    f:close();
    return true;
end

--- Download and install `tag` into `target` (the addon folder, with a trailing backslash). Returns a summary or
-- nil, error. Nothing in `target` changes unless every file downloaded and matched the manifest.
function updater.install(tag, target)
    local raw = 'https://raw.githubusercontent.com/' .. updater.REPO .. '/' .. tag .. '/';
    local mtext, err = fetch(raw .. 'manifest.txt');
    if mtext == nil then return nil, err; end
    local man = parse_manifest(mtext);
    if man.version == nil or #man.files == 0 then return nil, 'the release has no usable manifest'; end
    local stage = target:gsub('\\$', '') .. '.update\\';
    local plan = {};
    for _, f in ipairs(man.files) do
        local rel = f.path:gsub('/', '\\');
        if rel:find('%.%.') or rel:match('^[\\/]') or rel:match(':') then return nil, 'bad path in manifest: ' .. f.path; end
        -- unchanged files are skipped
        local cur = io.open(target .. rel, 'rb');
        local same = false;
        if cur then local d = cur:read('*a'); cur:close(); same = (#d == f.size and sha256(d) == f.hash); end
        if not same then
            local data, e = fetch(raw .. 'addons/xiv1ui/' .. f.path);
            if data == nil then return nil, e; end
            if #data ~= f.size or sha256(data) ~= f.hash then return nil, 'checksum mismatch: ' .. f.path; end
            local dst = stage .. rel;
            mkdirs(dst:match('^(.*)\\'));
            if not write(dst, data) then return nil, 'could not write ' .. dst; end
            plan[#plan + 1] = rel;
        end
    end
    -- everything downloaded and matched: move it into place
    local later = {};
    for _, rel in ipairs(plan) do
        mkdirs((target .. rel):match('^(.*)\\'));
        -- MOVEFILE_REPLACE_EXISTING | COPY_ALLOWED; a locked file is left as <file>.new for the next start
        if ffi.C.MoveFileExA(stage .. rel, target .. rel, 0x3) == 0 then
            ffi.C.MoveFileExA(stage .. rel, target .. rel .. '.new', 0x3);
            later[#later + 1] = rel;
        end
    end
    if #later > 0 then write(target .. 'pending-update.txt', table.concat(later, '\n') .. '\n'); end
    return { version = man.version, changed = #plan, later = #later };
end

--- Files left as <file>.new by an earlier update (locked then): swap them in now, before anything uses them.
function updater.finish_pending(target)
    local f = io.open(target .. 'pending-update.txt', 'r');
    if f == nil then return; end
    for rel in f:lines() do
        if rel ~= '' then ffi.C.MoveFileExA(target .. rel .. '.new', target .. rel, 0x1); end
    end
    f:close();
    os.remove(target .. 'pending-update.txt');
end

--- /xiv1ui update [now]
function updater.command(args, target, enabled, current)
    if not enabled then
        say('In-game updates are off. Turn them on in Configuration » Experimental (use at your own risk).');
        return;
    end
    if io.open(target .. 'dev\\eval.lua', 'r') then
        say('This is a development copy of xiv1ui: update it with git instead.');
        return;
    end
    local tag, version = updater.latest();
    if tag == nil then say('Could not check for updates (' .. tostring(version) .. ').'); return; end
    if not newer(version, current) then say('xiv1ui ' .. current .. ' is the latest version.'); return; end
    if (args[3] or ''):lower() ~= 'now' then
        say(string.format('xiv1ui %s is available (you have %s). Type /xiv1ui update now to install it. '
            .. 'Use at your own risk.', version, current));
        return;
    end
    say('Downloading xiv1ui ' .. version .. '... (the game pauses for a few seconds)');
    local r, err = updater.install(tag, target);
    if r == nil then say('Update failed, nothing was changed: ' .. tostring(err)); return; end
    if r.later > 0 then
        say(string.format('Installed %s (%d files). %d file(s) in use are replaced when the game next starts.',
            r.version, r.changed, r.later));
    else
        say(string.format('Installed %s (%d files). Reloading xiv1ui.', r.version, r.changed));
    end
    AshitaCore:GetChatManager():QueueCommand(-1, '/addon reload xiv1ui');
end

updater.newer = newer;

--- Called every frame in the world: once per load, 15 s after the player is in, check for a newer release and say
-- which command installs it (only with in-game updates on). The check pauses the game for a moment, so it waits
-- until loading is long over.
local since, checked = nil, false;
function updater.tick(enabled, current)
    if checked or not enabled then return; end
    since = since or os.clock();
    if os.clock() - since < 15 then return; end
    checked = true;
    local tag, version = updater.latest();
    if tag and newer(version, current) then
        say(string.format('xiv1ui %s is available (you have %s). Type /xiv1ui update now to install it '
            .. '(at your own risk).', version, current));
    end
end

return updater;
