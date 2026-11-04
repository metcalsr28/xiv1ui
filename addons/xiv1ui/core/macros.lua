--[[
* xiv1ui - the player's FFXI macros: read from the game's own macro files and run line by line.
*
* xiv1ui's macro palette replaces the game's (which can't be hidden reliably: its frames and key labels are separate
* drawing objects), so it needs the macros themselves and a way to run them:
*   - USER/<character id in hex>/mcr<N>.dat holds one macro set: a 24-byte header, then 20 macros of 380 bytes
*     (4 unknown, 6 lines of 61 bytes, a 9-byte title, 1 pad). Macros 1-10 are the Ctrl row, 11-20 the Alt row.
*     N = (book - 1) * 10 + (set - 1), and the first file is plain mcr.dat. Book titles are 16-byte entries after a
*     24-byte header in mcr.ttl. Text is Shift-JIS with FFXI's auto-translate codes.
*   - Lines run in order through the chat manager, exactly as if typed; "/wait N" and a trailing "<wait N>" pause.
*     "/macro book N" and "/macro set N" switch xiv1ui's palette (the game's own selection isn't readable).
* The files are re-read each time the palette opens, so edits made in the game's macro editor show up once the game
* has saved them.
--]]

local ffi      = require('ffi');
local encoding = require('gdifonts.encoding');
local xi_now   = require('core.now');
local store    = require('core.store');


local macros = {};

macros.BOOKS = 20;
macros.SETS  = 10;

local user_dir = nil;

local function game_dir() return require('core.paths').ffxi(); end

local function dir()
    local id = AshitaCore:GetMemoryManager():GetParty():GetMemberServerId(0);
    if id == 0 then return nil; end
    if user_dir == nil or user_dir.id ~= id then
        local g = game_dir();
        if g == nil then return nil; end
        user_dir = { id = id, path = string.format('%sUSER\\%x\\', g, id) };
    end
    return user_dir.path;
end

--- Shift-JIS (with auto-translate codes) to UTF-8 for drawing.
function macros.to_utf8(s)
    if s == '' then return s; end
    local ok, parsed = pcall(function () return AshitaCore:GetChatManager():ParseAutoTranslate(s, false); end);
    if ok and type(parsed) == 'string' then s = parsed; end
    return encoding:ShiftJIS_To_UTF8(s, true);
end

-- A NUL-terminated field. (Not s:find('\0', 1, true): once JIT-compiled, that misses the NUL in the game client.)
local function cstr(data, at, len)
    return ffi.string(data:sub(at + 1, at + len));
end

local function read(name)
    local d = dir();
    if d == nil then return nil; end
    local f = io.open(d .. name, 'rb');
    if f == nil then return nil; end
    local data = f:read('*a');
    f:close();
    return data;
end

--- The 20 macros of a set: { title, title_utf8, lines = { ... } } (an empty macro has no lines).
function macros.load(book, set)
    local n = (book - 1) * 10 + (set - 1);
    local data = read(n == 0 and 'mcr.dat' or ('mcr' .. n .. '.dat'));
    local out = {};
    for i = 1, 20 do
        local base = 24 + (i - 1) * 380;
        local m = { title = '', lines = {} };
        if data and #data >= base + 380 then
            for l = 0, 5 do
                local line = cstr(data, base + 4 + l * 61, 61);
                if line:match('%S') then m.lines[#m.lines + 1] = line; end
            end
            m.title = cstr(data, base + 4 + 6 * 61, 9);
        end
        m.title_utf8 = macros.to_utf8(m.title);
        out[i] = m;
    end
    return out;
end

-- MD5 through Windows' CryptoAPI (the macro files' header carries the MD5 of what follows it).
pcall(ffi.cdef, [[
    int CryptAcquireContextA(uintptr_t* prov, const char* container, const char* provider, uint32_t type, uint32_t flags);
    int CryptCreateHash(uintptr_t prov, uint32_t alg, uintptr_t key, uint32_t flags, uintptr_t* hash);
    int CryptHashData(uintptr_t hash, const uint8_t* data, uint32_t len, uint32_t flags);
    int CryptGetHashParam(uintptr_t hash, uint32_t param, uint8_t* data, uint32_t* len, uint32_t flags);
    int CryptDestroyHash(uintptr_t hash);
    int CryptReleaseContext(uintptr_t prov, uint32_t flags);
]]);
local function md5(s)
    local ok, adv = pcall(ffi.load, 'advapi32');
    if not ok then return nil; end
    local prov, hash = ffi.new('uintptr_t[1]'), ffi.new('uintptr_t[1]');
    -- PROV_RSA_FULL = 1, CRYPT_VERIFYCONTEXT = 0xF0000000, CALG_MD5 = 0x8003, HP_HASHVAL = 2
    if adv.CryptAcquireContextA(prov, nil, nil, 1, 0xF0000000) == 0 then return nil; end
    local out = nil;
    if adv.CryptCreateHash(prov[0], 0x8003, 0, 0, hash) ~= 0 then
        local buf = ffi.new('uint8_t[?]', #s);
        ffi.copy(buf, s, #s);
        local digest, len = ffi.new('uint8_t[16]'), ffi.new('uint32_t[1]', 16);
        if adv.CryptHashData(hash[0], buf, #s, 0) ~= 0 and adv.CryptGetHashParam(hash[0], 2, digest, len, 0) ~= 0 then
            out = ffi.string(digest, 16);
        end
        adv.CryptDestroyHash(hash[0]);
    end
    adv.CryptReleaseContext(prov[0], 0);
    return out;
end

local function field(s, len, sjis)
    -- (Shift-JIS, cut to fit with room for the terminating NUL, padded with NULs; `sjis`: already Shift-JIS)
    s = s or '';
    if not sjis then s = encoding:UTF8_To_ShiftJIS(s, true) or ''; end
    if #s > len - 1 then s = s:sub(1, len - 1); end
    return s .. string.rep('\0', len - #s);
end

-- The game keeps the set it has loaded in memory (the 20 macros laid out as in its file, after a 4-byte pointer)
-- and writes that set's file back from there on every zone change and logout, so a set written while it's loaded
-- has to change there too. After the 20 macros: the set within the book x 2 (+4), the file number x 2 (+8) and the
-- book from 0 (+12). The object's pointer is stored where the game makes it at start-up.
local loaded_ptr = nil;
local function loaded_set()
    if loaded_ptr == nil then
        loaded_ptr = ashita.memory.find('FFXiMain.dll', 0, '53E8????????6A24A3????????E8', 9, 0) or 0;
        if loaded_ptr ~= 0 then loaded_ptr = ashita.memory.read_uint32(loaded_ptr); end
    end
    if loaded_ptr == 0 then return nil; end
    local obj = ashita.memory.read_uint32(loaded_ptr);
    if obj == nil or obj == 0 then return nil; end
    local tail = obj + 4 + 20 * 380;
    local n2, book = ashita.memory.read_uint32(tail + 8), ashita.memory.read_uint32(tail + 12);
    if n2 == nil or n2 % 2 ~= 0 or n2 / 2 >= 400 or book ~= math.floor(n2 / 20) then return nil; end
    return obj + 4, n2 / 2;
end

--- Write macros into a set's file. `changes` is { [1..20] = { title = utf8, lines = { ... }, sjis } } (lines in
-- UTF-8, or Shift-JIS as the game wrote them if sjis is set: those came from its files): only those
-- macros change, the rest stay as they are. The file as it was goes to `backup_dir` first (once per call site, if
-- given). Returns true, or nil and why.
function macros.save(book, set, changes, backup_dir)
    local d = dir();
    if d == nil then return nil, 'no character'; end
    local n = (book - 1) * 10 + (set - 1);
    local name = n == 0 and 'mcr.dat' or ('mcr' .. n .. '.dat');
    local old = read(name);
    if old and backup_dir then
        local f = io.open(backup_dir .. name, 'rb');
        if f then f:close();                                          -- (backed up already this time)
        else
            f = io.open(backup_dir .. name, 'wb');
            if f == nil then return nil, 'could not write the backup'; end
            f:write(old);
            f:close();
        end
    end
    if old == nil and next(changes) == nil then return true; end      -- (no file and nothing to put in one)
    if old == nil or #old < 24 + 20 * 380 then old = string.rep('\0', 24 + 20 * 380); end
    local body = {};
    for i = 1, 20 do
        local base = 24 + (i - 1) * 380;
        local c = changes[i];
        if c == nil then
            body[i] = old:sub(base + 1, base + 380);
        else
            local lines = {};
            for l = 1, 6 do lines[l] = field(c.lines[l] or '', 61, c.sjis); end
            body[i] = old:sub(base + 1, base + 4) .. table.concat(lines) .. field(c.title or '', 9) .. '\0';
        end
    end
    local data = table.concat(body);
    local sum = md5(data);
    if sum == nil then return nil, 'no MD5'; end
    local f = io.open(d .. name, 'wb');
    if f == nil then return nil, 'could not write ' .. name; end
    -- (bytes 4-7 of the header aren't known: the game's own value stays)
    f:write('\1\0\0\0' .. old:sub(5, 8) .. sum .. data);
    f:close();
    -- (read back: the file must be what was meant)
    local back = read(name);
    if back == nil or #back ~= 24 + #data or back:sub(25) ~= data then return nil, name .. ' did not read back'; end
    local at, loaded = loaded_set();
    if at and loaded == n then ffi.copy(ffi.cast('void*', at), data, #data); end
    return true;
end

function macros.book_title(book)
    local data = read(book <= 20 and 'mcr.ttl' or 'mcr_2.ttl');
    local at = 24 + ((book - 1) % 20) * 16;
    if data == nil or #data < at + 16 then return string.format('Book%02d', book); end
    local t = cstr(data, at, 16);
    return t ~= '' and macros.to_utf8(t) or string.format('Book%02d', book);
end

-- Current book/set (xiv1ui's settings are per character).
function macros.current()
    local s = store.data.macro;
    return s.book, s.set;
end

function macros.select(book, set)
    local s = store.data.macro;
    s.book = ((book - 1) % macros.BOOKS) + 1;
    s.set  = ((set - 1) % macros.SETS) + 1;
    store.save();
end

-- Running macro: { lines, i, wake, title }.
local running = nil;
macros.on_switch = nil;     -- called after a /macro book|set line (so the palette reloads)

--- "/macro book N" / "/macro set N": returns true if the line was one of these.
function macros.switch_command(line)
    local what, n = line:lower():match('^/macro%s+(%a+)%s+(%d+)');
    n = tonumber(n);
    if n == nil then return false; end
    local b, s = macros.current();
    if what == 'book' then macros.select(n, s);
    elseif what == 'set' then macros.select(b, n);
    else return false; end
    if macros.on_switch then macros.on_switch(); end
    return true;
end

function macros.run(m)
    if m == nil or #m.lines == 0 then return; end
    running = { lines = m.lines, i = 1, wake = 0, title = m.title_utf8 };
end

function macros.running() return running; end

--- Called every frame: runs lines until the next wait.
function macros.tick()
    local r = running;
    if r == nil or xi_now() < r.wake then return; end
    local cm = AshitaCore:GetChatManager();
    while r.i <= #r.lines do
        local line = r.lines[r.i];
        r.i = r.i + 1;
        local w = line:lower():match('^/wait%s*(%d*%.?%d*)%s*$');
        if w then
            r.wake = xi_now() + math.min(tonumber(w) or 1, 60);
            return;
        end
        local body, tail = line:match('^(.-)%s*<wait%s*(%d*%.?%d*)>%s*$');
        if body then line = body; end
        if not macros.switch_command(line) then cm:QueueCommand(1, line); end
        if body then
            r.wake = xi_now() + math.min(tonumber(tail) or 1, 60);
            return;
        end
    end
    running = nil;
end

return macros;
