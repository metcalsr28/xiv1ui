--[[
* xiv1ui - EXP bar (bottom centre, under the HP/MP/TP row), after FFXIV 1.0 (reference §8):
* a square class tile, "Warrior Level: 75" (with the support job after it), a long thin light-blue gauge, and
* "Next 1234/5000" in gold italic at the right. With limit mode on it shows limit points and merits instead.
*
* Under it, slim bars for what a level 99 character earns (each one switched in Configuration » HUD, and drawn only
* when it means something for this character): Capacity Points toward the next Job Point, Exemplar Points toward
* the next Master Level, and (off by default) Limit Points toward the next merit. The HP/MP/TP row and the action
* bar move up by expbar.lift() to make room.
--]]

local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local store  = require('core.store');

local expbar = {};

local job_obj, abbr_obj, next_lbl, next_val;
local row_objs = {};
local ROW_H = 13;                   -- each slim bar row (track and its label)
local rows_cache, rows_at = {}, -1;
local drawn_lift, drawn_at = 0, -10;

function expbar.init()
    job_obj  = text.new('label', { font_height = 16, font_color = 0xFFF4F0E6 });
    abbr_obj = text.new('slotkey', { fixed = true, font_height = 13, font_color = 0xFFF8E6A8, font_alignment = text.align.Center });
    next_lbl = text.new('label', { font_height = 16, font_color = 0xFFF0C860 });
    next_val = text.new('label', { font_height = 16, font_color = 0xFFF4F0E6, font_alignment = text.align.Right });
end

local function job_name(id)
    local s = AshitaCore:GetResourceManager():GetString('jobs.names', id);
    return (s and s ~= '') and s or ('Job ' .. id);
end

local function job_abbr(id)
    local s = AshitaCore:GetResourceManager():GetString('jobs.names_abbr', id);
    return (s and s ~= '') and s or job_name(id):sub(1, 3):upper();
end

local function n(v)                 -- 21300 -> "21,300"
    local s = tostring(math.floor(v));
    while true do
        local t, k = s:gsub('^(%d+)(%d%d%d)', '%1,%2');
        s = t;
        if k == 0 then return s; end
    end
end

--- The slim rows to show: { { frac, label } ... } (re-read a few times a second).
local function rows()
    local now = os.clock();
    if now - rows_at < 0.25 then return rows_cache; end
    rows_at = now;
    local out = {};
    local p = AshitaCore:GetMemoryManager():GetPlayer();
    local d = store.data;
    if p:GetMainJobLevel() >= 99 then
        local job = p:GetMainJob();
        if d.xp_cp ~= false then
            local cp, jp, spent = p:GetCapacityPoints(job) or 0, p:GetJobPoints(job) or 0, p:GetJobPointsSpent(job) or 0;
            if cp + jp + spent > 0 then
                out[#out + 1] = { cp / 30000, string.format('JP %d   CP %s/30,000', jp, n(cp)) };
            end
        end
        if d.xp_ep ~= false then
            local need = p:GetMasteryExpNeeded() or 0;
            if need > 0 then
                local ep = p:GetMasteryExp() or 0;
                out[#out + 1] = { ep / need, string.format('ML %d   EP %s/%s', p:GetMasteryJobLevel() or 0, n(ep), n(need)) };
            end
        end
        if d.xp_lp == true and not p:GetIsLimitModeEnabled() then
            out[#out + 1] = { (p:GetLimitPoints() or 0) / 10000,
                              string.format('Merits %d/%d   LP %s/10,000', p:GetMeritPoints() or 0, p:GetMeritPointsMax() or 0,
                                            n(p:GetLimitPoints() or 0)) };
        end
    end
    rows_cache = out;
    return out;
end

--- How far the bottom HUD rows (HP/MP/TP, the action bar) move up for the slim bars.
function expbar.lift()
    local k = #rows();
    return k == 0 and 0 or (k * ROW_H + 1);
end

--- The lift the EXP bar drew with lately (0 when it isn't being drawn), for the rows above it.
function expbar.drawn_lift()
    return (os.clock() - drawn_at < 0.5) and drawn_lift or 0;
end

function expbar.render()
    local p = AshitaCore:GetMemoryManager():GetPlayer();
    local main, lvl = p:GetMainJob(), p:GetMainJobLevel();
    local sub, slvl = p:GetSubJob(), p:GetSubJobLevel();

    local cur, need, label;
    if p:GetIsLimitModeEnabled() then
        cur, need, label = p:GetLimitPoints(), 10000, string.format('Limit  (%d merits)', p:GetMeritPoints());
    else
        cur, need, label = p:GetExpCurrent(), p:GetExpNeeded(), 'Next';
    end

    local tw, th = layout.size('exp_track');
    local extra = rows();
    local lift = expbar.lift();
    drawn_lift, drawn_at = lift, os.clock();
    local x, y = layout.anchor('bottom', tw + 40, 0, 14, -14 - lift, 'expbar');
    layout.bounds('expbar', x, y - 24, tw + 40, 30 + lift);

    draw.image('job_tile', x, y - 22);
    text.draw(abbr_obj, job_abbr(main), x + 15, y - 3, 'baseline');
    local jl = string.format('%s Level: %d', job_name(main), lvl);
    if sub ~= 0 and slvl > 0 then jl = jl .. string.format('   / %s %d', job_name(sub), slvl); end
    text.draw(job_obj, jl, x + 38, y - 6, 'baseline');

    draw.image('exp_track', x + 36, y - 2);
    if need > 0 and cur > 0 then
        draw.image('exp_fill', x + 36, y - 2, { sw = math.floor(tw * math.min(1, cur / need) + 0.5) });
    end
    local val = string.format('%d/%d', cur, need);
    text.draw(next_val, val, x + 36 + tw, y - 6, 'baseline');
    local vw = text.size(next_val);
    text.draw(next_lbl, label, x + 36 + tw - vw - 8 - text.size(next_lbl), y - 6, 'baseline');

    -- slim bars: a thin track as long as the space left of the label, the label at its right end
    for i, row in ipairs(extra) do
        local o = row_objs[i];
        if o == nil then
            o = text.new('label', { font_height = 14, font_color = 0xFFE8E0C8, font_alignment = text.align.Right });
            row_objs[i] = o;
        end
        local ry = y + 10 + (i - 1) * ROW_H;        -- (the track art has 3 px of padding round the tube)
        text.draw(o, row[2], x + 36 + tw, ry + 8, 'baseline');
        local len = tw - text.size(o) - 12;
        if len > 40 then
            local k = len / tw;
            draw.image('exp_track', x + 36, ry, { scale = { k, 0.6 } });
            local f = math.max(0, math.min(1, row[1]));
            if f > 0 then
                draw.image('exp_fill', x + 36, ry, { sw = math.floor(tw * f + 0.5), scale = { k, 0.6 } });
            end
        end
    end
end

return expbar;
