-- HWMP2.4: do not replace localized text with a forced English dictionary.
doscanpath("data:ui", "playerspatch_ui_util.lua")
if GetProductionTimeSetting() == 2 then
    dofilepath("data:scripts/hwmp24/tooltips.lua")
    for i, item in research do
        local description = HWMP_TooltipText(item.Description)
        if description ~= nil and description ~= "" and item.Time ~= nil then
            local value = ""
            if item.UpgradeValue ~= nil then
                local percent = item.UpgradeValue * 100 - 100
                local sign = ""
                if percent > 0 then sign = "+" end
                value = "\n<b>" .. HWMP_TooltipValue() .. ":</b> " .. sign .. percent .. "% "
            end
            research[i].Description = description .. "  \n" .. value .. "\n<b>" .. HWMP_TooltipBaseTime() .. ":</b> " .. item.Time .. "s"
        end
    end
end
