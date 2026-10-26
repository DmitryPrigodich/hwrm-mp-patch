# Inherited model and icon assets

[Русский](ru/ASSET_PROVENANCE.md) · [Package size](PACKAGE_SIZE.md)

The official [Players Patch full changelog](https://github.com/HW-PlayersPatch/File_Share/blob/master/ChangeLists/Players%20Patch%20-%20Full%20Change%20List.md) explains several visual/functional reasons for these files. Local SHA256 comparison was performed against the extracted regular 2.3, Test21 and current stock Homeworld2/HW1Ships/HW2Ships archives. This is source/asset inspection, not a new native visual test. No assets were removed or changed in this audit.

| Asset | Evidence and reason |
|---|---|
| hgn_mothership.hod — 29,495,305 bytes | Byte-identical to current stock HW2Ships and regular 2.3. The historical changelog includes Gearbox 2.205's mothership visual/badge fix and notes that those preview changes reached official 2.303. In this installation the PP copy adds no model difference; it is a candidate for a separately validated packaging cleanup. |
| kus_researchship.hod and kus_researchship_1.hod — about 7.5 MB each | Different from stock, identical between regular 2.3 and Test21. The changelog restores rotation when all six research hubs are joined. HIER and other rig/collision/export chunks differ; the main model also has different DOCK data. |
| kus_supportfrigate.hod — 6,835,891 bytes | Different from stock, inherited unchanged from regular 2.3. Binary inspection finds changes in HIER, DOCK, MRKS, GLOW and other export data. The changelog documents holding/launching docked ships and hyperspace transport. Those behavioral changes provide context; it does not identify the purpose of every individual HOD edit. |
| kus_cruiserion.hod and kus_destroyerion1.hod | Inherited unchanged from regular 2.3; different from stock. The changelog explicitly fixes player colors on Kushan heavy-cruiser/destroyer ion turrets. |
| obs_observer.hod — 6,633,891 bytes | Added by regular Players Patch for its observer mode, inherited by Test21. The accompanying obs_observer.ship is a separate service ship definition. |
| Three Test missile HOD paths | Corvettes' anti-fighter/small missile HODs are byte-identical to native Vaygr small/anti-fighter/frigate missile assets. The Medium missile HOD is byte-identical to native vgr_heavymissile.hod. These are copied resources under separate missile-type paths; the file names alone do not indicate new graphics. |
| ship/icons/*.dds — 5,418,408 bytes | Six subsystem/taskbar icon atlases at multiple UI resolutions, different from stock and unchanged between regular 2.3 and Test21. The changelog explicitly makes the advanced research-module icon more distinguishable. They are interface icon sheets. |
| cmd_ico_stance_eva_hw1c.dds / cmd_ico_stance_neu_hw1c.dds | Additional classic-stance UI icon resources, inherited from regular Players Patch alongside its classic/remastered stance-order option. |
| hw1_production_fighter.hod — 1,429 bytes | A tiny service subsystem model. Its definition is an invisible FighterProduction system; it is unrelated to the large ship-model payload. |

HOD includes rig/docking data as well as model resources. Re-exported POOL/normal/metadata bytes may differ too; such differences alone do not establish a redesigned hull. The full asset must be included even when the intended change is a rig, docking, material or display fix. Exact donor file sizes/hashes and equal/changed classification are in baseline/test-inventory.json.

The strongest immediate redundancy finding is the exact-path stock-identical Hiigaran mothership. The copied missile models use different resource paths and cannot simply be omitted on that evidence alone. Any cleanup belongs to a later release with dependency/loading checks; the already published release remains unchanged.
