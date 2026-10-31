--[[
* xiv1ui - between areas. While the game loads a zone it writes "Downloading data..." into its help bar (windows
* helpwind and titlewin, with the Network box, netstat, beside them), first over a black screen and then across the
* top of the new area while it fills in. xiv1ui hides that bar whenever no game menu is open (it then only carries
* status text) and draws its own small "Now Loading..." at the bottom right while an area loads, as its lobby
* loading screen does (reference §43.6). It runs before the HUD can draw (no player entity yet).
--]]

local gamewin = require('core.gamewin');

local zoning = {};
local hider = gamewin.new();

-- The zone change: the game's zoning flag is set for the first few seconds; the area keeps loading for a few more
-- after it clears (the text isn't kept anywhere xiv1ui can read), so the mark stays up 5 s longer.
local last_zoning = -100;
local function now() return os.clock(); end

--- True while an area is loading (the zoning flag, and a few seconds after).
function zoning.active()
    local p = AshitaCore:GetMemoryManager():GetPlayer();
    if p and p:GetIsZoning() ~= 0 and not require('ui.lobby').active() then last_zoning = now(); end
    return now() - last_zoning < 5;
end

-- The help bar only carries status text ("Downloading data...", "K.O.") while no game menu is open; menus keep it
-- (xiv1ui's restyled menus hide it themselves and draw their own help). Hidden at scene start so it never shows for
-- a frame. The Network box is hidden here too, since the HUD (and core/native.lua with it) isn't running yet.
function zoning.early()
    -- (not in the lobby, which has its own screens; the login status isn't "in the world" in the middle of a zone)
    local in_world = not require('ui.lobby').active();
    local _, focus = require('core.native').focused();
    if in_world and focus == nil and require('core.store').data.hide_native ~= false then
        hider:hide({ 'helpwind', 'titlewin', 'netstat' });
        -- over the black screen at the start of a zone change the text comes from another window (chdummy)
        if zoning.active() then hider:hide({ 'chdummy' }); end
    elseif hider:active() then
        hider:restore();
    end
end

function zoning.release() hider:restore(); end

return zoning;
