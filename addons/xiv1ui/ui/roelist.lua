--[[
* xiv1ui - Commands » Quests » Records of Eminence (and the Objective List's objectives), in place of FFXI's list
* (window "menu    quest01" with class +0x68 = 2, the list it shows: 0 Current / 1 Completed Quests (ui/quests.lua),
* 2 Records of Eminence, 3 the Objective List: its categories, their sub-categories, then a sub-category's
* objectives).
*
* The game keeps running its list: the cursor (+0x30, 0-based), the entries (+0x20 -> 8-byte records, the objective
* id in the low 12 bits of the first u16) and their count (+0x40). Names and descriptions come from the objectives' text table (DAT
* 55672, English): 4088 records of 0xC00 bytes from 0x20, one per objective id, every byte rotated right by 3 bits;
* in a record, u32 offsets at +4 (from +0x1C) to the short name, the full name (+0x14) and the description (+0x24).
* Progress comes from the server's 0x111 packet, completion from 0x112 (ui/roe.lua); the goals from
* core/roe_goals.lua.
*
* Objective List: an entry is a category (0xF200 + n: its name is record n of DAT 55673, 0xC00 bytes each,
* bytes rotated like the objectives', the name at +0x280) or an objective (0xEnnn, the id in the low 12 bits). The
* path taken is kept at +0x7C (u16s: the root 0xF200, the category, the sub-category).
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local mem     = require('core.mem');
local store   = require('core.store');
local gamewin = require('core.gamewin');
local xi_now  = require('core.now');

local roelist = {};
local ok_goals, GOALS = pcall(require, 'core.roe_goals');
if not ok_goals then GOALS = {}; end
local ok_rewards, REWARDS = pcall(require, 'core.roe_rewards');
if not ok_rewards then REWARDS = {}; end

-- objective id -> { name, text } (false: not readable), read from the DAT one record at a time
local texts, dat_path = {}, nil;
local function objective(id)
    local t = texts[id];
    if t ~= nil then return t or nil; end
    texts[id] = false;
    if dat_path == nil then dat_path = require('core.maps').dat_file(55672) or false; end
    if not dat_path then return nil; end
    local f = io.open(dat_path, 'rb');
    if f == nil then return nil; end
    f:seek('set', 0x20 + id * 0xC00);
    local raw = f:read(0xC00);
    f:close();
    if raw == nil or #raw < 0xC00 then return nil; end
    local b = {};
    for i = 1, #raw do
        local c = raw:byte(i);
        b[i] = string.char(bit.band(bit.bor(bit.lshift(c, 3), bit.rshift(c, 5)), 0xFF));
    end
    local d = table.concat(b);
    local function u32(o) return d:byte(o + 1) + d:byte(o + 2) * 256 + d:byte(o + 3) * 65536 + d:byte(o + 4) * 16777216; end
    if u32(0) ~= 6 then return nil; end
    local function str(o) return (d:sub(0x1C + o + 1):match('^[^%z]*')); end
    local name, desc = str(u32(4 + 4 * 4)), str(u32(4 + 8 * 4));
    if name == '' then name = str(u32(4)); end
    t = { name = name, text = desc };
    texts[id] = t;
    return t;
end
roelist.objective = objective;

-- category code -> name (false: not readable)
local cats, cat_path = {}, nil;
local function category(code)
    local k = code - 0xF200;
    if k < 0 or k > 1023 then return nil; end
    local c = cats[k];
    if c ~= nil then return c or nil; end
    cats[k] = false;
    if cat_path == nil then cat_path = require('core.maps').dat_file(55673) or false; end
    if not cat_path then return nil; end
    local f = io.open(cat_path, 'rb');
    if f == nil then return nil; end
    f:seek('set', k * 0xC00 + 0x280);
    local raw = f:read(64);
    f:close();
    if raw == nil then return nil; end
    local b = {};
    for i = 1, #raw do
        local v = bit.band(bit.bor(bit.lshift(raw:byte(i), 3), bit.rshift(raw:byte(i), 5)), 0xFF);
        if v == 0 then break; end
        b[#b + 1] = string.char(v);
    end
    c = table.concat(b);
    if c == '' then return nil; end
    cats[k] = c;
    return c;
end

local function which()
    if store.data.cmd_menu == false then return nil; end
    local _, f = require('core.native').focused();
    if f ~= 'quest01' then return nil; end
    local slot = gamewin.slot('quest01');
    local cls = slot and mem.u32(slot);
    local mode = cls and mem.u32(cls + 0x68);
    if mode ~= 2 and mode ~= 3 then return nil; end
    return cls, mode;
end
roelist.active = function () return which() ~= nil; end

local hider = gamewin.new({ frame_only = true });   -- (see gamewin.new)
local unreadable = nil;              -- a list render() left to the game (its texts couldn't be read)
function roelist.release() hider:restore(); end

--- At each scene start, before the game draws: the list is hidden as soon as it opens (render() draws ours).
-- After Confirm / Back the Objective List moves to another level only while the window's text is on (+0x6A). While
-- such a change is pending the class's +0x74 (the level's data) is 0, and the text is let on until it's there.
local function pending(cls) return mem.u32(cls + 0x68) == 3 and (mem.u32(cls + 0x74) or 0) == 0; end

function roelist.early()
    -- (only when render() will draw it: while the game is still fetching the list, it's left to the game)
    local cls = which();
    hider.pass = cls ~= nil and pending(cls);
    local n, list = cls and mem.u32(cls + 0x40), cls and mem.u32(cls + 0x20);
    if n and list and list ~= unreadable and n <= 512 and (n == 0 or mem.ok(list, n * 8)) then
        hider:hide({ 'quest01' });
    end
end

local W, ROW_H, SHOWN = 560, 46, 8;
local view_first, opened = 0, nil;

--- An objective's page: its description, how many, what it gives, and whether it can be done again.
function roelist.page(q, p, a, mode)
    local goal = GOALS[q.id] or 1;
    local rw = REWARDS[q.id];
    local done = require('ui.roe').completed(q.id) == true;
    local lines = {};
    if p then
        lines[#lines + 1] = string.format('Progress: %d / %d', p, goal);
    else
        lines[#lines + 1] = done and string.format('Completed (%d / %d)', goal, goal) or string.format('Number required: %d', goal);
    end
    if rw then
        local gives = {};
        if rw[1] > 0 then gives[#gives + 1] = string.format('%d Sparks', rw[1]); end
        if rw[2] > 0 then gives[#gives + 1] = string.format('%d EXP', rw[2]); end
        if rw[3] > 0 then gives[#gives + 1] = string.format('%d Unity Accolades', rw[3]); end
        if #gives > 0 then lines[#lines + 1] = 'Rewards: ' .. table.concat(gives, ', '); end
        lines[#lines + 1] = rw[4] and 'Repeatable' or 'Not repeatable';
    end
    local body = ui.label('roe_page', 'small', { font_height = 18, font_color = 0xFFE8E4D8, box_width = W - 56 });
    local btext = q.text:gsub('\n', ' ');
    if body.settings.text ~= btext then text.set(body, btext); end
    local _, bh2 = text.size(body);
    local LH = 24;
    local H = 52 + bh2 + 20 + #lines * LH + 36;
    local x, y = layout.anchor('topleft', W, H, 40, 60, 'roelist');
    local col = draw.alpha(0xFFFFFFFF, a);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh, col);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th, col);
    draw.image('title_swash', x + 8, y + 4, { color = col });
    local title = ui.label('roe_title', 'name', { font_height = 22 });
    title:set_opacity(a);
    text.draw(title, q.name, x + 40, y + 27, 'baseline');
    body:set_opacity(a);
    text.draw(body, btext, x + 28, y + 50);
    local ly = y + 52 + bh2 + 14;
    draw.rect(x + 20, ly - 6, W - 40, 1, draw.alpha(0x60C8A860, a));
    for i, l in ipairs(lines) do
        local o = ui.label('roe_pl' .. i, 'small', { font_height = 17 });
        local c = (i == #lines and rw) and 0xFFB8C0D8 or 0xFFE8C060;
        if o.settings.font_color ~= c then o:set_font_color(c); end
        o:set_opacity(a);
        text.draw(o, l, x + 28, ly + (i - 1) * LH + 16, 'baseline');
    end
    local hint = ui.label('roe_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
    hint:set_opacity(a);
    text.draw(hint, 'Back: the list', x + 24, y + H - 12, 'baseline');
end

function roelist.render()
    local cls = which();
    hider.pass = cls ~= nil and pending(cls);
    local n, cur, list = cls and mem.u32(cls + 0x40), cls and mem.u32(cls + 0x30), cls and mem.u32(cls + 0x20);
    if cls == nil or n == nil or n > 512 or list == nil or (n > 0 and not mem.ok(list, n * 8)) then
        -- (a list backed out of stays on screen a frame or more while the game closes it: hidden until then)
        if hider:active() then hider:release_except({ 'quest01' }); end
        opened = nil;
        return;
    end
    local mode = mem.u32(cls + 0x68);
    local rows, cat_level = {}, false;
    for i = 0, n - 1 do
        local code = mem.u16(list + i * 8) or 0;
        local o;
        if mode == 3 and code >= 0xF200 and code < 0xF600 then
            local nm = category(code);
            o = nm and { name = nm, text = '', cat = true };
            cat_level = true;
        else
            local id = bit.band(code, 0x0FFF);
            local ob = objective(id);
            o = ob and { id = id, name = ob.name, text = ob.text };
        end
        if o == nil then                      -- (text unreadable: the game's own list)
            if hider:active() then hider:restore(); end
            unreadable = list;
            return;
        end
        rows[#rows + 1] = o;
    end
    -- the Objective List's title: where in it you are
    local heading = 'Records of Eminence';
    if mode == 3 then
        local first = mem.u16(list) or 0;
        if cat_level and first - 0xF200 < 0x30 then heading = 'Objective List';
        elseif cat_level then heading = category(mem.u16(cls + 0x7E) or 0) or 'Objective List';
        else heading = category(mem.u16(cls + 0x80) or 0) or 'Objective List'; end
    end
    hider:hide({ 'quest01' });
    if opened == nil then opened, view_first = xi_now(), 0; end
    local a = math.min(1, (xi_now() - opened) / 0.15);
    if cur and cur < n then
        if cur < view_first then view_first = cur; end
        if cur >= view_first + SHOWN then view_first = cur - SHOWN + 1; end
    else
        cur = nil;
    end
    view_first = math.max(0, math.min(view_first, math.max(0, n - SHOWN)));
    local shown = math.min(SHOWN, n);

    -- progress: what the server last said for the objectives you have undertaken
    local progress = {};
    require('ui.roe').restore();
    for _, r in ipairs(require('ui.roe').records or {}) do progress[r.id] = r.progress; end

    local sel = cur and rows[cur + 1];
    if sel and sel.text == '' then sel = nil; end
    local RH = cat_level and 32 or ROW_H;            -- (a category is a name only)
    -- Confirm on an objective: the game turns the window into that objective's page (+0x64 = 1) until Back
    if sel and sel.id and mem.u32(cls + 0x64) == 1 then
        roelist.page(sel, progress[sel.id], a, mode);
        return;
    end
    local desc = ui.label('roe_desc', 'small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = W - 48 });
    local dtext = sel and (sel.text:gsub('\n', ' ')) or '';
    if desc.settings.text ~= dtext then text.set(desc, dtext); end
    local _, dh = text.size(desc);
    local H = 52 + math.max(1, shown) * RH + (sel and dh + 30 or 20) + 26;
    local x, y = layout.anchor('topleft', W, H, 40, 60, 'roelist');
    local col = draw.alpha(0xFFFFFFFF, a);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh, col);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th, col);
    draw.image('title_swash', x + 8, y + 4, { color = col });
    local title = ui.label('roe_title', 'name', { font_height = 22 });
    title:set_opacity(a);
    text.draw(title, heading, x + 40, y + 27, 'baseline');
    local sp = require('ui.roe').sparks;
    local cnt = ui.label('roe_count', 'small', { font_height = 15, font_color = 0xFFC8C4B8, font_alignment = text.align.Right });
    cnt:set_opacity(a);
    local taken = mode == 2 and n or (require('ui.roe').current or 0);
    text.draw(cnt, (sp and string.format('Sparks %d   ', sp) or '') .. string.format('%d / 30', taken), x + W - 20,
              y + 25, 'baseline');

    if n == 0 then
        local none = ui.label('roe_none', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
        none:set_opacity(a);
        text.draw(none, mode == 2 and 'No objectives undertaken.' or 'Nothing here yet.', x + 34, y + 72, 'baseline');
    end
    local sw, sh = layout.size('row_sel');
    for r = 1, shown do
        local i = view_first + r;
        local q = rows[i];
        local ry = y + 44 + (r - 1) * RH;
        local on = (cur and i - 1 == cur);
        if on then
            draw.nine('row_sel', x + 22, ry, W - 44, RH - 4, 6, sw, sh, col);
            draw.image('cursor_gold', x + 2, ry + (cat_level and 1 or 8), { color = col });
        end
        local o = ui.label('roe_row' .. r, 'small', { font_height = 18 });
        -- (limited-time challenges in pink, as FFXI marks them)
        local timed = q.text:find('^%[Limited%-time') ~= nil;
        local c = timed and (on and 0xFFFFC8E0 or 0xFFF0A0C8) or (on and 0xFFFFFFFF or 0xFFD8D4C8);
        if o.settings.font_color ~= c then o:set_font_color(c); end
        o:set_opacity(a);
        text.draw(o, q.name, x + 40, ry + 21, 'baseline');
        -- a category opens onto more: a small arrow at the right
        if q.cat then draw.image('dlg_arrow', x + W - 46, ry + 9, { rot = math.pi / 2, color = col }); end
        -- the progress bar under the name: gold, full when done
        -- (the server leaves out objectives with no progress yet: those start at 0; in the Objective List, ones
        -- not taken on show their goal only, and completed ones are full)
        -- (no entry in the goals table: a goal of 1)
        local goal = GOALS[q.id] or 1;
        local done = (not q.cat) and require('ui.roe').completed(q.id) == true;
        local p = (not q.cat) and (progress[q.id] or (done and goal) or 0) or nil;
        if p and mode == 3 and progress[q.id] then
            local tag = ui.label('roe_tag' .. r, 'small', { font_height = 13, font_color = 0xFFE8C060,
                                                            font_alignment = text.align.Right });
            tag:set_opacity(a);
            text.draw(tag, 'Taken on', x + W - 30, ry + 19, 'baseline');
        end
        if p then
            local frac = math.max(0, math.min(1, p / goal));
            local bx, by, bwid = x + 40, ry + 29, W - 190;
            draw.rect(bx, by, bwid, 6, draw.alpha(0x40C8A860, a));
            draw.rect(bx, by, math.floor(bwid * frac + 0.5), 6, draw.alpha(frac >= 1 and 0xFF9BE08C or 0xFFE8C060, a));
            local pl = ui.label('roe_prog' .. r, 'small', { font_height = 15, font_color = 0xFFE8E4D8,
                                                            font_alignment = text.align.Right });
            pl:set_opacity(a);
            text.draw(pl, done and 'Complete' or string.format('%d / %d', p, goal), x + W - 30, ry + 36, 'baseline');
        end
    end
    local dy = y + 52 + math.max(1, shown) * RH;
    if sel then
        draw.rect(x + 20, dy - 2, W - 40, 1, draw.alpha(0x60C8A860, a));
        desc:set_opacity(a);
        text.draw(desc, dtext, x + 24, dy + 10);
    end
    local hint = ui.label('roe_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
    hint:set_opacity(a);
    text.draw(hint, cat_level and 'Confirm: open   Left / Right: other lists'
                    or mode == 3 and 'Confirm: take on / cancel   Left / Right: other lists'
                    or 'Confirm: options   Left / Right: other lists', x + 24, y + H - 12, 'baseline');
end

return roelist;
