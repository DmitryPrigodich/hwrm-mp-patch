-- Native smoke: source identity is pinned separately; sound/visual review remains human.
function HWAM_Init(c)
    if c.load_only==1 then return end
    HWA_Freeze(c.source)
    HWA_Freeze(c.target)
    c.initial_hp=HWA_Hp(c.target)
    c.peak=0
    HWA_Log(c,"baseline","missile="..c.missile.."|hp="..c.initial_hp.."|source_entries="..SobGroup_Count(c.source))
end

function HWAM_Tick(c,t)
    if c.load_only==1 then
        if t>=2 then
            local status="failed"
            if SobGroup_Count("HWA_MotherH")==1 and HWA_Hp("HWA_MotherH")>0 then status="passed" end
            HWA_Result(c,status,"stock_hod_fallback=1|hgn_mothership_entries="..SobGroup_Count("HWA_MotherH").."|visual_acceptance=0")
        end
        return
    end
    local count=HWA_CountNear(c,{c.x,0,c.z+750},6000)
    if count>c.peak then c.peak=count end
    if t>=3 and not c.fired then
        c.fired=1
        SobGroup_AbilityActivate(c.source,AB_Attack,1)
        SobGroup_Attack(c.source_player,c.source,c.target)
        HWA_Log(c,"fire_requested","missile="..c.missile)
    end
    if count>0 and not c.launch_observed then
        c.launch_observed=1
        HWA_Log(c,"launch_observed","count="..count)
    end
    local damage=c.initial_hp-HWA_Hp(c.target)
    if c.launch_observed and damage>0 then
        HWA_Result(c,"passed","peak_missiles="..c.peak.."|damage="..damage.."|launch_and_impact=1|sound_visual_acceptance=0")
    elseif t>=45 then
        HWA_Result(c,"failed","peak_missiles="..c.peak.."|damage="..damage.."|reason=no_observed_launch_and_impact")
    end
end
