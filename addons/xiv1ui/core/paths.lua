--[[
* xiv1ui - where the game's files are. Installs lay out FFXI differently (HorizonXI: <Ashita>\SquareEnix\FINAL FANTASY
* XI\, CatsEyeXI: catseyexi-client\Game\FINAL FANTASY XI\ beside the Ashita folder), so the FFXI folder is taken from
* where the game loaded FFXiMain.dll, and the Horizon layout is only the fallback.
--]]

local ffi = require('ffi');

pcall(ffi.cdef, [[
void* __stdcall GetModuleHandleA(const char* name);
uint32_t __stdcall GetModuleFileNameA(void* module, char* buffer, uint32_t size);
]]);

local paths = {};

local ffxi = nil;

--- The FFXI folder (with a trailing backslash): the one holding FFXiMain.dll, VTABLE.DAT and the ROM folders.
function paths.ffxi()
    if ffxi then return ffxi; end
    local ok, dir = pcall(function ()
        local buf = ffi.new('char[520]');
        local n = ffi.C.GetModuleFileNameA(ffi.C.GetModuleHandleA('FFXiMain.dll'), buf, 520);
        if n == 0 then return nil; end
        return ffi.string(buf, n):match('^(.*\\)');
    end);
    if ok and dir then
        ffxi = dir;
    else
        ffxi = AshitaCore:GetInstallPath():gsub('[\\/]+$', '') .. '\\SquareEnix\\FINAL FANTASY XI\\';
    end
    return ffxi;
end

--- The Ashita folder (with a trailing backslash).
function paths.install()
    return AshitaCore:GetInstallPath():gsub('[\\/]+$', '') .. '\\';
end

return paths;
