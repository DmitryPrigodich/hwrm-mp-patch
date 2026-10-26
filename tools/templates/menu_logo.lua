-- Keep the native wordmark/font; the cropped UV excludes the Hiigaran emblem.
BACKGROUND_LOGO = {
    type = "Frame",
    visible = 1,
    Layout = {
        sector = 1,
        size_WH = { w = 0.5, h = 0.5, wr = "scr", hr = "scr" },
        pivot_XY = { 0.5, 0.5 },
        pos_XY = { x = 0.25, y = 0.35, xr = "scr", yr = "scr" },
        lockAspect = 2,
    },
    [1] = {
        type = "Frame",
        name = "HWMP_Wordmark",
        Layout = {
            pos_XY = { x = 0, y = 0, xr = "par", yr = "par" },
            size_WH = { w = 1, h = 0.375, wr = "par", hr = "par" },
        },
        BackgroundGraphic = {
            type = "Graphic",
            uvRect = { 0, 1, 1, 0.625 },
            texture = "Data:UI/NewUI/Background/hwmp24_wordmark.tga",
        },
    },
    [2] = {
        type = "Frame",
        name = "HWMP_TaiidanEmblem",
        Layout = {
            pos_XY = { x = 0.5, y = 0.62, xr = "par", yr = "par" },
            size_WH = { w = 0.25, h = 0.5, wr = "par", hr = "par" },
            pivot_XY = { 0.5, 0.5 },
            lockAspect = 1,
        },
        BackgroundGraphic = {
            type = "Graphic",
            uvRect = { 0, 1, 1, 0 },
            texture = "Data:UI/NewUI/Background/hwmp24_taiidan.tga",
        },
    },
    [3] = {
        type = "TextLabel",
        name = "HWMP_MenuTitle",
        Layout = {
            pos_XY = { x = 0.5, y = 0.97, xr = "par", yr = "par" },
            size_WH = { w = 1, h = 0.15, wr = "par", hr = "par" },
            pivot_XY = { 0.5, 0.5 },
        },
        Text = {
            text = "Multiplayer Patch 2.4",
            font = "Heading2Font",
            pixels = 80,
            rel = 2160,
            color = { 128, 220, 255, 255 },
            hAlign = "Center",
            vAlign = "Middle",
        },
    },
}
