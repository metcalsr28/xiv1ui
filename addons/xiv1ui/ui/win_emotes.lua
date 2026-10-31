--[[
* xiv1ui - Emotes window (reference §28, "Emotes & Signs"): FFXI's emotes in a list; Enter or click performs one
* (on your target if you have one, as the game's own emote commands do).
--]]

local ui = require('core.ui');

local M = {};

local EMOTES = {
    'wave', 'bow', 'salute', 'kneel', 'laugh', 'cry', 'no', 'yes', 'joy', 'cheer', 'clap', 'praise', 'smile',
    'poke', 'slap', 'stagger', 'sigh', 'comfort', 'surprised', 'amazed', 'stare', 'blush', 'angry', 'disgusted',
    'muted', 'doze', 'panic', 'grin', 'dance', 'think', 'fume', 'doubt', 'sulk', 'psych', 'huh', 'shocked',
    'hurray', 'goodbye', 'welcome', 'point', 'nod', 'toss', 'aim', 'bell', 'upset', 'dance1', 'dance2', 'dance3',
    'dance4', 'jobemote',
};
table.sort(EMOTES);

local ROWS = 14;
local win = { id = 'emotes', title = 'Emotes & Signs', w = 300, h = 70 + ROWS * 26 + 10, sel = 1, first = 0, rows = {} };

win.draw = function (w, x, y)
    local items = {};
    for i, e in ipairs(EMOTES) do items[i] = { label = e:sub(1, 1):upper() .. e:sub(2), right = '/' .. e }; end
    if w.sel > w.first + ROWS then w.first = w.sel - ROWS; end
    if w.sel <= w.first then w.first = w.sel - 1; end
    w.rows = ui.list(w, 'emo', items, w.sel, x + 40, y + 48, w.w - 70, 26, ROWS, w.first, ui.top() == w);
end

local function perform(i)
    AshitaCore:GetChatManager():QueueCommand(1, '/' .. EMOTES[i] .. ' motion');
end

win.key = function (w, vk)
    if vk == ui.VK.UP then w.sel = math.max(1, w.sel - 1);
    elseif vk == ui.VK.DOWN then w.sel = math.min(#EMOTES, w.sel + 1);
    elseif vk == ui.VK.PRIOR then w.sel = math.max(1, w.sel - ROWS);
    elseif vk == ui.VK.NEXT then w.sel = math.min(#EMOTES, w.sel + ROWS);
    elseif vk == ui.VK.RETURN then perform(w.sel);
    elseif vk == ui.VK.ESCAPE then return false; end
    return true;
end

win.click = function (w, mx, my)
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then w.sel = r[5]; perform(r[5]); return; end
    end
end

win.wheel = function (w, delta) w.sel = math.max(1, math.min(#EMOTES, w.sel + (delta > 0 and -3 or 3))); end

function M.open() ui.open(win); end

return M;
