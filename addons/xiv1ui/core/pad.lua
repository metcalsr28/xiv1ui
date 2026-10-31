--[[
* xiv1ui - controller support, after FFXIV 1.0's "anchor cursor" pad model (reference §36): no virtual mouse;
* the D-pad moves a cursor, A confirms, B cancels, the shoulder buttons switch tabs.
*
*   With an xiv1ui window open:  D-pad = arrows, A = Enter, B = Esc, LB/RB = previous/next tab.
*                                (these buttons are kept from the game only while a window is open)
*   Hold Back + X:               Main Menu.
*   Hold Back + A:               action-bar cursor: D-pad ←/→ choose a slot, ↑/↓ change bar, A fires, B leaves.
*
* XInput button ids are bit positions: 0-3 D-pad up/down/left/right, 4 Start, 5 Back, 8/9 LB/RB, 12-15 A/B/X/Y.
* On unless Configuration » "Controller drives xiv1ui" is turned off (store.data.pad == false).
--]]

local ui    = require('core.ui');
local store = require('core.store');

local pad = {};

local B = { UP = 0, DOWN = 1, LEFT = 2, RIGHT = 3, START = 4, BACK = 5, LB = 8, RB = 9, A = 12, B = 13, X = 14, Y = 15 };
pad.B = B;

local held = {};
pad.bar_cursor = nil;        -- slot index while the action-bar cursor is active

local function key(vk)
    local win = ui.top();
    if vk == ui.VK.ESCAPE then
        if not (win and win.key and win.key(win, vk)) and win then ui.close(win.id); end
    elseif win and win.key then
        win.key(win, vk);
    end
end

--- xinput_button handler; returns true when the button should be kept from the game.
function pad.button(e)
    if store.data.pad == false then return false; end
    local b, down = e.button, (e.state or 0) ~= 0;
    local was = held[b];
    held[b] = down;
    local press = down and not was;

    -- chords on Back: never block Back itself, only the face button pressed with it
    if held[B.BACK] and b ~= B.BACK then
        if press and b == B.X then require('ui.mainmenu').toggle(); end
        if press and b == B.A then pad.bar_cursor = pad.bar_cursor or 1; end
        return true;
    end

    -- placing an action / macro on the bar: D-pad Left/Right choose the slot, A places it, B cancels
    local hb0 = require('ui.hotbar');
    if hb0.assigning() then
        pad.assign_cursor = pad.assign_cursor or 1;
        if press then
            if b == B.LEFT then pad.assign_cursor = (pad.assign_cursor - 2) % 10 + 1;
            elseif b == B.RIGHT then pad.assign_cursor = pad.assign_cursor % 10 + 1;
            elseif b == B.A then hb0.use(pad.assign_cursor); pad.assign_cursor = nil;
            elseif b == B.B then hb0.cancel_assign(); pad.assign_cursor = nil; end
        end
        if b == B.LEFT or b == B.RIGHT or b == B.UP or b == B.DOWN or b == B.A or b == B.B then return true; end
        return false;
    end
    pad.assign_cursor = nil;

    -- action-bar cursor
    if pad.bar_cursor then
        local hb = require('ui.hotbar');
        if press then
            if b == B.LEFT then pad.bar_cursor = (pad.bar_cursor - 2) % 10 + 1;
            elseif b == B.RIGHT then pad.bar_cursor = pad.bar_cursor % 10 + 1;
            elseif b == B.UP then AshitaCore:GetChatManager():QueueCommand(-1, '/xiv1ui page prev');
            elseif b == B.DOWN then AshitaCore:GetChatManager():QueueCommand(-1, '/xiv1ui page next');
            elseif b == B.A then hb.use(pad.bar_cursor);
            elseif b == B.B then pad.bar_cursor = nil; end
        end
        if b == B.LEFT or b == B.RIGHT or b == B.UP or b == B.DOWN or b == B.A or b == B.B then return true; end
        return false;
    end

    -- windows
    if ui.any_open() then
        if press then
            if b == B.UP then key(ui.VK.UP);
            elseif b == B.DOWN then key(ui.VK.DOWN);
            elseif b == B.LEFT then key(ui.VK.LEFT);
            elseif b == B.RIGHT then key(ui.VK.RIGHT);
            elseif b == B.A then key(ui.VK.RETURN);
            elseif b == B.B then key(ui.VK.ESCAPE);
            elseif b == B.LB then key(ui.VK.LEFT);
            elseif b == B.RB then key(ui.VK.TAB); end
        end
        if b == B.UP or b == B.DOWN or b == B.LEFT or b == B.RIGHT or b == B.A or b == B.B or b == B.LB or b == B.RB then
            return true;
        end
    end
    return false;
end

return pad;
