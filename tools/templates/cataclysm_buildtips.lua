-- Native UCS references keep non-ASCII names out of the engine's byte-string path.
dofilepath("locale:hwmp24_cataclysm.lua")
for i, item in build do
    local name = HWMP_CataclysmBuildNames[item.ThingToBuild]
    if name ~= nil and item.HWMP_CataclysmSU == nil then
        local descriptions = HWMP_CataclysmBuildDescriptions
        if GetProductionTimeSetting ~= nil and GetProductionTimeSetting() == 2 then
            descriptions = HWMP_CataclysmBuildTimedDescriptions
        end
        build[i].DisplayedName = name
        build[i].Description = descriptions[item.ThingToBuild]
        build[i].HWMP_CataclysmSU = 1
    end
end
