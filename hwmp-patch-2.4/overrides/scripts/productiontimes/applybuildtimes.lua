-- HWMP2.4: selected-language text; unknown descriptions retain their UCS ID.
doscanpath("data:ui", "playerspatch_ui_util.lua")
if GetProductionTimeSetting() == 2 then
    dofilepath("data:scripts/hwmp24/tooltips.lua")
    dofilepath("data:scripts/productiontimes/buildtimes.lua")
    for i, item in build do
        local seconds = buildtimes[item.ThingToBuild]
        local description = HWMP_TooltipText(item.Description)
        if seconds ~= nil and description ~= nil and description ~= "" then
            build[i].Description = description .. "  \n\n<b>" .. HWMP_TooltipBaseTime() .. ":</b>  " .. seconds .. "s"
        end
    end
end
