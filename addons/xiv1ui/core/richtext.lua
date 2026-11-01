--[[
* xiv1ui - text in more than one colour (a chat line with its key words lit). The font library draws each text object
* in one colour, so a rich line is laid out here from coloured pieces: word wrapping is done by xiv1ui, from each
* character's width (measured once per font and size), and every run of one colour on a row is its own text object.
*
*   local r = rich.new(style)                -- style: { font_family, font_height, outline_width }
*   rich.set(r, { { 'text', ARGB }, ... })   -- the pieces, in order
*   rich.set_width(r, w)                     -- wrap width (HUD units)
*   local w, h = rich.size(r)                -- laid-out size (HUD units)
*   rich.render(r, x, y, opacity)            -- top-left at x, y
--]]

local text = require('core.text');
local draw = require('core.draw');

local rich = {};

-- character advance widths per font style (HUD units), measured on first use
local widths = {};
local probes = {};

local function style_key(st) return st.font_family .. '|' .. st.font_height .. '|' .. st.outline_width; end

-- a text object in the style, for measuring (one per style, so the text module scales it like the real ones)
local function probe_for(st)
    local key = style_key(st);
    local p = probes[key];
    if p == nil then
        p = text.new('small', { font_height = st.font_height, outline_width = st.outline_width,
                                font_family = st.font_family });
        p.base_family = st.font_family;
        probes[key] = p;
    end
    return p;
end

local function measure(st, s)
    local p = probe_for(st);
    text.set(p, s);
    return (text.size(p));
end

-- the advance of one character (a UTF-8 sequence): eleven in a row less one, over ten (padding and outline cancel)
local function advance(st, ch)
    local key = style_key(st) .. '|' .. draw.scale;
    local t = widths[key];
    if t == nil then t = {}; widths[key] = t; end
    local w = t[ch];
    if w == nil then
        if ch == ' ' then
            w = (measure(st, 'a' .. (' '):rep(10) .. 'a') - measure(st, 'aa')) / 10;
        else
            w = (measure(st, ch:rep(11)) - measure(st, ch)) / 10;
        end
        t[ch] = w;
    end
    return w;
end

local function width_of(st, s)
    local w = 0;
    for ch in s:gmatch('[%z\1-\127\194-\244][\128-\191]*') do w = w + advance(st, ch); end
    return w;
end

-- the height of one row and the step between rows
local rows_h = {};
local function row_metrics(st)
    local key = style_key(st) .. '|' .. draw.scale;
    local m = rows_h[key];
    if m then return m[1], m[2]; end
    local p = probe_for(st);
    text.set(p, 'Ag');
    local _, h1 = text.size(p);
    text.set(p, 'Ag\nAg');
    local _, h2 = text.size(p);
    m = { h1, h2 - h1 };
    rows_h[key] = m;
    return h1, h2 - h1;
end

function rich.new(style)
    return { style = { font_family = style.font_family or text.SERIF, font_height = style.font_height or 16,
                       outline_width = style.outline_width or 2 },
             pieces = {}, width = 0, runs = {}, dirty = true, w = 0, h = 0 };
end

function rich.set(r, pieces) r.pieces = pieces; r.dirty = true; end
function rich.set_width(r, w) if r.width ~= w then r.width = w; r.dirty = true; end end

local function layout(r)
    if not r.dirty and r.scale == draw.scale then return; end
    r.dirty, r.scale = false, draw.scale;
    local st = r.style;
    local h1, step = row_metrics(st);
    -- words (with the spaces after them), each keeping its piece's colour
    local words = {};
    for _, p in ipairs(r.pieces) do
        for word, sp in p[1]:gmatch('([^ ]*)( *)') do
            if word ~= '' or sp ~= '' then words[#words + 1] = { word, sp, p[2] }; end
        end
    end
    -- greedy wrap: a word that doesn't fit starts the next row (its trailing spaces may hang over the edge)
    local rows, row, x = {}, {}, 0;
    local maxw = (r.width > 0) and r.width or math.huge;
    for _, wd in ipairs(words) do
        local ww, sw = width_of(st, wd[1]), width_of(st, wd[2]);
        if x > 0 and x + ww > maxw then
            rows[#rows + 1] = row;
            row, x = {}, 0;
        end
        row[#row + 1] = { wd[1] .. wd[2], wd[3], x };
        x = x + ww + sw;
    end
    rows[#rows + 1] = row;
    -- runs: consecutive words of one colour on a row become one text object
    local old = r.runs;
    local runs, k = {}, 0;
    local widest = 0;
    for ri, rw in ipairs(rows) do
        local i = 1;
        while i <= #rw do
            local s, col, x0 = rw[i][1], rw[i][2], rw[i][3];
            local j = i + 1;
            while j <= #rw and rw[j][2] == col do s = s .. rw[j][1]; j = j + 1; end
            k = k + 1;
            local obj = old[k] and old[k].obj;
            if obj == nil then
                obj = text.new('small', { font_height = st.font_height, outline_width = st.outline_width,
                                          font_family = st.font_family, font_color = col });
                obj.base_family = st.font_family;
            elseif obj.settings.font_color ~= col then
                obj:set_font_color(col);
            end
            -- (the font drops spaces at either end of a text object: a run that starts with them moves right)
            local lead = s:match('^ +');
            if lead then x0 = x0 + width_of(st, lead); s = s:sub(#lead + 1); end
            s = s:gsub(' +$', '');
            if obj.settings.text ~= s then text.set(obj, s); end
            runs[k] = { obj = obj, x = x0, row = ri - 1 };
            widest = math.max(widest, x0 + width_of(st, s));
            i = j;
        end
    end
    r.runs = runs;
    r.w, r.h = widest, h1 + (#rows - 1) * step;
    r.step = step;
end

function rich.size(r)
    layout(r);
    return r.w, r.h;
end

function rich.render(r, x, y, opacity)
    layout(r);
    for _, run in ipairs(r.runs) do
        if opacity then run.obj:set_opacity(opacity); end
        text.render(run.obj, x + run.x, y + run.row * r.step);
    end
end

return rich;
