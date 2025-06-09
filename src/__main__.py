import json
import sys
from os import walk, makedirs
from pathlib import Path
from .read_meta import try_read_meta, QuixelAsset, QuixelModel, QuixelTexture
from .make_material import make_material
from .make_model import setup_model, compile_model

from .lib.pbr.src.module.core.vmt import make_vmt
from .lib.pbr.src.module.core.convert import export as export_material
from .lib.pbr.src.module.core.material import Material, MaterialMode, GameTarget, NormalType

TEX_MODE = MaterialMode.PBRModel
TEX_SIZE = (4096, 4096)

#region Init

with open('./config.json', 'r') as c:
	g_config = json.load(c)
	assert "binPath" in g_config
	assert "gamePath" in g_config

BINPATH = Path(g_config["binPath"])
GAMEPATH = Path(g_config["gamePath"])

arg_count = len(sys.argv)
if arg_count < 2:
	print("Expected an argument! (root directory)")
	exit(1)

root_dir = Path(sys.argv[-1])
completed_assets: set[str] = set()
found_assets: list[tuple[Path, QuixelAsset]] = []

print("--- Initializing Converter ---")
print("Using root directory:", str(root_dir))

for root, dirs, files in walk(root_dir):
	for file in files:
		if file.endswith(".json"):
			full_path = (root_dir / root) / file
			parsed = try_read_meta(full_path, sizeStr=f'{TEX_SIZE[0]}x{TEX_SIZE[1]}')

			if not parsed:
				print("- [Failed]:    ", full_path)
				continue

			print("- [Succeeded]: ", full_path)
			for p in parsed:
				found_assets.append((full_path, p))
			break

asset_count = len(found_assets)
if not asset_count:
	print("No Quixel assets found!")
	exit(1)

print("--- Beginning Processing ---")
print(f"\nConverting {asset_count} asset{'s' if asset_count > 1 else ''}...")

#endregion

vmt_folder = (GAMEPATH / "materials/models/props_megascans")
mdl_folder = (GAMEPATH / "models/props_megascans")
mdlsrc_folder = (GAMEPATH / "modelsrc/props_megascans")
makedirs(vmt_folder, exist_ok=True)
makedirs(mdl_folder, exist_ok=True)
makedirs(mdlsrc_folder, exist_ok=True)

for path, asset in found_assets:

	# region Materials

	if asset.materialName not in completed_assets:
		completed_assets.add(asset.materialName)

		print("\nProcessing material for", asset.name)
		material = make_material(path, asset, texSize=TEX_SIZE, texMode=TEX_MODE)
		texlist = export_material(material)

		vmt_path = (GAMEPATH/"materials"/material.name).with_suffix(".vmt")
		vmt = make_vmt(material)
		print(f"- Writing VMT to {vmt_path}")
		with open(vmt_path, "w") as vmt_file:
			vmt_file.write(vmt)
		
		print(f"- Writing {len(texlist)} textures to {GAMEPATH/'materials'/'models'/material.name}_*.vtf")
		ver = GameTarget.vtf_version(material.target)
		for tex in texlist:
			tex.image.save(GAMEPATH/"materials"/(material.name+tex.name+".vtf"), version=ver, compressed=tex.compressed)
	
	else:
		print("\nSkipping material for", asset.name, "(Already completed)")

	#endregion

	#region Meshes

	print("\nProcessing meshes for", asset.name, "...")
	setup_model(path, GAMEPATH, asset)

	print("\nCompiling meshes for", asset.name, "...")
	compile_model(GAMEPATH, BINPATH, asset)

	#endregion

try:
	input("Process completed! Waiting for user to exit program.")
except KeyboardInterrupt:
	pass
print("goodbye!")
