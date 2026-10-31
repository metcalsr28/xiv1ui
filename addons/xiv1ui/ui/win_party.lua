--[[
* xiv1ui - Party window (Main Menu » Party, reference §27): members with job, level and area; Enter on a member
* opens commands (Target, Send Tell, Give Leadership, Remove from Party) and the footer has Invite Target, Leave
* Party and Disband. Everything goes through the game's own /pcmd and chat commands.
--]]

local ui   = require('core.ui');
local text = require('core.text');

local M = {};

local win = { id = 'partywin', title = 'Party', w = 560, h = 380, sel = 1, rows = {}, btns = {} };

local function members()
    local p = AshitaCore:GetMemoryManager():GetParty();
    local r = AshitaCore:GetResourceManager();
    local out = {};
    for i = 0, 5 do
        if p:GetMemberIsActive(i) == 1 and p:GetMemberName(i) ~= '' then
            local job = r:GetString('jobs.names_abbr', p:GetMemberMainJob(i)) or '';
            local zone = r:GetString('zones.names', p:GetMemberZone(i)) or '';
            out[#out + 1] = { slot = i, name = p:GetMemberName(i), job = job, lvl = p:GetMemberMainJobLevel(i), zone = zone };
        end
    end
    return out, p;
end

local function is_leader()
    local p = AshitaCore:GetMemoryManager():GetParty();
    local lead = p:GetAlliancePartyLeaderServerId1();
    return lead ~= 0 and lead == p:GetMemberServerId(0);
end

local function cmd(c) AshitaCore:GetChatManager():QueueCommand(1, c); end

local function member_actions(m)
    local list = { { label = 'Target', run = function () cmd(string.format('/ta <p%d>', m.slot)); end } };
    if m.slot ~= 0 then
        list[#list + 1] = { label = 'Send Tell', run = function ()
            AshitaCore:GetChatManager():SetInputText('/tell ' .. m.name .. ' ');
        end };
        if is_leader() then
            list[#list + 1] = { label = 'Give Leadership', run = function () cmd('/pcmd leader ' .. m.name); end };
            list[#list + 1] = { label = 'Remove from Party', run = function () cmd('/pcmd kick ' .. m.name); end };
        end
    end
    list[#list + 1] = { label = 'Close', run = function () end };
    return list;
end

win.draw = function (w, x, y)
    local list = members();
    w.list = list;
    ui.header('pty', (#list >= 6 and 'Full Party') or (#list >= 2 and 'Light Party') or 'No Party', x + 30, y + 64, 480);
    local items = {};
    for i, m in ipairs(list) do
        items[i] = { label = string.format('%s', m.name), right = string.format('%s %d   %s', m.job, m.lvl, m.zone),
                     color = i == 1 and 0xFFF4E070 or nil };
    end
    w.rows = ui.list(w, 'pty', items, w.sel, x + 40, y + 78, w.w - 70, 28, 6, 0, ui.top() == w and not w.popup);

    w.btns = {};
    local bx = x + 30;
    for i, b in ipairs({ { 'Invite Target', '/pcmd add <t>' }, { 'Leave Party', '/pcmd leave' },
                         is_leader() and { 'Disband', '/pcmd breakup' } or nil }) do
        if b then
            w.btns[#w.btns + 1] = { rect = ui.button('pty' .. i, b[1], bx, y + w.h - 46, 150, false), cmd = b[2] };
            bx = bx + 166;
        end
    end

    if w.popup then
        local p = w.popup;
        local px, py = x + 260, y + 78 + (w.sel - 1) * 28;
        local cw, ch = require('core.layout').size('win_body');
        require('core.draw').nine('win_body', px, py, 210, 18 + #p.items * 26, 12, cw, ch);
        p.rows = ui.list(w, 'ptypop', p.items, p.sel, px + 22, py + 8, 170, 26, #p.items, 0, true);
    end
end

local function open_popup(w)
    local m = (w.list or {})[w.sel];
    if m then w.popup = { sel = 1, items = member_actions(m) }; end
end

win.key = function (w, vk)
    if w.popup then
        local p = w.popup;
        if vk == ui.VK.UP then p.sel = (p.sel - 2) % #p.items + 1;
        elseif vk == ui.VK.DOWN then p.sel = p.sel % #p.items + 1;
        elseif vk == ui.VK.RETURN then p.items[p.sel].run(); w.popup = nil;
        elseif vk == ui.VK.ESCAPE then w.popup = nil; end
        return true;
    end
    local n = #(w.list or {});
    if vk == ui.VK.UP then w.sel = math.max(1, w.sel - 1);
    elseif vk == ui.VK.DOWN then w.sel = math.min(math.max(1, n), w.sel + 1);
    elseif vk == ui.VK.RETURN then open_popup(w);
    elseif vk == ui.VK.ESCAPE then return false; end
    return true;
end

win.click = function (w, mx, my)
    if w.popup and w.popup.rows then
        for _, r in ipairs(w.popup.rows) do
            if ui.hit(r, mx, my) then w.popup.items[r[5]].run(); w.popup = nil; return; end
        end
        w.popup = nil;
        return;
    end
    for _, b in ipairs(w.btns) do
        if ui.hit(b.rect, mx, my) then cmd(b.cmd); return; end
    end
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then w.sel = r[5]; open_popup(w); return; end
    end
end

function M.open() ui.open(win); end

return M;
