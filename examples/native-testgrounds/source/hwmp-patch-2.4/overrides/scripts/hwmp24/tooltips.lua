-- The native locale alias selects the sibling language archive.
dofilepath("locale:hwmp24_tooltips.lua")

function HWMP_TooltipText(value)
    if value == nil then return nil end
    if strsub(value, 1, 1) == "$" then return HWMP_TooltipLocalization[value] end
    return value
end

function HWMP_TooltipBaseTime()
    return HWMP_TooltipBaseTimeLabel
end

function HWMP_TooltipValue()
    return HWMP_TooltipValueLabel
end
