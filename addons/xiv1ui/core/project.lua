--[[
* xiv1ui - world-to-screen projection, using the view and projection transforms the game leaves on the device
* at present time (the same approach as the targetlines addon).
--]]

local d3d = require('d3d8');
local ffi = require('ffi');

local project = {};

local dev = d3d.get_device();
local view, proj, vw, vh;

--- Call once per frame (from d3d_present) before using project.point.
function project.begin()
    local ok1, v = dev:GetTransform(ffi.C.D3DTS_VIEW);
    local ok2, p = dev:GetTransform(ffi.C.D3DTS_PROJECTION);
    local _, vp = dev:GetViewport();
    view, proj = v, p;
    vw, vh = vp and vp.Width or 0, vp and vp.Height or 0;
end

--- Which way the camera looks, as a heading in the game's convention (radians; 0 east, +pi/2 south), or nil.
-- (The view matrix's third column is the camera's forward vector in world space: x, y up, z = the game's north.)
function project.camera_heading()
    if view == nil then return nil; end
    local fx, fz = view._13, view._33;
    -- (checked by projecting compass points: the forward column points away from the scene here, so it's negated)
    return math.atan2(fz, -fx);
end

--- Project a point in D3D world space (x, y up, z). Returns sx, sy (in HUD units, see core/draw.lua), visible.
function project.point(x, y, z)
    if view == nil or proj == nil or vw == 0 then return nil; end
    local v, p = view, proj;
    -- row vector * view
    local cx = x * v._11 + y * v._21 + z * v._31 + v._41;
    local cy = x * v._12 + y * v._22 + z * v._32 + v._42;
    local cz = x * v._13 + y * v._23 + z * v._33 + v._43;
    local cw = x * v._14 + y * v._24 + z * v._34 + v._44;
    -- * projection
    local px = cx * p._11 + cy * p._21 + cz * p._31 + cw * p._41;
    local py = cx * p._12 + cy * p._22 + cz * p._32 + cw * p._42;
    local pw = cx * p._14 + cy * p._24 + cz * p._34 + cw * p._44;
    if pw <= 0.0001 then return nil; end
    local nx, ny = px / pw, py / pw;
    local k = require('core.draw').scale;
    return (nx + 1) * 0.5 * vw / k, (1 - ny) * 0.5 * vh / k, (nx > -1.2 and nx < 1.2 and ny > -1.2 and ny < 1.2);
end

local ffi_ = require('ffi');
local mem  = require('core.mem');

--- Where entity i is drawn: x, feet height, y (D3D world space) and the model's height, or nil if unknown.
-- While running, the logical position (LocalPosition) leads the drawn body and the actor's copy at actor+0x5FC
-- trails it, each by ~0.5 yalms; the body is at their midpoint. The height comes from the model's bounding box
-- (8 corners of x, height, y, w at actor+0x918; corners 0-3 at the feet, 4-7 at the top; height grows downward).
-- See docs/MODDING-NOTES.md.
function project.anchor(i)
    local e = AshitaCore:GetMemoryManager():GetEntity();
    local a = e:GetActorPointer(i);
    if a == nil or a == 0 or not mem.ok(a + 0x5FC, 12) or not mem.ok(a + 0x918, 0x80) then return nil; end
    local p = ffi_.cast('float*', a + 0x5FC);
    local b = ffi_.cast('float*', a + 0x918);
    -- (a character that has only just come into the world can have its model box not yet filled in: no anchor yet)
    local top, feet = tonumber(b[1]), tonumber(b[17]);
    if top == nil or feet == nil then return nil; end
    local h = top - feet;
    if h ~= h or h < 0.3 or h > 20 then return nil; end
    local lx, lz, ly = e:GetLocalPositionX(i), e:GetLocalPositionZ(i), e:GetLocalPositionY(i);
    if lx == nil or lz == nil or ly == nil then return nil; end      -- (the entity went away, e.g. while zoning)
    return (p[0] + lx) / 2, (p[1] + lz) / 2, (p[2] + ly) / 2, h;
end

--- Screen position of a point on entity i's model: frac = 0 at the feet, 1 at the top of its bounding box, plus
-- `extra` yalms. Falls back to the logical position lifted by `fallback` yalms.
function project.on_model(i, frac, extra, fallback)
    local x, feet, y, h = project.anchor(i);
    if x then return project.point(x, feet - h * frac - (extra or 0), y); end
    return project.entity(i, fallback or 1.2);
end

--- Screen position of an entity (by index), lifted `up` yalms above its feet. FFXI keeps positions as x, y (north),
-- z (height); in D3D space height is the second axis. (Verified in game: an orc's feet project onto its feet.)
function project.entity(idx, up)
    local e = AshitaCore:GetMemoryManager():GetEntity();
    local x, y, z = e:GetLocalPositionX(idx), e:GetLocalPositionY(idx), e:GetLocalPositionZ(idx);
    if x == nil then return nil; end
    return project.point(x, z - (up or 0), y);
end

return project;
