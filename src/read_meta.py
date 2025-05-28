from pathlib import Path
from typing import NamedTuple
import json

class QuixelModel(NamedTuple):
	lod: int
	path: str
	triCount: int
	variation: int

class QuixelTexture(NamedTuple):
	name: str
	path: str
	colorSpace: str
	minIntensity: int
	maxIntensity: int
	averageColor: tuple[float, float, float]

class QuixelAsset(NamedTuple):
	name: str
	gameName: str
	materialName: str
	textures: dict[str, QuixelTexture]
	models: list[QuixelModel]
	properties: dict[str, str]


def try_read_meta(fp: Path, sizeStr="2048x2048") -> QuixelAsset|None:
	return read_meta(fp, sizeStr=sizeStr)
	try:
		return read_meta(fp, sizeStr=sizeStr)
	except Exception as e:
		print(e)
		return None

def read_meta(fp: Path, sizeStr: str) -> list[QuixelAsset]:
	with open(fp, 'r') as file:
		data = json.load(file)
	
	assert "pack" in data
	assert "name" in data

	name = data["name"]
	game_name = "props_megascans/" + name.lower().replace(" ", "_") + "_" + fp.name[:-5]
	props = read_properties(data["properties"])

	if data["pack"]:
		pack = data["pack"]
		print(f"| Reading meta as collection... ({pack['name']})")

		texture_list =  [read_maps(t, sizeStr, "image/jpeg") for t in data["maps"]]
		textures: dict[str, str] = { t.name: t for t in texture_list if t }
		variant_list: list[QuixelModel] = [read_model(t, i) for i, t in enumerate(data["models"])]

		variants: dict[int, QuixelAsset] = {}
		for variant_lod in variant_list:
			if not variant_lod: continue
			v_id = variant_lod.variation
			if v_id not in variants: variants[v_id] = QuixelAsset(name+" "+str(v_id), game_name+"_"+str(v_id), game_name, textures, [], props)
			variant = variants[v_id]
			variant.models.append(variant_lod)
		
		for variant in variants.values():
			variant.models.sort(key=lambda x : x.lod)

		print(f'| Found {len(variants)} variants in collection!')
		return variants.values()

	else:
		texture_list = [read_texture(t, sizeStr, "image/jpeg") for t in data["components"]]
		textures: dict[str, str] = { t.name: t for t in texture_list if t }
		models: list[QuixelModel] = [read_mesh(t, i) for i, t in enumerate(data["meshes"])]
		models = [x for x in models if x]

		return [QuixelAsset(name, game_name, game_name, textures, models, props)]


def read_maps(data: object, resString: str, mimeType: str) -> QuixelTexture|None:
	''' This function is only used for asset packs, like foliage! '''
	assert "uri" in data
	assert "resolution" in data
	assert "mimeType" in data

	if data["resolution"] != resString: return None
	if data["mimeType"] != mimeType: return None

	return QuixelTexture(
		data["name"],
		data["uri"],
		data["colorSpace"],
		0,
		255,
		read_color(data["averageColor"])
	)

def read_texture(data: object, resString: str, mimeType: str) -> QuixelTexture:
	path = ""

	assert "uris" in data
	uri = data["uris"][0]
	assert "resolutions" in uri
	for entry in uri["resolutions"]:
		if entry["resolution"] != resString: continue
		for format in entry["formats"]:
			if format["mimeType"] != mimeType: continue
			path = format["uri"]
			break


	return QuixelTexture(
		data["name"],
		path,
		data["colorSpace"],
		data["minIntensity"],
		data["maxIntensity"],
		read_color(data["averageColor"])
	)

def read_color(color: str) -> tuple[float, float, float]:
	return (
		int(color[1:3], 16) / 255.0,
		int(color[3:5], 16) / 255.0,
		int(color[5:7], 16) / 255.0
	)

def read_model(data: object, ind: int, mimeType="application/x-fbx") -> QuixelModel:
	''' This function is only used for asset packs, like foliage! '''
	tri_count = data["tris"] if "tris" in data else -1
	if data["mimeType"] != mimeType: return
	return QuixelModel(data["lod"]+1 if "lod" in data else 0, data["uri"], tri_count, data["variation"])

def read_mesh(data: object, ind: int, mimeType="application/x-fbx") -> QuixelModel:
	tri_count = data["tris"] if "tris" in data else -1
	for uri in data["uris"]:
		if uri["mimeType"] != mimeType: continue
		return QuixelModel(ind, uri["uri"], tri_count, -1)

def read_properties(data: object) -> dict[str, str]:
	out = {}
	for prop in data:
		out[prop["key"]] = prop["value"]
	return out
