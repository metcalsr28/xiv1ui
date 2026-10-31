--[[
* xiv1ui - wall-clock seconds for animations and timers. (os.clock() is process CPU time, which in the game runs
* faster than real time because several threads are busy, so it can't be used for anything visible.)
--]]

local ffi = require('ffi');
pcall(ffi.cdef, 'uint64_t __stdcall GetTickCount64(void);');
local k32 = ffi.load('kernel32');

return function ()
    return tonumber(k32.GetTickCount64()) / 1000;
end
