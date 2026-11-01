--[[
* xiv1ui - text.
*
* Registers the bundled fonts with Windows for this process, then makes gdifonts text objects in a few named
* styles. Objects are drawn manually through the shared sprite (draw.sprite()) so they layer correctly with images.
*
* UI scale: callers work in unscaled HUD units. Text is re-rendered at the scaled size (so it stays crisp rather than
* being stretched), positioned in screen pixels, and text.size reports back in HUD units.
--]]

local ffi = require('ffi');
local gdi = require('gdifonts.include');
local draw = require('core.draw');

ffi.cdef[[
    int __stdcall AddFontResourceExA(const char* name, uint32_t fl, void* res);
    int __stdcall RemoveFontResourceExA(const char* name, uint32_t fl, void* res);
]]
local gdi32 = ffi.load('gdi32');

local text = {};

local FONT_FILES = {
    'XIV1UI-Serif-Regular.ttf',
    'XIV1UI-Serif-Italic.ttf',
    'XIV1UI-SerifBold.ttf',
    'XIV1UI-SerifJP.ttf',
    'PTSans-Regular.ttf',         -- chat font choices (OFL, unmodified)
    'PTSerif-Regular.ttf',
};
local loaded = {};

-- Family names inside the bundled files (built by tools/make_fonts.py from Alegreya, OFL).
text.SERIF        = 'XIV1UI Serif';
text.SERIF_BOLD   = 'XIV1UI Serif Bold';
text.FALLBACK     = 'Arial';

text.flags = gdi.FontFlags;
text.align = gdi.Alignment;
text.gradient = gdi.Gradient;

-- Named styles. Heights are in pixels at UI scale 1. SERIF_BOLD is already bold italic (it is that family's only,
-- "Regular" face), so its styles use no flags; asking GDI+ for another style of it draws nothing.
text.styles = {
    numeral   = { font_family = 'SERIF_BOLD', font_flags = 0, font_height = 34, font_color = 0xFFFFFFFF,
                  outline_color = 0xC0101018, outline_width = 2,
                  gradient_style = 3, gradient_color = 0xFFC8D0E0 },
    label     = { font_family = 'SERIF', font_flags = 2, font_height = 19, font_color = 0xFFE8E4D8,
                  outline_color = 0xC0101018, outline_width = 2 },
    small     = { font_family = 'SERIF', font_flags = 0, font_height = 17, font_color = 0xFFE8E4D8,
                  outline_color = 0xC0101018, outline_width = 2 },
    name      = { font_family = 'SERIF', font_flags = 2, font_height = 24, font_color = 0xFFFFFFFF,
                  outline_color = 0xC0101018, outline_width = 2 },
    slotkey   = { font_family = 'SERIF_BOLD', font_flags = 0, font_height = 17, font_color = 0xFFFFFFFF,
                  outline_color = 0xFF000000, outline_width = 2 },
    timer     = { font_family = 'SERIF_BOLD', font_flags = 0, font_height = 18, font_color = 0xFFFFFFFF,
                  outline_color = 0xFF000000, outline_width = 2 },
};

function text.init(addon_path)
    for _, f in ipairs(FONT_FILES) do
        local p = addon_path .. 'fonts\\' .. f;
        if gdi32.AddFontResourceExA(p, 0, nil) > 0 then
            loaded[#loaded + 1] = p;
        end
    end
    -- Fall back to Arial if the bundled fonts could not be registered.
    if not gdi:get_font_available(text.SERIF) then text.SERIF = text.FALLBACK; end
    if not gdi:get_font_available(text.SERIF_BOLD) then text.SERIF_BOLD = text.FALLBACK; end
end

function text.release()
    gdi:destroy_interface();
    for _, p in ipairs(loaded) do gdi32.RemoveFontResourceExA(p, 0, nil); end
    loaded = {};
end

--- Make a text object in a named style; overrides is an optional table of gdifonts settings.
function text.new(style, overrides)
    local s = {};
    for k, v in pairs(text.styles[style] or text.styles.small) do s[k] = v; end
    if overrides then for k, v in pairs(overrides) do s[k] = v; end end
    -- fixed = true: text that must fit a badge (job tile, compass N) ignores Minimum text size
    local fixed = s.fixed;
    s.fixed = nil;
    if s.font_family == 'SERIF' then s.font_family = text.SERIF;
    elseif s.font_family == 'SERIF_BOLD' then s.font_family = text.SERIF_BOLD; end
    local obj = gdi:create_object(s, true);
    obj.hud = { h = s.font_height, ow = s.outline_width or 0, bw = s.box_width or 0, scale = 1, min = 0, fixed = fixed };
    -- callers set the HUD-unit height; the object renders at the scaled (and minimum-raised) one
    local set_h = obj.set_font_height;
    obj.set_font_height = function (self, h)
        self.hud.h = h;
        local px = math.floor(math.max(h, self.hud.min) * self.hud.scale + 0.5);
        self:set_outline_width(text.outline_px(self.hud.ow, px, self.hud.scale));
        set_h(self, px);
    end
    return obj;
end

--- The outline width (pixels) for text drawn `px` pixels high at UI scale `sc` (the same at every size).
function text.outline_px(ow, px, sc)
    return math.floor(ow * sc + 0.5);
end

-- Configuration » Minimum text size: smaller text is drawn at this height instead (HUD units; 0 = off).
local function min_size()
    return require('core.store').data.min_text or 0;
end

-- Re-render an object at the current UI scale / minimum size if either changed.
local function sync(obj)
    local hud, sc, mn = obj.hud, draw.scale, min_size();
    if hud and hud.fixed then mn = 0; end
    if hud == nil or (hud.scale == sc and hud.min == mn) then return; end
    hud.scale, hud.min = sc, mn;
    obj.settings.font_height = math.floor(math.max(hud.h, mn) * sc + 0.5);
    obj.settings.outline_width = text.outline_px(hud.ow, obj.settings.font_height, sc);
    obj.settings.box_width = math.floor(hud.bw * sc + 0.5);
    obj.is_dirty = true;
end

--- Change a text object's wrap width (HUD units); it re-wraps at the next draw.
function text.set_box_width(obj, w)
    if obj.hud == nil or obj.hud.bw == w then return; end
    obj.hud.bw = w;
    obj.hud.scale = nil;          -- (sync re-applies the scaled width)
end

--- Text box size in HUD units.
function text.size(obj)
    sync(obj);
    local w, h = obj:get_text_size();
    return w / draw.scale, h / draw.scale;
end

--- Draw an object at its top-left (x, y in HUD units), for callers that set the text themselves.
function text.render(obj, x, y)
    sync(obj);
    obj.settings.position_x = x * draw.scale;
    obj.settings.position_y = y * draw.scale;
    obj:render(draw.sprite());
end

-- Where the baseline sits inside a gdifonts texture, as a fraction of its height (measured for the bundled serif;
-- its tall line spacing leaves a lot of room below the glyphs).
local BASELINE = 0.91;

-- gdifonts textures are cut to the ink: the top is fixed for a given font, but the height grows with descenders
-- ("Gear" 20 px, "Journal" 24 px at 17 px). So the baseline is measured once per font on a descender-free string.
local ref_heights = {};
local function baseline_offset(obj)
    local st = obj.settings;
    local key = st.font_family .. '|' .. st.font_height .. '|' .. st.font_flags .. '|' .. st.outline_width;
    local h = ref_heights[key];
    if h == nil then
        local probe = gdi:create_object({ font_family = st.font_family, font_height = st.font_height,
            font_flags = st.font_flags, outline_width = st.outline_width, text = 'HEIGHT 0' }, true);
        local _, ph = probe:get_text_size();
        h = (ph > 0) and ph or st.font_height;
        ref_heights[key] = h;
    end
    return math.floor(h * BASELINE + 0.5);
end

-- Japanese (and other non-Latin) text: the Latin serif has no kana/kanji, so strings with CJK characters switch to
-- the bundled Japanese serif (Noto Serif JP, OFL), or failing that the first Japanese-capable system font.
local CJK_FONTS = { 'XIV1UI Serif JP', 'Yu Mincho', 'MS Mincho', 'MS PMincho', 'Osaka', 'Arial Unicode MS',
                    'MS Gothic' };
local cjk_font = false;
local function cjk_family()
    if cjk_font == false then
        cjk_font = nil;
        for _, f in ipairs(CJK_FONTS) do
            if gdi:get_font_available(f) then cjk_font = f; break; end
        end
    end
    return cjk_font;
end

local function has_cjk(str)
    return str:find('[\227-\239]') ~= nil;      -- UTF-8 lead bytes of the CJK/kana ranges
end

local function set_text(obj, str)
    local fam = obj.base_family or obj.settings.font_family;
    obj.base_family = fam;
    local want = (has_cjk(str) and cjk_family()) or fam;
    if obj.settings.font_family ~= want then obj:set_font_family(want); end
    obj:set_text(str);
end
text.set = set_text;

--- Set text/position (only re-rendering the texture when the text changes) and draw it.
-- By default y is the top of the text box; with valign = 'baseline', y is where the text should sit.
function text.draw(obj, str, x, y, valign)
    sync(obj);
    if obj.settings.text ~= str then set_text(obj, str); end
    x, y = x * draw.scale, y * draw.scale;
    if valign == 'baseline' then
        y = y - baseline_offset(obj);
    end
    obj.settings.position_x = x;
    obj.settings.position_y = y;
    obj:render(draw.sprite());
end

return text;
