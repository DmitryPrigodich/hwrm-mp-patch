-- Native atlas V=0 is its top: keep the wordmark, exclude the baked blue emblem.
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
            uvRect = { 0, 0.375, 1, 0 },
            texture = "Data:UI/NewUI/Background/hwmp24_wordmark.tga",
        },
    },
    [2] = {
        type = "Frame",
        name = "HWMP_HiigaranEmblem",
        Layout = {
            pos_XY = { x = 0.17, y = 0.64, xr = "par", yr = "par" },
            size_WH = { w = 0.18, h = 0.36, wr = "par", hr = "par" },
            pivot_XY = { 0.5, 0.5 },
            lockAspect = 1,
        },
        BackgroundGraphic = {
            type = "Graphic",
            uvRect = { 0, 1, 1, 0 },
            texture = "Data:UI/NewUI/Background/hwmp24_hiigaran.tga",
        },
    },
    [3] = {
        type = "Frame",
        name = "HWMP_VaygrEmblem",
        Layout = {
            pos_XY = { x = 0.39, y = 0.64, xr = "par", yr = "par" },
            size_WH = { w = 0.18, h = 0.36, wr = "par", hr = "par" },
            pivot_XY = { 0.5, 0.5 },
            lockAspect = 1,
        },
        BackgroundGraphic = {
            type = "Graphic",
            uvRect = { 0, 1, 1, 0 },
            texture = "Data:UI/NewUI/Background/hwmp24_vaygr.tga",
        },
    },
    [4] = {
        type = "Frame",
        name = "HWMP_TaiidanEmblem",
        Layout = {
            pos_XY = { x = 0.61, y = 0.64, xr = "par", yr = "par" },
            size_WH = { w = 0.18, h = 0.36, wr = "par", hr = "par" },
            pivot_XY = { 0.5, 0.5 },
            lockAspect = 1,
        },
        BackgroundGraphic = {
            type = "Graphic",
            uvRect = { 0, 1, 1, 0 },
            texture = "Data:UI/NewUI/Background/hwmp24_taiidan.tga",
        },
    },
    [5] = {
        type = "Frame",
        name = "HWMP_KushanEmblem",
        Layout = {
            pos_XY = { x = 0.83, y = 0.64, xr = "par", yr = "par" },
            size_WH = { w = 0.18, h = 0.36, wr = "par", hr = "par" },
            pivot_XY = { 0.5, 0.5 },
            lockAspect = 1,
        },
        BackgroundGraphic = {
            type = "Graphic",
            uvRect = { 0, 1, 1, 0 },
            texture = "Data:UI/NewUI/Background/hwmp24_kushan.tga",
        },
    },
    [6] = {
        type = "TextLabel",
        name = "HWMP_MenuTitle",
        Layout = {
            pos_XY = { x = 0.5, y = 0.95, xr = "par", yr = "par" },
            size_WH = { w = 1, h = 0.15, wr = "par", hr = "par" },
            pivot_XY = { 0.5, 0.5 },
        },
        Text = {
            text = "Multiplayer Patch 2.4.5",
            font = "Heading2Font",
            pixels = 80,
            rel = 2160,
            color = { 128, 220, 255, 255 },
            hAlign = "Center",
            vAlign = "Middle",
        },
    },
}
