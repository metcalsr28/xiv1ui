--[[
* xiv1ui - Actions & Traits window (reference §22): everything you can put on the action bar, by category
* (Abilities / Weapon Skills / Magic / Commands), with the selected action's details. Enter (or click) an action,
* then press 1–0 or click an action-bar slot to place it there. ←/→ (or Tab) switch categories.
--]]

local ui      = require('core.ui');
local draw    = require('core.draw');
local text    = require('core.text');
local actions = require('core.actions');

local M = {};

local TABS = { 'Abilities', 'Weapon Skills', 'Magic', 'Commands' };
local COMMANDS = {
    { kind = 'cmd', name = 'Attack',     command = '/attack <t>' },
    { kind = 'cmd', name = 'Disengage',  command = '/attack off' },
    { kind = 'cmd', name = 'Check',      command = '/check <t>' },
    { kind = 'cmd', name = 'Heal',       command = '/heal' },
    { kind = 'cmd', name = 'Lock On',    command = '/lockon' },
    { kind = 'cmd', name = 'Follow',     command = '/follow <t>' },
    { kind = 'cmd', name = 'Assist',     command = '/assist <t>' },
    { kind = 'cmd', name = 'Ranged',     command = '/ra <t>' },
    { kind = 'cmd', name = 'Main Menu',  command = '/xiv1ui menu' },
    { kind = 'cmd', name = 'Next Bar',   command = '/xiv1ui page next' },
};

local ROWS = 14;
local win = { id = 'actions', title = 'Actions & Traits', w = 560, h = 470, tab = 1, sel = 1, first = 0, rows = {}, tabs = {} };

local function gather(tab)
    local out = {};
    local player = AshitaCore:GetMemoryManager():GetPlayer();
    local r = AshitaCore:GetResourceManager();
    if tab == 1 then
        for id = 512, 1023 do
            local a = r:GetAbilityById(id);
            if a and player:HasAbility(id) and a.Name[1] ~= '' then out[#out + 1] = { kind = 'ja', name = a.Name[1] }; end
        end
    elseif tab == 2 then
        for id = 1, 255 do
            local a = r:GetAbilityById(id);
            if a and player:HasWeaponSkill(id) and a.Name[1] ~= '' then out[#out + 1] = { kind = 'ws', name = a.Name[1] }; end
        end
    elseif tab == 3 then
        local job, lvl = player:GetMainJob(), player:GetMainJobLevel();
        local sub, slvl = player:GetSubJob(), player:GetSubJobLevel();
        for id = 1, 1023 do
            local s = r:GetSpellById(id);
            if s and s.Name[1] ~= '' and player:HasSpell(s.Index) then
                local need = s.LevelRequired and s.LevelRequired[job + 1];
                local need2 = s.LevelRequired and s.LevelRequired[sub + 1];
                if (need and need ~= 255 and need > 0 and need <= lvl) or (need2 and need2 ~= 255 and need2 > 0 and need2 <= slvl) then
                    out[#out + 1] = { kind = 'ma', name = s.Name[1] };
                end
            end
        end
    else
        for _, c in ipairs(COMMANDS) do out[#out + 1] = c; end
    end
    return out;
end

local function refresh(w)
    w.items = gather(w.tab);
    w.sel = math.max(1, math.min(w.sel, #w.items));
    w.first = 0;
end

win.on_open = function (w) refresh(w); end

win.draw = function (w, x, y)
    -- category tabs
    w.tabs = {};
    local tx = x + 20;
    for i, t in ipairs(TABS) do
        local bw = 120;
        w.tabs[i] = ui.button('acttab' .. i, t, tx, y + 44, bw, i == w.tab);
        tx = tx + bw + 8;
    end
    -- list (left) and details (right)
    local items = {};
    for i, b in ipairs(w.items or {}) do
        local info = actions.resolve(b);
        items[i] = { label = b.name, right = info and info.cost and (info.cost .. ' ' .. info.cost_kind) or nil };
    end
    if #items == 0 then items[1] = { label = '(nothing yet)', disabled = true }; end
    if w.sel > w.first + ROWS then w.first = w.sel - ROWS; end
    if w.sel <= w.first then w.first = w.sel - 1; end
    w.rows = ui.list(w, 'act', items, w.sel, x + 40, y + 84, 270, 26, ROWS, w.first, ui.top() == w);

    local b = (w.items or {})[w.sel];
    if b then
        local info = actions.resolve(b);
        local dx = x + 330;
        ui.header('actdet', 'Details', dx, y + 102, 200);
        if info then
            draw.image('slot_shadow', dx + 70, y + 116);
            draw.image('slot_well', dx + 78, y + 124);
            draw.image(info.disc, dx + 78, y + 124);
            if info.icon then
                draw.image(info.icon, dx + 78, y + 124);
            else
                local g = ui.label('actglyph', 'name', { font_height = 26, font_alignment = text.align.Center });
                text.draw(g, info.glyph, dx + 100, y + 156, 'baseline');
            end
            draw.image('slot_ring', dx + 70, y + 116);
            local lines = { b.name, info.kind_label or '' };
            if info.cast then lines[#lines + 1] = string.format('Cast: %g s   Recast: %g s', info.cast, info.recast); end
            if info.cost then lines[#lines + 1] = string.format('%s Cost: %d', info.cost_kind, info.cost); end
            lines[#lines + 1] = info.command or '';
            for n, l in ipairs(lines) do
                local o = ui.label('actdet' .. n, n == 1 and 'name' or 'small', { font_height = n == 1 and 20 or 15,
                    font_color = n == 1 and 0xFFFFFFFF or (n == #lines and 0xFFA8B4D8 or 0xFFF0DCA0) });
                text.draw(o, l, dx, y + 210 + (n - 1) * 24, 'baseline');
            end
        end
        local hint = ui.label('acthint', 'small', { font_height = 15, font_color = 0xFFB8C0D8 });
        text.draw(hint, 'Enter / click: place on the action bar', dx, y + w.h - 24, 'baseline');
    end
end

local function choose(w)
    local b = (w.items or {})[w.sel];
    if not b then return; end
    local copy = {};
    for k, v in pairs(b) do copy[k] = v; end
    require('ui.hotbar').begin_assign(copy);
    ui.close(w.id);
    ui.close('mainmenu');
end

win.key = function (w, vk)
    local n = #(w.items or {});
    if vk == ui.VK.UP then w.sel = math.max(1, w.sel - 1);
    elseif vk == ui.VK.DOWN then w.sel = math.min(math.max(1, n), w.sel + 1);
    elseif vk == ui.VK.PRIOR then w.sel = math.max(1, w.sel - ROWS);
    elseif vk == ui.VK.NEXT then w.sel = math.min(math.max(1, n), w.sel + ROWS);
    elseif vk == ui.VK.LEFT then w.tab = (w.tab - 2) % #TABS + 1; refresh(w);
    elseif vk == ui.VK.RIGHT or vk == ui.VK.TAB then w.tab = w.tab % #TABS + 1; refresh(w);
    elseif vk == ui.VK.RETURN then choose(w);
    elseif vk == ui.VK.ESCAPE then return false; end
    return true;
end

win.click = function (w, mx, my)
    for i, r in ipairs(w.tabs) do
        if ui.hit(r, mx, my) then w.tab = i; refresh(w); return; end
    end
    for _, r in ipairs(w.rows) do
        if ui.hit(r, mx, my) then
            if w.sel == r[5] then choose(w); else w.sel = r[5]; end
            return;
        end
    end
end

win.wheel = function (w, delta)
    w.sel = math.max(1, math.min(#(w.items or {}), w.sel + (delta > 0 and -3 or 3)));
end

function M.open() ui.open(win); end

return M;
