"""Generate native checkpoint persistence directly in the effect library."""
import re

def apply(effects,journal):
    basic=journal.rstrip()+'\n\n'
    basic+='\nfunction HWJ_Flush()\n for i=1,getn(HWMP_EffectRecords) do HWJ_WriteRecord(HWMP_EffectRecords[i]) end\nend\n'
    names=('HWMP_FindEffectRecord','HWMP_BlockRecord','HWMP_ReleaseRecord','HWMP_ReleaseOwner',
           'HWMP_UnblockGroup','HWMP_ClearReleasedTumble','HWMP_SetAbilityAllowed','HWMP_SetSpeedAllowed','HWMP_ReleaseAbility')
    for name in names:
        start=effects.index('function '+name+'(')
        following=re.search(r'(?m)^function ',effects[start+1:])
        end=start+1+following.start() if following else len(effects)
        block=effects[start:end];first=block.index('\n')
        if name=='HWMP_FindEffectRecord':
            block=block[:first+1]+'    HWJ_Sync(0)\n'+block[first+1:]
            block=block.replace('return record','HWJ_ReadRecord(record); return record')
        elif name=='HWMP_ReleaseOwner':
            block='''function HWMP_ReleaseOwner(owner)
    local marker=HWJ_OwnerName(HWMP_OwnerKey(owner))
    if not HWJ_Exists(marker) or SobGroup_Empty(marker)==1 then return end
    HWJ_Sync(0)
    for i=1,getn(HWMP_EffectRecords) do
        local record=HWMP_EffectRecords[i]
        if HWJ_Exists(record.group) and SobGroup_Empty(record.group)==0 and SobGroup_GroupInGroup(record.group,marker)==1 then
            HWMP_ReleaseRecord(record,owner)
        end
    end
end

'''
        elif name=='HWMP_BlockRecord':
            last=block.rfind('\nend');block=block[:last]+'\n    HWJ_MarkOwner(record,owner)\n    HWJ_WriteRecord(record)'+block[last:]
        elif name=='HWMP_ReleaseRecord':
            block=block[:first+1]+'    HWJ_ReadRecord(record)\n'+block[first+1:]
            last=block.rfind('\nend');block=block[:last]+'\n    HWJ_UnmarkOwner(record,owner)\n    HWJ_WriteRecord(record)'+block[last:]
        else:
            force=1 if name in ('HWMP_SetAbilityAllowed','HWMP_SetSpeedAllowed','HWMP_ReleaseAbility') else 0
            prefix='    HWJ_Sync('+str(force)+')\n'
            block=block[:first+1]+prefix+block[first+1:]
            if name in ('HWMP_SetAbilityAllowed','HWMP_SetSpeedAllowed','HWMP_ReleaseAbility'):
                last=block.rfind('\nend');block=block[:last]+'\n    HWJ_Flush()'+block[last:]
        effects=effects[:start]+block+effects[end:]
    return effects+'\n'+basic


def generate_effects():
    from pathlib import Path
    root=Path(__file__).resolve().parent/'templates'
    return apply((root/'effects_base.lua').read_text(encoding='ascii'),(root/'effect_journal.lua').read_text(encoding='ascii'))

def patch_gravity(text):
    old='previously_stunned = SobGroup_CreateAndClear("gravwell-" .. ship_id .. "-previously-stunned")'
    assert text.count(old)==1
    text=text.replace(old,'previously_stunned = HWJ_PreviousGroup(ship_id)')
    old='else HWMP_BlockGroup(group, owner, GW_MEM_PROTO.abilities_to_disable, 1) end'
    assert text.count(old)==1
    return text.replace(old,'elseif HWJ_OwnerHas(owner,group)==1 then\n            for i=1,getn(GW_MEM_PROTO.abilities_to_disable) do SobGroup_AbilityActivate(group,GW_MEM_PROTO.abilities_to_disable[i],0) end\n            SobGroup_SetSpeed(group,0)\n        else HWMP_BlockGroup(group, owner, GW_MEM_PROTO.abilities_to_disable, 1) end')
