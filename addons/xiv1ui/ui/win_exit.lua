--[[
* xiv1ui - Exit Game (reference §18, entry 19): "Exit Game / Return to character screen / Cancel".
* Uses the game's own /shutdown and /logout, which keep FFXI's normal 30-second countdown.
--]]

local ui = require('core.ui');

local M = {};

local CHOICES = {
    { label = 'Exit Game',                   cmd = '/shutdown' },
    { label = 'Return to character screen',  cmd = '/logout' },
    { label = 'Cancel' },
};

local win = { id = 'exit', title = 'Exit Game', w = 360, h = 70 + #CHOICES * 30 + 20, sel = 3, rows = {} };

win.draw = function (w, x, y)
    local items = {};
    for i, c in ipairs(CHOICES) do items[i] = { label = c.label }; end
    w.rows = ui.list(w, 'exit', items, w.sel, x + 40, y + 52, w.w - 70, 30, #items, 0, ui.top() == w);
end

local function choose(i)
    local c = CHOICES[i];
    ui.close(win.id);
    if c and c.cmd then
        ui.close('mainmenu');
        AshitaCore:GetChatManager():QueueCommand(1, c.cmd);
    end
end

win.key = function (w, vk)
    if vk == ui.VK.UP then w.sel = (w.sel - 2) % #CHOICES + 1;
    elseif vk == ui.VK.DOWN then w.sel = w.sel % #CHOICES + 1;
    elseif vk == ui.VK.RETURN then choose(w.sel);
    elseif vk == ui.VK.ESCAPE then return false; end
    return true;
end

win.click = function (w, mx, my)
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then choose(r[5]); return; end
    end
end

function M.open() ui.open(win); end

return M;
