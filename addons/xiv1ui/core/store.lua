--[[
* xiv1ui - saved settings (per character, via Ashita's settings library).
--]]

local settings = require('settings');

local defaults = T{
    hide_native = true,    -- hide the FFXI panels xiv1ui replaces
    layout = T{},          -- per-widget drag offsets: layout[id] = { dx, dy }
    ui_locked = false,     -- UI Lock: widgets can't be dragged
    ui_scale = 1,          -- UI scale (one of draw.SCALES)
    chat_size = 16,        -- chat log text height (px at UI scale 1)
    min_text = 0,          -- smaller text is raised to this height (0 = off)
    macro = T{
        palette = true,    -- Ctrl/Alt show xiv1ui's macro palette instead of the game's
        book = 1,
        set = 1,
    },
    hotbar = T{
        page = 1,
        keys = false,      -- bind number keys 1..0 to the slots
        bars = T{},        -- bars[job][page][slot] = binding (see core/actions.lua)
    },
};

local store = { data = settings.load(defaults) };

settings.register('settings', 'xiv1ui_settings_update', function (s)
    if s ~= nil then store.data = s; end
end);

function store.save()
    settings.save();
end

return store;
