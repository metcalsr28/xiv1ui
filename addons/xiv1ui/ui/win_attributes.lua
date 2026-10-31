--[[
* xiv1ui - Attributes window (reference §20): tabs General / Jobs / Skills. General shows name, race, nation,
* title and rank, base stats and elemental resistances; Jobs lists every job's level with the current job in green
* (1.0's class rows); Skills lists combat skill levels.
--]]

local ui   = require('core.ui');
local text = require('core.text');

local M = {};

local TABS = { 'General', 'Jobs', 'Skills' };
local STAT_NAMES = { 'STR', 'DEX', 'VIT', 'AGI', 'INT', 'MND', 'CHR' };
local ELEMENTS = { 'Fire', 'Ice', 'Wind', 'Earth', 'Lightning', 'Water', 'Light', 'Dark' };
local NATIONS = { [0] = 'San d\'Oria', 'Bastok', 'Windurst' };
local SKILLS = {
    [1] = 'Hand-to-Hand', 'Dagger', 'Sword', 'Great Sword', 'Axe', 'Great Axe', 'Scythe', 'Polearm', 'Katana',
    'Great Katana', 'Club', 'Staff', [25] = 'Archery', [26] = 'Marksmanship', [27] = 'Throwing', [28] = 'Guard',
    [29] = 'Evasion', [30] = 'Shield', [31] = 'Parrying', [32] = 'Divine Magic', [33] = 'Healing Magic',
    [34] = 'Enhancing Magic', [35] = 'Enfeebling Magic', [36] = 'Elemental Magic', [37] = 'Dark Magic',
    [38] = 'Summoning Magic', [39] = 'Ninjutsu', [40] = 'Singing', [41] = 'String Instrument',
    [42] = 'Wind Instrument', [43] = 'Blue Magic',
};

local win = { id = 'attributes', title = 'Attributes', w = 600, h = 470, tab = 1, tabs = {} };

local function row(key, label, value, x, y, color)
    local o = ui.label('at' .. key, 'small', { font_height = 16, font_color = color or 0xFFE8E4D8 });
    text.draw(o, label, x, y, 'baseline');
    local v = ui.label('atv' .. key, 'small', { font_height = 16, font_alignment = text.align.Right, font_color = color or 0xFFF4F0E6 });
    text.draw(v, tostring(value), x + 200, y, 'baseline');
end

win.draw = function (w, x, y)
    w.tabs = {};
    local tx = x + 24;
    for i, t in ipairs(TABS) do
        w.tabs[i] = ui.button('attab' .. i, t, tx, y + 44, 120, i == w.tab);
        tx = tx + 128;
    end
    local mm = AshitaCore:GetMemoryManager();
    local p = mm:GetPlayer();
    local r = AshitaCore:GetResourceManager();

    if w.tab == 1 then
        local name = mm:GetParty():GetMemberName(0);
        ui.header('atgen', name, x + 30, y + 104, 240);
        local ly = y + 132;
        row('nat', 'Nation', NATIONS[p:GetNation()] or '?', x + 40, ly); ly = ly + 22;
        row('rank', 'Rank', p:GetRank() or 0, x + 40, ly); ly = ly + 22;
        local title = r:GetString('titles', p:GetTitle()) or '';
        row('title', 'Title', title ~= '' and title or '—', x + 40, ly); ly = ly + 30;
        for i, n in ipairs(STAT_NAMES) do
            local base, mod = p:GetStat(i - 1) or 0, p:GetStatModifier(i - 1) or 0;
            row('st' .. i, n, mod ~= 0 and string.format('%d  +%d', base, mod) or base, x + 40, ly);
            ly = ly + 22;
        end
        ui.header('atel', 'Elements', x + 320, y + 104, 240);
        for i, n in ipairs(ELEMENTS) do
            row('el' .. i, n, p:GetResist(i - 1) or 0, x + 330, y + 132 + (i - 1) * 22);
        end
        row('atk', 'Attack', p:GetAttack() or 0, x + 330, y + 132 + 8 * 22 + 8, 0xFFF0DCA0);
        row('def', 'Defense', p:GetDefense() or 0, x + 330, y + 132 + 9 * 22 + 8, 0xFFF0DCA0);
    elseif w.tab == 2 then
        ui.header('atjobs', 'Jobs', x + 30, y + 104, 520);
        local main = p:GetMainJob();
        for j = 1, 22 do
            local nm = r:GetString('jobs.names', j) or ('Job ' .. j);
            local lvl = p:GetJobLevel(j) or 0;
            local col = (j == main) and 0xFF9BE08C or (lvl > 0 and 0xFFF4F0E6 or 0xFF80848C);
            local c, rr = math.floor((j - 1) / 11), (j - 1) % 11;
            row('job' .. j, nm, lvl > 0 and ('Level ' .. lvl) or '—', x + 40 + c * 270, y + 132 + rr * 24, col);
        end
    else
        ui.header('atskills', 'Combat & Magic Skills', x + 30, y + 104, 520);
        local n = 0;
        for id, nm in pairs(SKILLS) do
            local s = p:GetCombatSkill(id);
            local v = s and (type(s) == 'table' or type(s) == 'cdata') and (s.Skill or s.GetSkill and s:GetSkill()) or s;
            if type(v) == 'number' and v > 0 then
                local c, rr = math.floor(n / 11), n % 11;
                row('sk' .. id, nm, v, x + 40 + c * 270, y + 132 + rr * 24);
                n = n + 1;
            end
        end
        if n == 0 then
            local o = ui.label('atnosk', 'small', { font_height = 16, font_color = 0xFF9AA4C4 });
            text.draw(o, 'No skills yet.', x + 40, y + 140, 'baseline');
        end
    end
end

win.key = function (w, vk)
    if vk == ui.VK.LEFT then w.tab = (w.tab - 2) % #TABS + 1;
    elseif vk == ui.VK.RIGHT or vk == ui.VK.TAB then w.tab = w.tab % #TABS + 1;
    elseif vk == ui.VK.ESCAPE then return false; end
    return true;
end

win.click = function (w, mx, my)
    for i, r in ipairs(w.tabs) do if ui.hit(r, mx, my) then w.tab = i; return; end end
end

function M.open() ui.open(win); end

return M;
