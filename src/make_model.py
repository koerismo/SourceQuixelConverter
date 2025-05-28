from .read_meta import QuixelAsset, QuixelModel
from .smd import SourceModelWriter
from pathlib import Path
import subprocess
import pyassimp

def convert_model(src_path: str|Path, out_path: str, mat: str="mat"):
	with pyassimp.load(str(src_path)) as scene:
		assert len(scene.meshes)

		mesh: pyassimp = scene.meshes[0]
		# assert mesh.vertices
		# assert mesh.texcoords
		# assert mesh.normals

		verts = mesh.vertices
		coords = mesh.texturecoords[0]
		normals = mesh.normals

	smd = SourceModelWriter(out_path)

	for u1, u2, u3 in mesh.faces:
		smd.write_smd_triangle(mat)
		smd.write_smd_vertex(verts[u1], normals[u1], coords[u1])
		smd.write_smd_vertex(verts[u2], normals[u2], coords[u2])
		smd.write_smd_vertex(verts[u3], normals[u3], coords[u3])

	smd.end()
	smd.close()

def compile_model(game_path: Path, bin_path: Path, asset: QuixelAsset):
	path_modelsrc = (game_path/"modelsrc"/asset.gameName).with_suffix(".qc")
	studio_process = subprocess.run([bin_path / "studiomdl.exe", path_modelsrc])

def get_base_lod(asset: QuixelAsset) -> int:
	if asset.properties.get("size", None) == "large": return 100
	if asset.properties.get("size", None) == "medium": return 10
	return 6


def setup_model(src_path: Path, game_path: Path, asset: QuixelAsset):
	src_folder = src_path.parent
	primary_model = None

	path_modelsrc = (game_path/"modelsrc"/asset.gameName).with_suffix(".smd")
	path_models = (game_path/asset.gameName).with_suffix(".mdl")

	name_modelsrc: Path = Path(asset.gameName).name
	name_game: Path = Path(asset.gameName).with_suffix(".mdl")
	name_material = Path(asset.materialName).name
	path_cdmaterials = Path("models")/name_game.parent

	print(f"| Source: {src_folder}")
	print(f"| Target path: {path_modelsrc}.qc/smd")
	print(f"| QC include name: {name_modelsrc}.qc/smd")
	print(f"| Compiled name: {name_game}")

	lod_base = get_base_lod(asset)
	lod_count = 0
	lods: list[tuple[QuixelModel, float]] = []

	for i, model in enumerate(asset.models[2:]):
		if not primary_model:
			primary_model = model
			print(f"| Picked primary model ({model.path}) ({model.triCount} tris)")
			continue
		
		if i%2 == 1: continue
		if lod_count > 4: break
		lod_count += 1
		lod_distance = i * lod_base
		lods.append((model, lod_distance))
		print(f"| Picked LOD-{model.lod-1} ({model.path}) ({model.triCount} tris) (distance={lod_distance})")

	QC = []

	if not primary_model:
		print("ERROR: No primary model. Something has gone very wrong!")
		exit(1)
	
	convert_model(src_folder / primary_model.path, path_modelsrc, name_material)
	QC.extend([
		f'$modelname "{name_game}"',
		f'$cdmaterials "{path_cdmaterials}"',
		'$staticprop',
		'$upaxis Y',
		f'$body studio "{name_modelsrc}"',
		f'$sequence idle "{name_modelsrc}"',
	])

	for i, (lod_model, lod_dist) in enumerate(lods):
		new_name = path_modelsrc.with_suffix("").name + "_lod"+str(i)+".smd"
		convert_model(src_folder / lod_model.path, path_modelsrc.with_name(new_name), name_material)
		QC.extend([
			f'$lod {lod_dist}',
			'{',
			f'	replacemodel "{name_modelsrc}" "{new_name}"',
			'}'
		])

	with open(path_modelsrc.with_suffix(".qc"), 'w') as f:
		f.write("\n".join(QC))

