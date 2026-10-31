--[[
* xiv1ui - layout helpers: screen size, anchors, and texture content sizes from assets/manifest.lua.
--]]

local scaling = require('scaling');

local layout = {};

local manifest = nil;

function layout.init(addon_path)
    local ok, m = pcall(dofile, addon_path .. 'assets\\manifest.lua');
    manifest = ok and m or {};
    local ok2, icons = pcall(dofile, addon_path .. 'assets\\icons_manifest.lua');      -- macro icons (make_icons.py)
    if ok2 and type(icons) == 'table' then for k, v in pairs(icons) do manifest[k] = v; end end
    local ok3, ai = pcall(dofile, addon_path .. 'assets\\action_icons_manifest.lua');  -- action icons (make_action_icons.py)
    if ok3 and type(ai) == 'table' then for k, v in pairs(ai) do manifest[k] = v; end end
end

--- Content size of a generated texture (the PNG canvas is padded to a power of two).
function layout.size(name)
    local s = manifest and manifest[name];
    if s then return s[1], s[2]; end
    return 0, 0;
end

--- Screen size in HUD units (screen pixels divided by the UI scale).
function layout.screen()
    local k = require('core.draw').scale;
    return scaling.window.w / k, scaling.window.h / k;
end

-- Screen boxes of the HUD widgets this frame (for dragging): widgets[id] = { x, y, w, h }.
layout.widgets = {};

-- (boxes are kept in plain HUD units: a scaled part's box is multiplied out by its factor)
function layout.bounds(id, x, y, w, h)
    local k = require('core.draw').part;
    layout.widgets[id] = { x * k, y * k, w * k, h * k };
end

--- Top-left corner for a w x h block placed at an anchor ('bottom', 'top', 'topleft', ...) plus an offset.
-- With an id, the widget's saved drag offset is added too.
-- A HUD part's sideways shift (Configuration » HUD, e.g. the action bar group moved right to make room for the chat),
-- in plain HUD units; set by xiv1ui.lua while that part draws.
layout.part_dx = 0;

function layout.anchor(where, w, h, dx, dy, id)
    dx = (dx or 0) + layout.part_dx / require('core.draw').part;
    if id then
        local ox, oy = layout.offset(id);
        dx, dy = (dx or 0) + ox, (dy or 0) + oy;
    end
    local sw, sh = layout.screen();
    local x, y;
    if where == 'bottom' then      x, y = (sw - w) / 2, sh - h;
    elseif where == 'top' then     x, y = (sw - w) / 2, 0;
    elseif where == 'topleft' then x, y = 0, 0;
    elseif where == 'topright' then x, y = sw - w, 0;
    elseif where == 'bottomleft' then x, y = 0, sh - h;
    elseif where == 'bottomright' then x, y = sw - w, sh - h;
    elseif where == 'left' then    x, y = 0, (sh - h) / 2;
    elseif where == 'right' then   x, y = sw - w, (sh - h) / 2;
    else                           x, y = (sw - w) / 2, (sh - h) / 2; end
    return math.floor(x + (dx or 0)), math.floor(y + (dy or 0));
end

-- Per-widget offsets from HUD layout editing (dragging), saved in the settings: layout.offset(id) -> dx, dy.
-- (offsets are saved in plain HUD units; a scaled part gets them in its own units)
function layout.offset(id)
    local o = require('core.store').data.layout[id];
    local k = require('core.draw').part;
    if o then return o[1] / k, o[2] / k; end
    return 0, 0;
end

function layout.move(id, dx, dy)
    local st = require('core.store');
    local o = st.data.layout[id] or T{ 0, 0 };
    st.data.layout[id] = T{ o[1] + dx, o[2] + dy };
end

function layout.reset()
    local st = require('core.store');
    st.data.layout = T{};
    st.save();
end

return layout;
